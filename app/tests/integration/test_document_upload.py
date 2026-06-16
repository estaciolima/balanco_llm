import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from companies.models import Company
from documents.models import BalanceDocument


MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.mark.django_db
def test_valid_pdf_upload_preserves_raw_file(client, user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.CELERY_TASK_ALWAYS_EAGER = True
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    upload = SimpleUploadedFile("balance.pdf", MINIMAL_PDF, content_type="application/pdf")

    response = client.post(
        reverse("document-upload", args=[company.pk]),
        {"file": upload, "fiscal_year": 2025},
        follow=True,
    )

    assert response.status_code == 200
    document = BalanceDocument.objects.get()
    assert document.original_filename == "balance.pdf"
    assert document.reporting_period.fiscal_year == 2025
    assert document.file.storage.exists(document.file.name)
