# Generated manually to attach uploaded PDFs to a fiscal year.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0003_reportingperiod_fiscal_year"),
        ("documents", "0002_balancedocument_document_status_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="balancedocument",
            name="reporting_period",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="documents",
                to="companies.reportingperiod",
            ),
        ),
    ]
