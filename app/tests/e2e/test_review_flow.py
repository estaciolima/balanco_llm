from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from companies.models import Company, ReportingPeriod
from documents.models import BalanceDocument
from extraction.models import ExtractedLineItem, ProcessingRun, RawExtraction
from review.models import ReviewTask
from standardization.models import StandardLineItem


@pytest.mark.django_db(transaction=True)
def test_review_approve_and_correct_flow(live_server, page):
    user = get_user_model().objects.create_user(username="reviewer", password="password123")
    company = Company.objects.create(legal_name="ACME Holdings")
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
        original_filename="review-balance.pdf",
        file="balance-documents/review-balance.pdf",
        file_uri="/media/balance-documents/review-balance.pdf",
        sha256="review-sha",
        content_type="application/pdf",
        file_size_bytes=128,
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
    approve_item = ExtractedLineItem.objects.create(
        document=document,
        processing_run=run,
        raw_extraction=raw,
        source_label="Cash",
        suggested_standard_line_item=line_item,
        raw_value="100.00",
        normalized_value=Decimal("100.00"),
        currency="BRL",
        reporting_period=period,
        confidence=0.72,
        evidence={"text": "Cash 100.00"},
    )
    approve_task = ReviewTask.objects.create(
        document=document,
        extracted_line_item=approve_item,
        reason=ReviewTask.Reason.LOW_CONFIDENCE,
    )
    correct_item = ExtractedLineItem.objects.create(
        document=document,
        processing_run=run,
        raw_extraction=raw,
        source_label="Cash revised",
        suggested_standard_line_item=line_item,
        raw_value="95.00",
        normalized_value=Decimal("95.00"),
        currency="BRL",
        reporting_period=period,
        confidence=0.41,
        evidence={"text": "Cash revised 95.00"},
    )
    correct_task = ReviewTask.objects.create(
        document=document,
        extracted_line_item=correct_item,
        reason=ReviewTask.Reason.CONFLICT,
    )

    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill("reviewer")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign in").click()

    page.goto(f"{live_server.url}/review/")
    page.get_by_role("link", name="review-balance.pdf").first.click()
    page.get_by_role("button", name="Approve").click()
    page.wait_for_url(f"{live_server.url}/review/{approve_task.pk}/")
    assert page.get_by_text("Review task approved.").is_visible()

    page.goto(f"{live_server.url}/review/{correct_task.pk}/")
    page.get_by_role("link", name="Correct").click()
    page.get_by_label("Value").fill("101.25")
    page.get_by_label("Reason").fill("Adjusted after manual review")
    page.get_by_role("button", name="Save correction").click()
    page.wait_for_url(f"{live_server.url}/review/{correct_task.pk}/")
    assert page.get_by_text("Review task corrected.").is_visible()
