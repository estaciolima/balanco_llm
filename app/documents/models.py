import uuid

from django.conf import settings
from django.db import models

from companies.models import Company, ReportingPeriod


class BalanceDocument(models.Model):
    class UploadStatus(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        REJECTED = "rejected", "Rejected"
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company, null=True, blank=True, related_name="documents", on_delete=models.SET_NULL
    )
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        null=True,
        blank=True,
        related_name="documents",
        on_delete=models.SET_NULL,
    )
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="balance-documents/")
    file_uri = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64, unique=True)
    content_type = models.CharField(max_length=100)
    file_size_bytes = models.PositiveBigIntegerField()
    upload_status = models.CharField(
        max_length=20, choices=UploadStatus.choices, default=UploadStatus.UPLOADED
    )
    detected_has_text = models.BooleanField(null=True, blank=True)
    detected_language = models.CharField(max_length=20, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["upload_status"], name="document_status_idx"),
            models.Index(fields=["company", "upload_status"], name="document_company_status_idx"),
        ]

    def __str__(self) -> str:
        return self.original_filename
