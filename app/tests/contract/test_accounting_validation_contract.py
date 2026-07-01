import copy
from decimal import Decimal

import pytest
from accounting.models import AccountingValidationFinding, AccountingValidationRun
from accounting.services import validate_structured_balance
from companies.models import Company
from documents.models import BalanceDocument
from extraction.models import ProcessingRun, RawExtraction


def _raw_extraction(user, content):
    company = Company.objects.create(legal_name="Contrato LTDA")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance.pdf",
        file="balance-documents/balance.pdf",
        file_uri="/media/balance-documents/balance.pdf",
        sha256="sha-contract",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    processing_run = ProcessingRun.objects.create(document=document, pipeline_version="test")
    return RawExtraction.objects.create(
        document=document,
        processing_run=processing_run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content=content,
    )


@pytest.mark.django_db
def test_validate_structured_balance_persists_contract_shape_and_preserves_raw(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    content = {
        "llm_output": {
            "metadados": {"tipo_documento": "balanco_patrimonial"},
            "campos_analise": {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {"valor": 650},
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            },
        }
    }
    original = copy.deepcopy(content)
    raw = _raw_extraction(user, content)

    run = validate_structured_balance(raw)
    raw.refresh_from_db()

    assert raw.content == original
    assert isinstance(run, AccountingValidationRun)
    assert run.status == AccountingValidationRun.Status.INCONSISTENT
    assert "validacao_contabil" in run.validated_output
    finding = AccountingValidationFinding.objects.get(validation_run=run)
    assert finding.rule_id == "BALANCE_EQUATION_001"
    assert finding.severity == "high"
    assert finding.outcome == "failed"
    assert finding.difference == Decimal("50.000000")
