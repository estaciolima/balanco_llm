from decimal import Decimal

import pytest
from django.urls import reverse

from companies.models import Company, ReportingPeriod
from standardization.models import StandardLineItem, StandardizedBalanceValue


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
