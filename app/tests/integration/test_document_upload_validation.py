import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from companies.models import Company
from documents.models import BalanceDocument


@pytest.mark.django_db
def test_non_pdf_upload_is_rejected(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    upload = SimpleUploadedFile("notes.txt", b"not a pdf", content_type="text/plain")

    response = client.post(
        reverse("document-upload", args=[company.pk]),
        {"file": upload, "fiscal_year": 2025},
    )

    assert response.status_code == 200
    assert BalanceDocument.objects.count() == 0
    assert "Only PDF files are supported." in response.content.decode()
