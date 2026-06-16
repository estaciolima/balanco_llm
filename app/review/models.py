import uuid

from django.conf import settings
from django.db import models

from documents.models import BalanceDocument
from extraction.models import ExtractedLineItem


class ReviewTask(models.Model):
    class Reason(models.TextChoices):
        LOW_CONFIDENCE = "low_confidence", "Low confidence"
        CONFLICT = "conflict", "Conflict"
        MISSING_FIELD = "missing_field", "Missing field"
        DUPLICATE = "duplicate", "Duplicate"
        VALIDATION_ERROR = "validation_error", "Validation error"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CORRECTED = "corrected", "Corrected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(BalanceDocument, related_name="review_tasks", on_delete=models.CASCADE)
    extracted_line_item = models.ForeignKey(
        ExtractedLineItem,
        null=True,
        blank=True,
        related_name="review_tasks",
        on_delete=models.CASCADE,
    )
    reason = models.CharField(max_length=30, choices=Reason.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
