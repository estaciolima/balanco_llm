import uuid

from django.db import models

from companies.models import Company, ReportingPeriod


class StandardLineItem(models.Model):
    class Category(models.TextChoices):
        ASSET = "asset", "Asset"
        LIABILITY = "liability", "Liability"
        EQUITY = "equity", "Equity"
        REVENUE = "revenue", "Revenue"
        EXPENSE = "expense", "Expense"
        OTHER = "other", "Other"

    class NormalBalance(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"
        NEUTRAL = "neutral", "Neutral"

    class StatementSection(models.TextChoices):
        BALANCE = "balance", "Balance"
        LIQUIDITY = "liquidity", "Liquidity"

    class LineType(models.TextChoices):
        DETAIL = "detail", "Detail"
        SUBTOTAL = "subtotal", "Subtotal"
        TOTAL = "total", "Total"
        RATIO = "ratio", "Ratio"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    statement_section = models.CharField(
        max_length=20, choices=StatementSection.choices, default=StatementSection.BALANCE
    )
    line_type = models.CharField(max_length=20, choices=LineType.choices, default=LineType.DETAIL)
    display_level = models.PositiveSmallIntegerField(default=0)
    normal_balance = models.CharField(
        max_length=20, choices=NormalBalance.choices, default=NormalBalance.NEUTRAL
    )
    formula = models.JSONField(default=dict, blank=True)
    source_account_patterns = models.JSONField(default=list, blank=True)
    is_highlight = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["statement_section", "sort_order", "display_name"]
        indexes = [
            models.Index(fields=["category", "sort_order"], name="std_line_cat_idx"),
            models.Index(fields=["statement_section", "sort_order"], name="std_line_section_idx"),
            models.Index(fields=["parent", "sort_order"], name="std_line_parent_idx"),
        ]

    def __str__(self) -> str:
        return self.display_name


class LineItemAlias(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_line_item = models.ForeignKey(
        StandardLineItem, related_name="aliases", on_delete=models.CASCADE
    )
    alias_text = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default="pt")
    created_by_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["standard_line_item", "alias_text", "language"],
                name="uniq_standard_line_alias",
            )
        ]


class StandardizedBalanceValue(models.Model):
    class ApprovalStatus(models.TextChoices):
        APPROVED = "approved", "Approved"
        SUPERSEDED = "superseded", "Superseded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, related_name="standardized_values", on_delete=models.CASCADE)
    reporting_period = models.ForeignKey(
        ReportingPeriod, related_name="standardized_values", on_delete=models.CASCADE
    )
    standard_line_item = models.ForeignKey(
        StandardLineItem, related_name="standardized_values", on_delete=models.CASCADE
    )
    source_extracted_line_item_id = models.UUIDField(null=True, blank=True)
    source_extracted_account_id = models.UUIDField(null=True, blank=True)
    value = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10)
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.APPROVED
    )
    approved_by_id = models.CharField(max_length=100, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "reporting_period", "standard_line_item", "approval_status"],
                name="uniq_active_standardized_value",
            )
        ]
        indexes = [
            models.Index(
                fields=["company", "approval_status"],
                name="std_value_cmp_status_idx",
            ),
            models.Index(
                fields=["reporting_period", "standard_line_item"],
                name="std_value_period_line_idx",
            ),
        ]
