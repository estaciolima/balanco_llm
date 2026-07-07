import time

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from companies.models import Company


MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.mark.django_db
def test_upload_request_completes_quickly(client, user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.CELERY_TASK_ALWAYS_EAGER = True
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    upload = SimpleUploadedFile("balance.pdf", MINIMAL_PDF, content_type="application/pdf")

    started = time.perf_counter()
    response = client.post(
        reverse("document-upload", args=[company.pk]),
        {"file": upload, "fiscal_year": 2025},
    )
    elapsed = time.perf_counter() - started

    assert response.status_code == 302
    assert elapsed < 5
