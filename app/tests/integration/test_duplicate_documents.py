import hashlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from companies.models import Company
from documents.models import BalanceDocument


MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.mark.django_db
def test_duplicate_pdf_redirects_to_existing_document(client, user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.CELERY_TASK_ALWAYS_EAGER = True
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    checksum = hashlib.sha256(MINIMAL_PDF).hexdigest()
    BalanceDocument.objects.create(
        company=company,
        original_filename="existing.pdf",
        file="balance-documents/existing.pdf",
        file_uri="/media/balance-documents/existing.pdf",
        sha256=checksum,
        content_type="application/pdf",
        file_size_bytes=len(MINIMAL_PDF),
        uploaded_by=user,
    )
    upload = SimpleUploadedFile("duplicate.pdf", MINIMAL_PDF, content_type="application/pdf")

    response = client.post(
        reverse("document-upload", args=[company.pk]),
        {"file": upload, "fiscal_year": 2025},
    )

    assert response.status_code == 302
    assert BalanceDocument.objects.count() == 1
