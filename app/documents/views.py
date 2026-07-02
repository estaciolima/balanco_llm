import json
from decimal import Decimal, InvalidOperation

from accounting.models import AccountingValidationRun
from accounting.services import validate_structured_balance
from companies.models import Company
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from extraction.models import AIExtractionRun, RawExtraction

from documents.forms import DocumentUploadForm
from documents.models import BalanceDocument
from documents.services import (
    DuplicateDocumentError,
    UnsupportedDocumentError,
    create_balance_document,
    requeue_processing,
)

ANALYSIS_TABLE_ROWS = (
    ("highlight", "PATRIMÔNIO LÍQUIDO", "patrimonio_liquido"),
    ("highlight", "PERMANENTE", "permanente"),
    ("highlight", "EXIGÍVEL LONGO PRAZO", "exigivel_longo_prazo"),
    ("detail", "Bancos", "bancos_longo_prazo"),
    ("detail", "Impostos Parcelados / Diferidos", "impostos_parcelados_diferidos_longo_prazo"),
    ("highlight", "REALIZÁVEL LONGO PRAZO", "realizavel_longo_prazo"),
    ("detail", "Contas a Receber Clientes LP", "contas_receber_clientes_longo_prazo"),
    ("detail", "Estoques LP", "estoques_longo_prazo"),
    ("detail", "Contas a Receber Emp. Ligadas/Sócios", "contas_receber_empresas_ligadas_socios"),
    ("detail", "Impostos a Recuperar / Diferidos", "impostos_recuperar_diferidos_ativo"),
    ("highlight", "ATIVO CIRCULANTE", "ativo_circulante"),
    ("detail", "Caixa + Aplicações", "caixa_aplicacoes"),
    ("detail", "Contas a Receber", "contas_receber_curto_prazo"),
    ("detail", "Estoques", "estoques"),
    ("highlight", "PASSIVO CIRCULANTE", "passivo_circulante"),
    ("detail", "Bancos - Curto Prazo", "bancos_curto_prazo"),
    ("detail", "Fornecedores", "fornecedores"),
    ("detail", "Salários e Impostos", "salarios_impostos"),
    ("highlight", "TOTAL DO BALANÇO", "total_balanco"),
    ("highlight", "Prazo médio de recebimentos", "prazo_medio_recebimentos"),
    ("section", "LIQUIDEZ", None),
    ("detail", "Liquidez Corrente (AC/PC)", "liquidez_corrente"),
    ("detail", "Liquidez Seca (AC-E/PC)", "liquidez_seca"),
    ("detail", "Liquidez Geral (AC+RLP/PC+ELP)", "liquidez_geral"),
)


def format_analysis_value(value, *, is_ratio: bool = False) -> str:
    if value is None:
        return "-"
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)

    if is_ratio:
        formatted = f"{decimal_value:.2f}".rstrip("0").rstrip(".")
        return formatted.replace(".", ",")

    formatted = f"{decimal_value:,.2f}"
    integer, fraction = formatted.split(".")
    integer = integer.replace(",", ".")
    return integer if fraction == "00" else f"{integer},{fraction}"


def _origin_accounts_for_tooltip(item: dict) -> list[dict]:
    accounts = item.get("contas_origem_somadas") or item.get("contas_origem") or []
    return accounts if isinstance(accounts, list) and len(accounts) > 1 else []


def _origin_accounts_tooltip(item: dict) -> str:
    accounts = _origin_accounts_for_tooltip(item)
    if not accounts:
        return ""
    lines = []
    for account in accounts:
        description = account.get("descricao") or account.get("codigo") or "Conta"
        value = format_analysis_value(account.get("valor"))
        group = account.get("grupo_original")
        group_suffix = f" · {group}" if group else ""
        lines.append(f"{description}: {value}{group_suffix}")
    return "\n".join(lines)


