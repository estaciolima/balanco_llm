from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from companies.models import Company, ReportingPeriod
from standardization.models import StandardLineItem, StandardizedBalanceValue


@pytest.mark.django_db(transaction=True)
def test_dashboard_comparison_flow(live_server, page):
    user = get_user_model().objects.create_user(username="viewer", password="password123")
    company = Company.objects.create(legal_name="ACME Holdings")
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
        code="net_revenue",
        display_name="Net Revenue",
        category=StandardLineItem.Category.REVENUE,
    )
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period_2024,
        standard_line_item=line_item,
        value=Decimal("1200.00"),
        currency="BRL",
    )
    StandardizedBalanceValue.objects.create(
        company=company,
        reporting_period=period_2025,
        standard_line_item=line_item,
        value=Decimal("1500.00"),
        currency="BRL",
    )

    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill("viewer")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign in").click()

    page.goto(f"{live_server.url}/dashboard/company/{company.pk}/")
    assert page.get_by_role("heading", name="ACME Holdings dashboard").is_visible()
    assert page.get_by_text("Net Revenue").is_visible()
    assert page.get_by_text("2024").is_visible()
    assert page.get_by_text("2025").is_visible()
    assert page.locator("#chart-data").text_content()
