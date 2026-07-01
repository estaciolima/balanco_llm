from decimal import Decimal

import pytest
from accounting.models import AccountingValidationFinding, AccountingValidationRun
from accounting.services import validate_structured_balance
from audit.models import AuditEvent
from companies.models import Company
from documents.models import BalanceDocument
from extraction.models import ProcessingRun, RawExtraction


def create_structured_raw(user, llm_output, sha="sha-validation"):
    company = Company.objects.create(legal_name=f"Empresa {sha}")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename=f"{sha}.pdf",
        file=f"balance-documents/{sha}.pdf",
        file_uri=f"/media/balance-documents/{sha}.pdf",
        sha256=sha,
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    processing_run = ProcessingRun.objects.create(document=document, pipeline_version="test")
    raw = RawExtraction.objects.create(
        document=document,
        processing_run=processing_run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={"llm_output": llm_output},
    )
    return document, raw


@pytest.mark.django_db
def test_validation_run_consistent_for_balanced_extraction(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    _, raw = create_structured_raw(
        user,
        {
            "metadados": {"tipo_documento": "balanco_patrimonial"},
            "campos_analise": {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {"valor": 700},
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            },
        },
        sha="sha-consistent",
    )

    run = validate_structured_balance(raw)

    assert run.status == AccountingValidationRun.Status.CONSISTENT
    assert run.findings.get().outcome == "passed"


@pytest.mark.django_db
def test_validation_run_inconsistent_for_mismatched_balance(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    _, raw = create_structured_raw(
        user,
        {
            "metadados": {"tipo_documento": "balanco_patrimonial"},
            "campos_analise": {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {"valor": 650},
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            },
        },
        sha="sha-inconsistent",
    )

    run = validate_structured_balance(raw)

    assert run.status == AccountingValidationRun.Status.INCONSISTENT
    assert AccountingValidationFinding.objects.filter(
        validation_run=run,
        rule_id="BALANCE_EQUATION_001",
        outcome="failed",
        severity="high",
    ).exists()


@pytest.mark.django_db
def test_sum_account_correction_is_saved_without_mutating_raw_extraction(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    document, raw = create_structured_raw(
        user,
        {
            "metadados": {"tipo_documento": "balanco_patrimonial"},
            "campos_analise": {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {
                    "valor": 690,
                    "tipo_obtencao": "soma_contas",
                    "contas_origem": [
                        {"descricao": "A", "valor": 400},
                        {"descricao": "B", "valor": 300},
                    ],
                },
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            },
        },
        sha="sha-corrected",
    )
    original_raw_content = raw.content.copy()

    run = validate_structured_balance(raw)
    raw.refresh_from_db()

    corrected = run.validated_output["campos_analise"]["passivo_circulante"]
    assert corrected["valor_original"] == "690"
    assert corrected["valor_validado"] == "700"
    assert corrected["corrigido"] is True
    assert raw.content == original_raw_content
    assert AuditEvent.objects.filter(
        target_id=str(document.id), event_type="accounting.validation.correction_applied"
    ).exists()


@pytest.mark.django_db
def test_validation_audit_events_are_created_for_pipeline_service(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    document, raw = create_structured_raw(
        user,
        {
            "metadados": {"tipo_documento": "balanco_patrimonial"},
            "campos_analise": {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {"valor": 650},
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            },
        },
        sha="sha-audit-pipeline",
    )

    validate_structured_balance(raw)

    event_types = set(
        AuditEvent.objects.filter(target_id=str(document.id)).values_list("event_type", flat=True)
    )
    assert "accounting.validation.started" in event_types
    assert "accounting.validation.completed" in event_types
    assert "accounting.validation.inconsistency_detected" in event_types
