import pytest
from django.urls import reverse

from companies.models import Company


@pytest.mark.django_db
def test_document_upload_route_requires_authentication(client):
    company = Company.objects.create(legal_name="ACME")

    response = client.get(reverse("document-upload", args=[company.pk]))

    assert response.status_code == 302


@pytest.mark.django_db
def test_document_detail_route_requires_authentication(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")

    response = client.get(reverse("document-upload", args=[company.pk]))

    assert response.status_code == 200
