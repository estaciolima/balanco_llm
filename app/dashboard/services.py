from decimal import Decimal, InvalidOperation

from extraction.models import RawExtraction
from standardization.models import StandardizedBalanceValue

AI_ANALYSIS_ROWS = (
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


def format_dashboard_value(value, *, is_ratio: bool) -> str:
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return "-"
    if is_ratio:
        return f"{decimal_value:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    formatted = f"{decimal_value:,.2f}"
    integer, fraction = formatted.split(".")
    integer = integer.replace(",", ".")
    return integer if fraction == "00" else f"{integer},{fraction}"


def build_variation(current_value, previous_value) -> dict:
    if previous_value is None or previous_value == 0:
        return {"label": "-", "direction": "neutral", "bar_width": 0, "color": "#6c757d"}
    difference = current_value - previous_value
    percentage = (difference / abs(previous_value)) * Decimal("100")
    direction = "positive" if difference > 0 else "negative" if difference < 0 else "neutral"
    arrow = "▲" if direction == "positive" else "▼" if direction == "negative" else "•"
    label = f"{arrow} {percentage:+.1f}%" if direction != "neutral" else "• 0,0%"
    return {
        "label": label.replace(".", ","),
        "direction": direction,
        "bar_width": min(abs(float(percentage)), 100),
        "color": "#198754"
        if direction == "positive"
        else "#c43d3d"
        if direction == "negative"
        else "#6c757d",
    }


def _add_display_and_variation(rows: list[dict], periods: list[dict]) -> None:
    for row in rows:
        previous_value = None
        is_ratio = row["line_type"] == "ratio"
        for period in periods:
            cell = row["values"].get(period["label"])
            if cell is None:
                previous_value = None
                continue
            cell["display_value"] = format_dashboard_value(cell["value"], is_ratio=is_ratio)
            cell["variation"] = build_variation(cell["value"], previous_value)
            previous_value = cell["value"]


def get_company_ai_dashboard_matrix(*, company, start_year=None, end_year=None, currency=""):
    extractions = (
        RawExtraction.objects.select_related("document__reporting_period")
        .filter(
            document__company=company,
            source_method="openai_structured_output",
            extraction_type=RawExtraction.ExtractionType.METADATA,
            document__reporting_period__isnull=False,
        )
        .order_by("document__reporting_period__fiscal_year", "-created_at")
    )
    if start_year:
        extractions = extractions.filter(document__reporting_period__fiscal_year__gte=start_year)
    if end_year:
        extractions = extractions.filter(document__reporting_period__fiscal_year__lte=end_year)
    if currency:
        extractions = extractions.filter(document__reporting_period__currency__iexact=currency)

    latest_by_year = {}
    for extraction in extractions:
        latest_by_year.setdefault(extraction.document.reporting_period.fiscal_year, extraction)
    periods = [{"label": str(year), "fiscal_year": year} for year in sorted(latest_by_year)]
    rows = []
    flat_rows = []
    for sort_order, (row_type, label, field_name) in enumerate(AI_ANALYSIS_ROWS):
        if row_type == "section":
            continue
        is_ratio = field_name.startswith("liquidez_")
        row = {
            "code": field_name,
            "label": label,
            "section": "liquidity" if is_ratio else "balance",
            "line_type": "ratio" if is_ratio else "detail",
            "display_level": 0 if row_type == "highlight" else 1,
            "is_highlight": row_type == "highlight",
            "sort_order": sort_order,
            "values": {},
        }
        for period in periods:
            extraction = latest_by_year[period["fiscal_year"]]
            result = extraction.content.get("llm_output", {})
            fields = result.get("campos_analise", {}) if isinstance(result, dict) else {}
            item = fields.get(field_name, {}) if isinstance(fields, dict) else {}
            value = item.get("valor") if isinstance(item, dict) else None
            if value is None:
                continue
            try:
                decimal_value = Decimal(str(value))
            except (InvalidOperation, TypeError, ValueError):
                continue
            row["values"][period["label"]] = {
                "value": decimal_value,
                "currency": result.get("metadados", {}).get("moeda", ""),
                "document_id": str(extraction.document_id),
            }
            flat_rows.append(
                {
                    "year_label": period["label"],
                    "fiscal_year": period["fiscal_year"],
                    "standard_line_item": label,
                    "value": decimal_value,
                }
            )
        rows.append(row)

    _add_display_and_variation(rows, periods)
    return {"periods": periods, "rows": rows, "flat_rows": flat_rows, "source": "ai"}


def get_company_dashboard_rows(
    *, company, start_year=None, end_year=None, category="", currency=""
):
    queryset = (
        StandardizedBalanceValue.objects.select_related("reporting_period", "standard_line_item")
        .filter(
            company=company,
            approval_status=StandardizedBalanceValue.ApprovalStatus.APPROVED,
        )
        .order_by("standard_line_item__sort_order", "reporting_period__fiscal_year")
    )
    if start_year:
        queryset = queryset.filter(reporting_period__fiscal_year__gte=start_year)
    if end_year:
        queryset = queryset.filter(reporting_period__fiscal_year__lte=end_year)
    if category:
        queryset = queryset.filter(standard_line_item__category=category)
    if currency:
        queryset = queryset.filter(currency__iexact=currency)

    rows = []
    for value in queryset:
        rows.append(
            {
                "value_id": str(value.pk),
                "year_label": str(value.reporting_period.fiscal_year),
                "fiscal_year": value.reporting_period.fiscal_year,
                "standard_line_item_code": value.standard_line_item.code,
                "standard_line_item": value.standard_line_item.display_name,
                "category": value.standard_line_item.category,
                "section": value.standard_line_item.statement_section,
                "line_type": value.standard_line_item.line_type,
                "display_level": value.standard_line_item.display_level,
                "is_highlight": value.standard_line_item.is_highlight,
                "sort_order": value.standard_line_item.sort_order,
                "value": value.value,
                "currency": value.currency,
                "document_id": "",
            }
        )
    return rows


def get_company_dashboard_matrix(
    *, company, start_year=None, end_year=None, category="", currency=""
):
    flat_rows = get_company_dashboard_rows(
        company=company,
        start_year=start_year,
        end_year=end_year,
        category=category,
        currency=currency,
    )
    periods = []
    period_keys = set()
    grouped = {}

    for row in flat_rows:
        period_key = row["year_label"]
        if period_key not in period_keys:
            period_keys.add(period_key)
            periods.append({"label": row["year_label"], "fiscal_year": row["fiscal_year"]})

        item_key = row["standard_line_item_code"]
        grouped.setdefault(
            item_key,
            {
                "code": item_key,
                "label": row["standard_line_item"],
                "category": row["category"],
                "section": row["section"],
                "line_type": row["line_type"],
                "display_level": row["display_level"],
                "is_highlight": row["is_highlight"],
                "sort_order": row["sort_order"],
                "values": {},
            },
        )
        grouped[item_key]["values"][period_key] = {
            "value": row["value"],
            "currency": row["currency"],
            "document_id": row["document_id"],
        }

    periods.sort(key=lambda item: item["fiscal_year"])
    matrix_rows = sorted(grouped.values(), key=lambda item: item["sort_order"])
    _add_display_and_variation(matrix_rows, periods)
    return {"periods": periods, "rows": matrix_rows, "flat_rows": flat_rows}