def build_analysis_table(result: dict) -> list[dict[str, str | bool]]:
    fields = result.get("campos_analise", {})
    rows = []
    for row_type, label, field_name in ANALYSIS_TABLE_ROWS:
        if row_type == "section":
            rows.append({"type": row_type, "label": label, "value": "", "corrected": False})
            continue
        item = fields.get(field_name, {})
        value = item.get("valor_validado", item.get("valor")) if isinstance(item, dict) else None
        rows.append(
            {
                "type": row_type,
                "label": label,
                "value": format_analysis_value(value, is_ratio=field_name.startswith("liquidez_")),
                "corrected": bool(item.get("corrigido")) if isinstance(item, dict) else False,
                "original_value": (
                    format_analysis_value(item.get("valor")) if isinstance(item, dict) else "-"
                ),
                "origin_tooltip": _origin_accounts_tooltip(item) if isinstance(item, dict) else "",
            }
        )
    return rows


def _format_decimal_value(value) -> str:
    return format_analysis_value(value)


def _validation_badge_class(status: str) -> str:
    return {
        AccountingValidationRun.Status.CONSISTENT: "badge-success",
        AccountingValidationRun.Status.WARNING: "badge-warning",
        AccountingValidationRun.Status.INCONSISTENT: "badge-danger",
        AccountingValidationRun.Status.NOT_ASSESSABLE: "badge-warning",
    }.get(status, "")


def _validation_status_label(status: str) -> str:
    return {
        AccountingValidationRun.Status.CONSISTENT: "Coerente",
        AccountingValidationRun.Status.WARNING: "Com alertas",
        AccountingValidationRun.Status.INCONSISTENT: "Inconsistente",
        AccountingValidationRun.Status.NOT_ASSESSABLE: "Não avaliável",
    }.get(status, status)


def build_validation_summary(validation_run: AccountingValidationRun | None) -> dict | None:
    if validation_run is None:
        return None
    findings = list(validation_run.findings.all())
    return {
        "id": validation_run.id,
        "status": validation_run.status,
        "status_label": _validation_status_label(validation_run.status),
        "badge_class": _validation_badge_class(validation_run.status),
        "summary": validation_run.summary,
        "created_at": validation_run.created_at,
        "duration_ms": validation_run.duration_ms,
        "findings": [
            {
                "rule_id": finding.rule_id,
                "field_path": finding.field_path,
                "severity": finding.severity,
                "outcome": finding.outcome,
                "message": finding.message,
                "original_value": _format_decimal_value(finding.original_value),
                "calculated_value": _format_decimal_value(finding.calculated_value),
                "difference": _format_decimal_value(finding.difference),
            }
            for finding in findings
        ],
        "corrections": [
            {
                "rule_id": finding.rule_id,
                "field_path": finding.field_path,
                "message": finding.message,
                "original_value": _format_decimal_value(finding.original_value),
                "corrected_value": _format_decimal_value(finding.calculated_value),
                "difference": _format_decimal_value(finding.difference),
            }
            for finding in findings
            if finding.outcome == "corrected"
        ],
    }


def _token_count(value) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _format_cost(value: Decimal | None, currency: str) -> str:
    if value is None:
        return "Não configurado"
    prefix = "US$" if currency == "USD" else "R$"
    formatted = f"{value:.6f}"
    if currency == "BRL":
        formatted = formatted.replace(".", ",")
    return f"{prefix} {formatted}"


def build_usage_summary(ai_run: AIExtractionRun | None) -> dict | None:
    if ai_run is None:
        return None
    usage = ai_run.token_usage or {}
    input_tokens = _token_count(usage.get("input_tokens"))
    output_tokens = _token_count(usage.get("output_tokens"))
    input_details = usage.get("input_tokens_details") or {}
    cached_tokens = min(_token_count(input_details.get("cached_tokens")), input_tokens)
    input_price = settings.OPENAI_INPUT_USD_PER_MILLION_TOKENS
    cached_input_price = settings.OPENAI_CACHED_INPUT_USD_PER_MILLION_TOKENS
    output_price = settings.OPENAI_OUTPUT_USD_PER_MILLION_TOKENS

    estimated_usd = None
    if None not in (input_price, cached_input_price, output_price):
        estimated_usd = (
            Decimal(input_tokens - cached_tokens) * input_price
            + Decimal(cached_tokens) * cached_input_price
            + Decimal(output_tokens) * output_price
        ) / Decimal("1000000")
    estimated_brl = (
        estimated_usd * settings.USD_BRL_EXCHANGE_RATE
        if estimated_usd is not None and settings.USD_BRL_EXCHANGE_RATE is not None
        else None
    )
    return {
        "model": ai_run.model_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "estimated_usd": _format_cost(estimated_usd, "USD"),
        "estimated_brl": _format_cost(estimated_brl, "BRL"),
    }


