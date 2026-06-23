from decimal import Decimal

import pytest
from companies.models import Company, ReportingPeriod
from dashboard.services import get_company_dashboard_matrix, get_company_dashboard_rows
from standardization.models import StandardizedBalanceValue, StandardLineItem


@pytest.mark.django_db
def test_dashboard_query_groups_approved_values_by_company_and_period():
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
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period,
        standard_line_item=line_item,
        value=Decimal("100.00"),
        currency="BRL",
    )

    rows = get_company_dashboard_rows(company=company)

    assert len(rows) == 1
    assert rows[0]["standard_line_item"] == "Cash and Equivalents"


@pytest.mark.django_db
def test_dashboard_matrix_pivots_values_by_period_and_line_item():
    company = Company.objects.create(legal_name="ACME")
    period_2024 = ReportingPeriod.objects.create(
        company=company,
        fiscal_year=2024,
        currency="BRL",
    )
    period_2025 = ReportingPeriod.objects.create(
        company=company,
        fiscal_year=2025,
        currency="BRL",
    )
    line_item = StandardLineItem.objects.create(
        code="current_assets",
        display_name="ATIVO CIRCULANTE",
        category=StandardLineItem.Category.ASSET,
        line_type=StandardLineItem.LineType.SUBTOTAL,
        is_highlight=True,
        sort_order=110,
    )
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period_2024,
        standard_line_item=line_item,
        value=Decimal("152671509.21"),
        currency="BRL",
    )
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period_2025,
        standard_line_item=line_item,
        value=Decimal("163545229.00"),
        currency="BRL",
    )

    matrix = get_company_dashboard_matrix(company=company)

    assert [period["label"] for period in matrix["periods"]] == ["2024", "2025"]
    assert matrix["rows"][0]["label"] == "ATIVO CIRCULANTE"
    assert matrix["rows"][0]["values"]["2024"]["value"] == Decimal("152671509.21")
    assert matrix["rows"][0]["is_highlight"] is True


@pytest.mark.django_db
def test_dashboard_matrix_calculates_year_over_year_variations():
    company = Company.objects.create(legal_name="ACME")
    line_item = StandardLineItem.objects.create(
        code="cash_variation",
        display_name="Cash",
        category=StandardLineItem.Category.ASSET,
    )
    for year, value in ((2024, "100.00"), (2025, "125.00")):
        period = ReportingPeriod.objects.create(company=company, fiscal_year=year, currency="BRL")
        StandardizedBalanceValue.objects.create(
            company=company,
            reporting_period=period,
            standard_line_item=line_item,
            value=Decimal(value),
            currency="BRL",
        )

    matrix = get_company_dashboard_matrix(company=company)
    values = matrix["rows"][0]["values"]

    assert values["2024"]["variation"]["label"] == "-"
    assert values["2025"]["variation"]["label"] == "▲ +25,0%"
    assert values["2025"]["variation"]["direction"] == "positive"
    assert values["2025"]["variation"]["color"] == "#198754"
