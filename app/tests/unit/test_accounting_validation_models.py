from decimal import Decimal

import pytest
from accounting.models import AccountingValidationFinding, AccountingValidationRun
from companies.models import Company
from documents.models import BalanceDocument
from extraction.models import ProcessingRun, RawExtraction


@pytest.mark.django_db
def test_validation_run_and_finding_relationship(user):
    company = Company.objects.create(legal_name="Model Test LTDA")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance.pdf",
        file="balance-documents/balance.pdf",
        file_uri="/media/balance-documents/balance.pdf",
        sha256="sha-model",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    processing_run = ProcessingRun.objects.create(document=document, pipeline_version="test")
    raw = RawExtraction.objects.create(
        document=document,
        processing_run=processing_run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        content={"llm_output": {}},
    )
    validation_run = AccountingValidationRun.objects.create(
        document=document,
        raw_extraction=raw,
        status=AccountingValidationRun.Status.WARNING,
        tolerance_amount=Decimal("0.01"),
        tolerance_ratio=Decimal("0.01"),
        summary={"by_outcome": {"not_assessable": 1}},
        validated_output={},
    )
    finding = AccountingValidationFinding.objects.create(
        validation_run=validation_run,
        rule_id="TEST_RULE",
        field_path="campos_analise",
        severity="warning",
        outcome="not_assessable",
        message="Missing data",
    )

    assert validation_run.findings.get() == finding
    assert document.accounting_validation_runs.get() == validation_run
