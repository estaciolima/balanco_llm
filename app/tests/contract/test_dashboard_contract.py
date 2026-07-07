import pytest
from django.urls import reverse

from companies.models import Company


@pytest.mark.django_db
def test_dashboard_route_requires_authentication(client):
    company = Company.objects.create(legal_name="ACME")

    response = client.get(reverse("company-dashboard", args=[company.pk]))

    assert response.status_code == 302


@pytest.mark.django_db
def test_audit_route_requires_authentication(client):
    response = client.get(reverse("audit-event-list"))

    assert response.status_code == 302
