import uuid

from django.db import models

from companies.models import ReportingPeriod
from documents.models import BalanceDocument
from standardization.models import StandardLineItem


class ProcessingRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        BalanceDocument, related_name="processing_runs", on_delete=models.CASCADE
    )
    pipeline_version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RawExtraction(models.Model):
    class ExtractionType(models.TextChoices):
        NATIVE_TEXT = "native_text", "Native Text"
        OCR_TEXT = "ocr_text", "OCR Text"
        TABLE = "table", "Table"
        METADATA = "metadata", "Metadata"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_run = models.ForeignKey(
        ProcessingRun, related_name="raw_extractions", on_delete=models.CASCADE
    )
    document = models.ForeignKey(
        BalanceDocument, related_name="raw_extractions", on_delete=models.CASCADE
    )
    extraction_type = models.CharField(max_length=20, choices=ExtractionType.choices)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    content = models.JSONField(default=dict)
    confidence = models.FloatField(null=True, blank=True)
    source_method = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ExtractedLineItem(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CORRECTED = "corrected", "Corrected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        BalanceDocument, related_name="extracted_line_items", on_delete=models.CASCADE
    )
    processing_run = models.ForeignKey(
        ProcessingRun, related_name="extracted_line_items", on_delete=models.CASCADE
    )
    raw_extraction = models.ForeignKey(
        RawExtraction, related_name="extracted_line_items", on_delete=models.CASCADE
    )
    source_account_code = models.CharField(max_length=100, blank=True)
    source_parent_account_code = models.CharField(max_length=100, blank=True)
    source_hierarchy_level = models.PositiveSmallIntegerField(default=0)
    source_balance_nature = models.CharField(max_length=1, blank=True)
    source_label = models.CharField(max_length=255)
    suggested_standard_line_item = models.ForeignKey(
        StandardLineItem,
        null=True,
        blank=True,
        related_name="extracted_line_items",
        on_delete=models.SET_NULL,
    )
    raw_value = models.CharField(max_length=255)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    reporting_period = models.ForeignKey(
        ReportingPeriod, null=True, blank=True, related_name="extracted_line_items", on_delete=models.SET_NULL
    )
    confidence = models.FloatField(default=0.0)
    review_status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["document", "source_account_code"], name="ext_line_doc_code_idx"),
            models.Index(fields=["processing_run", "source_hierarchy_level"], name="ext_line_run_level_idx"),
        ]


class AIExtractionRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        BalanceDocument, related_name="ai_extraction_runs", on_delete=models.CASCADE
    )
    provider = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict, blank=True)
    output_hash = models.CharField(max_length=128, blank=True)
    token_usage = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=30, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)


class PromptTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=50)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AgentTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        BalanceDocument, null=True, blank=True, related_name="agent_tasks", on_delete=models.SET_NULL
    )
    task_type = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="pending")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
