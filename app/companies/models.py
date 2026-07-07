import uuid

from django.db import models


class Company(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    tax_identifier = models.CharField(max_length=100, blank=True, unique=True, null=True)
    country = models.CharField(max_length=2, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["legal_name"]

    def __str__(self) -> str:
        return self.display_name or self.legal_name


class CompanyAlias(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        EXTRACTION = "extraction", "Extraction"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, related_name="aliases", on_delete=models.CASCADE)
    alias = models.CharField(max_length=255)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "alias"], name="uniq_company_alias")
        ]
        ordering = ["alias"]


class ReportingPeriod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, related_name="reporting_periods", on_delete=models.CASCADE)
    fiscal_year = models.PositiveSmallIntegerField()
    currency = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "fiscal_year", "currency"],
                name="uniq_reporting_year_for_company",
            ),
        ]
        ordering = ["-fiscal_year"]
        indexes = [
            models.Index(fields=["company", "fiscal_year"], name="rpt_period_cmp_year_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.company} - {self.fiscal_year} ({self.currency})"
