import pytest
from django.urls import reverse

from companies.models import Company
from documents.models import BalanceDocument
from review.models import ReviewTask


@pytest.mark.django_db
def test_review_queue_requires_authentication(client):
    response = client.get(reverse("review-queue"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_review_detail_is_available_to_authenticated_user(client, user):
    client.force_login(user)
    company = Company.objects.create(legal_name="ACME")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance.pdf",
        file="balance-documents/balance.pdf",
        file_uri="/media/balance-documents/balance.pdf",
        sha256="abc123",
        content_type="application/pdf",
        file_size_bytes=10,
        uploaded_by=user,
    )
    task = ReviewTask.objects.create(document=document, reason=ReviewTask.Reason.MISSING_FIELD)

    response = client.get(reverse("review-detail", args=[task.pk]))

    assert response.status_code == 200
