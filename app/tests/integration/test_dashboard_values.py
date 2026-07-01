from decimal import Decimal

import pytest
from accounting.services import validate_structured_balance
from companies.models import Company, ReportingPeriod
from dashboard.services import get_company_ai_dashboard_matrix
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
    assert "Varia" in body


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
    assert "+25,0%" in body


@pytest.mark.django_db
def test_dashboard_uses_accounting_validated_values_when_available(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    company = Company.objects.create(legal_name="ACME Validated")
    period = ReportingPeriod.objects.create(company=company, fiscal_year=2025, currency="BRL")
    document = BalanceDocument.objects.create(
        company=company,
        reporting_period=period,
        original_filename="balance-validated.pdf",
        file="balance-documents/validated.pdf",
        file_uri="/media/balance-documents/validated.pdf",
        sha256="sha-ai-dashboard-validated",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
    raw = RawExtraction.objects.create(
        document=document,
        processing_run=run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {"tipo_documento": "balanco_patrimonial", "moeda": "BRL"},
                "campos_analise": {
                    "total_balanco": {"valor": 400},
                    "passivo_circulante": {
                        "valor": 90,
                        "tipo_obtencao": "soma_contas",
                        "contas_origem": [{"descricao": "Banco", "valor": 100}],
                    },
                    "exigivel_longo_prazo": {"valor": 0},
                    "patrimonio_liquido": {"valor": 300},
                },
            }
        },
    )
    validate_structured_balance(raw)

    matrix = get_company_ai_dashboard_matrix(company=company)
    passivo_row = next(row for row in matrix["rows"] if row["code"] == "passivo_circulante")

    assert passivo_row["values"]["2025"]["value"] == Decimal("100")
    assert passivo_row["values"]["2025"]["display_value"] == "100"
