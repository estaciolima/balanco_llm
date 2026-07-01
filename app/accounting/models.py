import uuid

from django.db import models
from documents.models import BalanceDocument
from extraction.models import AIExtractionRun, RawExtraction


class AccountingValidationRun(models.Model):
    class Status(models.TextChoices):
        CONSISTENT = "consistent", "Consistent"
        WARNING = "warning", "Warning"
        INCONSISTENT = "inconsistent", "Inconsistent"
        NOT_ASSESSABLE = "not_assessable", "Not assessable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        BalanceDocument, related_name="accounting_validation_runs", on_delete=models.CASCADE
    )
    raw_extraction = models.ForeignKey(
        RawExtraction, related_name="accounting_validation_runs", on_delete=models.CASCADE
    )
    ai_extraction_run = models.ForeignKey(
        AIExtractionRun,
        null=True,
        blank=True,
        related_name="accounting_validation_runs",
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.NOT_ASSESSABLE
    )
    tolerance_amount = models.DecimalField(max_digits=18, decimal_places=6)
    tolerance_ratio = models.DecimalField(max_digits=18, decimal_places=6)
    summary = models.JSONField(default=dict, blank=True)
    validated_output = models.JSONField(default=dict, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["document", "-created_at"], name="acct_run_doc_created_idx"),
            models.Index(fields=["raw_extraction", "-created_at"], name="acct_run_raw_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.status} validation for {self.document_id}"


class AccountingValidationFinding(models.Model):
    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        HIGH = "high", "High"

    class Outcome(models.TextChoices):
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        CORRECTED = "corrected", "Corrected"
        NOT_ASSESSABLE = "not_assessable", "Not assessable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validation_run = models.ForeignKey(
        AccountingValidationRun, related_name="findings", on_delete=models.CASCADE
    )
    rule_id = models.CharField(max_length=100)
    field_path = models.CharField(max_length=255, blank=True)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    outcome = models.CharField(max_length=30, choices=Outcome.choices)
    message = models.TextField()
    original_value = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    calculated_value = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    difference = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    inputs = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "rule_id", "field_path"]
        indexes = [
            models.Index(fields=["validation_run", "rule_id"], name="acct_find_run_rule_idx"),
            models.Index(fields=["outcome", "severity"], name="acct_find_outcome_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.rule_id} {self.outcome}"
