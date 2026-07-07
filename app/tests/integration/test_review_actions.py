from decimal import Decimal

import pytest
from django.urls import reverse

from companies.models import Company, ReportingPeriod
from documents.models import BalanceDocument
from extraction.models import ExtractedLineItem, ProcessingRun, RawExtraction
from review.models import ReviewTask
from standardization.models import StandardLineItem, StandardizedBalanceValue


@pytest.mark.django_db
def test_review_actions_approve_correct_and_reject(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    period = ReportingPeriod.objects.create(
        company=company,
        fiscal_year=2025,
        currency="BRL",
    )
    line_item = StandardLineItem.objects.create(
        code="cash_and_equivalents",
        display_name="Cash and Equivalents",
        category=StandardLineItem.Category.ASSET,
    )
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance.pdf",
        file="balance-documents/balance.pdf",
        file_uri="/media/balance-documents/balance.pdf",
        sha256="sha-review",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
    raw = RawExtraction.objects.create(
        processing_run=run,
        document=document,
        extraction_type=RawExtraction.ExtractionType.NATIVE_TEXT,
        content={"text": "Cash 100.00"},
        source_method="native_text",
    )
    item = ExtractedLineItem.objects.create(
        document=document,
        processing_run=run,
        raw_extraction=raw,
        source_label="Cash",
        suggested_standard_line_item=line_item,
        raw_value="100.00",
        normalized_value=Decimal("100.00"),
        currency="BRL",
        reporting_period=period,
        confidence=0.9,
        evidence={"text": "Cash 100.00"},
    )
    approve_task = ReviewTask.objects.create(
        document=document,
        extracted_line_item=item,
        reason=ReviewTask.Reason.LOW_CONFIDENCE,
    )

    response = client.post(reverse("review-approve", args=[approve_task.pk]), follow=True)

    assert response.status_code == 200
    assert StandardizedBalanceValue.objects.count() == 1

    correct_item = ExtractedLineItem.objects.create(
        document=document,
        processing_run=run,
        raw_extraction=raw,
        source_label="Cash corrected",
        suggested_standard_line_item=line_item,
        raw_value="50.00",
        normalized_value=Decimal("50.00"),
        currency="BRL",
        reporting_period=period,
        confidence=0.4,
        evidence={"text": "Cash corrected 50.00"},
    )
    correct_task = ReviewTask.objects.create(
        document=document,
        extracted_line_item=correct_item,
        reason=ReviewTask.Reason.LOW_CONFIDENCE,
    )
    response = client.post(
        reverse("review-correct", args=[correct_task.pk]),
        {
            "standard_line_item": line_item.pk,
            "value": "55.00",
            "currency": "BRL",
            "reporting_period": period.pk,
            "reason": "Adjusted after review",
        },
        follow=True,
    )
    assert response.status_code == 200

    reject_item = ExtractedLineItem.objects.create(
        document=document,
        processing_run=run,
        raw_extraction=raw,
        source_label="Reject me",
        raw_value="10.00",
        confidence=0.2,
        evidence={"text": "Reject me 10.00"},
    )
    reject_task = ReviewTask.objects.create(
        document=document,
        extracted_line_item=reject_item,
        reason=ReviewTask.Reason.MISSING_FIELD,
    )
    response = client.post(
        reverse("review-reject", args=[reject_task.pk]),
        {"reason": "Invalid extraction"},
        follow=True,
    )
    assert response.status_code == 200
    reject_task.refresh_from_db()
    assert reject_task.status == ReviewTask.Status.REJECTED
