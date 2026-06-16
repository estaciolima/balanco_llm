import pytest
from django.db import IntegrityError

from companies.models import Company, CompanyAlias, ReportingPeriod
from standardization.models import LineItemAlias, StandardLineItem


@pytest.mark.django_db
def test_company_alias_is_unique_per_company():
    company = Company.objects.create(legal_name="ACME")
    CompanyAlias.objects.create(company=company, alias="ACME SA")

    with pytest.raises(IntegrityError):
        CompanyAlias.objects.create(company=company, alias="ACME SA")


@pytest.mark.django_db
def test_reporting_period_is_unique_per_company_year_and_currency():
    company = Company.objects.create(legal_name="ACME")
    ReportingPeriod.objects.create(company=company, fiscal_year=2025, currency="BRL")

    with pytest.raises(IntegrityError):
        ReportingPeriod.objects.create(
            company=company,
            fiscal_year=2025,
            currency="BRL",
        )


@pytest.mark.django_db
def test_standard_line_item_alias_unique():
    item = StandardLineItem.objects.create(
        code="cash_and_equivalents",
        display_name="Cash and Equivalents",
        category=StandardLineItem.Category.ASSET,
    )
    LineItemAlias.objects.create(standard_line_item=item, alias_text="Cash", language="en")

    with pytest.raises(IntegrityError):
        LineItemAlias.objects.create(standard_line_item=item, alias_text="Cash", language="en")
