from decimal import Decimal

import pytest
from companies.models import Company, ReportingPeriod
from django.urls import reverse
from standardization.models import StandardizedBalanceValue, StandardLineItem


@pytest.mark.django_db
def test_dashboard_query_count_stays_reasonable(client, user, django_assert_num_queries):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    line_item = StandardLineItem.objects.create(
        code="cash",
        display_name="Cash",
        category=StandardLineItem.Category.ASSET,
    )
    for year in range(2021, 2026):
        period = ReportingPeriod.objects.create(
            company=company,
            fiscal_year=year,
            currency="BRL",
        )
        StandardizedBalanceValue.objects.create(
            company=company,
            reporting_period=period,
            standard_line_item=line_item,
            value=Decimal("100.00"),
            currency="BRL",
        )

    with django_assert_num_queries(6):
        response = client.get(reverse("company-dashboard", args=[company.pk]))

    assert response.status_code == 200
