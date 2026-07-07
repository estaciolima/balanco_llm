import pytest
from django.urls import reverse

from companies.models import Company


@pytest.mark.django_db
def test_dashboard_shows_empty_state_when_no_values_exist(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")

    response = client.get(reverse("company-dashboard", args=[company.pk]))

    assert response.status_code == 200
    assert "No approved values available" in response.content.decode()
