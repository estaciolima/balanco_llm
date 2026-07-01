# Generated manually for accounting validation MVP.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("documents", "0001_initial"),
        ("extraction", "0003_prompttemplate_agenttask_aiextractionrun"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountingValidationRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("consistent", "Consistent"),
                            ("warning", "Warning"),
                            ("inconsistent", "Inconsistent"),
                            ("not_assessable", "Not assessable"),
                        ],
                        default="not_assessable",
                        max_length=30,
                    ),
                ),
                ("tolerance_amount", models.DecimalField(decimal_places=6, max_digits=18)),
                ("tolerance_ratio", models.DecimalField(decimal_places=6, max_digits=18)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("validated_output", models.JSONField(blank=True, default=dict)),
                ("duration_ms", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ai_extraction_run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="accounting_validation_runs",
                        to="extraction.aiextractionrun",
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounting_validation_runs",
                        to="documents.balancedocument",
                    ),
                ),
                (
                    "raw_extraction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounting_validation_runs",
                        to="extraction.rawextraction",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AccountingValidationFinding",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("rule_id", models.CharField(max_length=100)),
                ("field_path", models.CharField(blank=True, max_length=255)),
                (
                    "severity",
                    models.CharField(
                        choices=[("info", "Info"), ("warning", "Warning"), ("high", "High")],
                        max_length=20,
                    ),
                ),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("passed", "Passed"),
                            ("failed", "Failed"),
                            ("corrected", "Corrected"),
                            ("not_assessable", "Not assessable"),
                        ],
                        max_length=30,
                    ),
                ),
                ("message", models.TextField()),
                (
                    "original_value",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=20, null=True),
                ),
                (
                    "calculated_value",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=20, null=True),
                ),
                (
                    "difference",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=20, null=True),
                ),
                ("inputs", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "validation_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="findings",
                        to="accounting.accountingvalidationrun",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "rule_id", "field_path"],
            },
        ),
        migrations.AddIndex(
            model_name="accountingvalidationrun",
            index=models.Index(fields=["document", "-created_at"], name="acct_run_doc_created_idx"),
        ),
        migrations.AddIndex(
            model_name="accountingvalidationrun",
            index=models.Index(
                fields=["raw_extraction", "-created_at"],
                name="acct_run_raw_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="accountingvalidationfinding",
            index=models.Index(fields=["validation_run", "rule_id"], name="acct_find_run_rule_idx"),
        ),
        migrations.AddIndex(
            model_name="accountingvalidationfinding",
            index=models.Index(fields=["outcome", "severity"], name="acct_find_outcome_idx"),
        ),
    ]
