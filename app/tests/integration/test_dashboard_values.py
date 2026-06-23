from decimal import Decimal

import pytest
from companies.models import Company, ReportingPeriod
from django.urls import reverse
from documents.models import BalanceDocument
from extraction.models import ProcessingRun, RawExtraction
from standardization.models import StandardizedBalanceValue, StandardLineItem


@pytest.mark.django_db
def test_dashboard_shows_only_approved_values(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    period = ReportingPeriod.objects.create(
        company=company,
        fiscal_year=2025,
        currency="BRL",
    )
    line_item = StandardLineItem.objects.create(
        code="cash",
        display_name="Cash",
        category=StandardLineItem.Category.ASSET,
    )
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period,
        standard_line_item=line_item,
        value=Decimal("100.00"),
        currency="BRL",
        approval_status=StandardizedBalanceValue.ApprovalStatus.APPROVED,
    )
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period,
        standard_line_item=StandardLineItem.objects.create(
            code="liability",
            display_name="Liability",
            category=StandardLineItem.Category.LIABILITY,
        ),
        value=Decimal("50.00"),
        currency="BRL",
        approval_status=StandardizedBalanceValue.ApprovalStatus.SUPERSEDED,
    )

    response = client.get(reverse("company-dashboard", args=[company.pk]))

    body = response.content.decode()
    assert response.status_code == 200
    assert "Cash" in body
    assert "Liability" not in body
    assert "Variação" in body


@pytest.mark.django_db
def test_dashboard_uses_ai_structured_output_when_available(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME AI")
    for year, assets in ((2024, 100), (2025, 125)):
        period = ReportingPeriod.objects.create(company=company, fiscal_year=year, currency="BRL")
        document = BalanceDocument.objects.create(
            company=company,
            reporting_period=period,
            original_filename=f"balance-{year}.pdf",
            file=f"balance-documents/{year}.pdf",
            file_uri=f"/media/balance-documents/{year}.pdf",
            sha256=f"sha-ai-dashboard-{year}",
            content_type="application/pdf",
            file_size_bytes=100,
            uploaded_by=user,
        )
        run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
        RawExtraction.objects.create(
            document=document,
            processing_run=run,
            extraction_type=RawExtraction.ExtractionType.METADATA,
            source_method="openai_structured_output",
            content={
                "llm_output": {
                    "metadados": {"moeda": "BRL"},
                    "campos_analise": {"ativo_circulante": {"valor": assets}},
                }
            },
        )

    response = client.get(reverse("company-dashboard", args=[company.pk]))

    body = response.content.decode()
    assert response.status_code == 200
    assert "ATIVO CIRCULANTE" in body
    assert "▲ +25,0%" in body
