from decimal import Decimal

import pytest
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from companies.models import Company, ReportingPeriod
from standardization.models import StandardLineItem, StandardizedBalanceValue


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

    with django_assert_num_queries(5):
        response = client.get(reverse("company-dashboard", args=[company.pk]))

    assert response.status_code == 200