@login_required
def document_upload(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            document = create_balance_document(
                company=company,
                uploaded_file=form.cleaned_data["file"],
                actor_user=request.user,
                fiscal_year=form.cleaned_data["fiscal_year"],
            )
        except UnsupportedDocumentError as exc:
            form.add_error("file", str(exc))
        except DuplicateDocumentError as exc:
            messages.warning(request, "This PDF already exists for processing.")
            return redirect("document-detail", document_id=exc.document.pk)
        else:
            messages.success(request, "PDF uploaded and queued for processing.")
            return redirect("document-detail", document_id=document.pk)

    return render(
        request,
        "documents/document_upload.html",
        {"company": company, "form": form},
    )


@login_required
def document_detail(request, document_id):
    document = get_object_or_404(
        BalanceDocument.objects.select_related("company", "reporting_period").prefetch_related(
            "processing_runs",
            "extracted_line_items",
        ),
        pk=document_id,
    )
    line_items = document.extracted_line_items.order_by(
        "source_account_code",
        "source_hierarchy_level",
        "source_label",
    )
    latest_ai_extraction = (
        document.raw_extractions.filter(
            extraction_type=RawExtraction.ExtractionType.METADATA,
            source_method="openai_structured_output",
        )
        .order_by("-created_at", "-processing_run__created_at")
        .first()
    )
    return render(
        request,
        "documents/document_detail.html",
        {
            "document": document,
            "line_items": line_items,
            "latest_ai_extraction": latest_ai_extraction,
        },
    )


@login_required
def document_reprocess(request, document_id):
    document = get_object_or_404(BalanceDocument, pk=document_id)
    if request.method == "POST":
        requeue_processing(document, request.user)
        messages.success(request, "Document queued for reprocessing.")
    return redirect("document-detail", document_id=document.pk)


def _latest_structured_extraction(document: BalanceDocument) -> RawExtraction | None:
    return (
        document.raw_extractions.filter(
            extraction_type=RawExtraction.ExtractionType.METADATA,
            source_method="openai_structured_output",
        )
        .order_by("-created_at", "-processing_run__created_at")
        .first()
    )


@login_required
def document_ai_extraction(request, document_id):
    document = get_object_or_404(BalanceDocument.objects.select_related("company"), pk=document_id)
    extraction = _latest_structured_extraction(document)
    if extraction is None:
        raise Http404("No structured AI extraction found for this document.")
    result = extraction.content.get("llm_output", {})
    metadata = result.get("metadados", {}) if isinstance(result, dict) else {}
    ai_run = document.ai_extraction_runs.order_by("-created_at").first()
    validation_run = (
        extraction.accounting_validation_runs.prefetch_related("findings")
        .order_by("-created_at")
        .first()
    )
    validated_result = validation_run.validated_output if validation_run else result
    return render(
        request,
        "documents/document_ai_extraction.html",
        {
            "document": document,
            "extraction": extraction,
            "analysis_rows": build_analysis_table(validated_result),
            "analysis_period": metadata.get("periodo_original")
            or metadata.get("ano_referencia")
            or "-",
            "validation_summary": build_validation_summary(validation_run),
            "usage_summary": build_usage_summary(ai_run),
            "formatted_json": json.dumps(result, ensure_ascii=False, indent=2),
        },
    )


@login_required
def document_validate_accounting(request, document_id):
    document = get_object_or_404(BalanceDocument.objects.select_related("company"), pk=document_id)
    if request.method != "POST":
        return redirect("document-ai-extraction", document_id=document.pk)

    extraction = _latest_structured_extraction(document)
    if extraction is None:
        messages.error(request, "Nenhuma extração estruturada da IA foi encontrada para validar.")
        return redirect("document-detail", document_id=document.pk)

    validation_run = validate_structured_balance(extraction, actor_user=request.user)
    status_label = _validation_status_label(validation_run.status)
    messages.success(
        request,
        f"Validação contábil executada com status: {status_label}.",
    )
    return redirect("document-ai-extraction", document_id=document.pk)
