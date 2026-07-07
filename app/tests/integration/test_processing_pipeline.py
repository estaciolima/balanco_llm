from decimal import Decimal
from unittest.mock import patch

import pytest

from companies.models import Company
from documents.models import BalanceDocument
from extraction.models import ExtractedLineItem, ProcessingRun, RawExtraction
from extraction.pipeline import process_document


@pytest.mark.django_db
@patch("extraction.pipeline.extract_tables")
@patch("extraction.pipeline.extract_native_text")
@patch("extraction.pipeline.detect_has_text")
def test_processing_pipeline_creates_raw_extractions_and_candidate_line_items(
    mock_detect_has_text,
    mock_extract_native_text,
    mock_extract_tables,
    user,
):
    mock_detect_has_text.return_value = True
    mock_extract_native_text.return_value = [
        {
            "page_number": 1,
            "text": "1.1.01 CAIXA E EQUIVALENTE DE CAIXA 1.000,00D",
            "method": "native_text",
        }
    ]
    mock_extract_tables.return_value = []
    company = Company.objects.create(legal_name="ACME")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance.pdf",
        file="balance-documents/balance.pdf",
        file_uri="/media/balance-documents/balance.pdf",
        sha256="sha-1",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")

    payloads = process_document(document, run)

    assert RawExtraction.objects.count() == 1
    assert ExtractedLineItem.objects.count() == 1
    item = ExtractedLineItem.objects.get()
    assert item.normalized_value == Decimal("1000.00")
    assert item.source_account_code == "1.1.01"
    assert item.source_parent_account_code == "1.1"
    assert item.source_balance_nature == "D"
    assert item.suggested_standard_line_item is None
    assert payloads["candidates_event"]["event_type"] == "document.candidates.parsed"
    assert payloads["candidates_event"]["payload"]["created_line_item_count"] == 1
