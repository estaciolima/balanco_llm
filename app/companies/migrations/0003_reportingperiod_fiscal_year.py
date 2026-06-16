# Generated manually for the fiscal-year-only period model.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0002_reportingperiod_rpt_period_cmp_end_idx"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="reportingperiod",
            name="rpt_period_cmp_end_idx",
        ),
        migrations.RemoveConstraint(
            model_name="reportingperiod",
            name="uniq_reporting_period_for_company",
        ),
        migrations.RemoveConstraint(
            model_name="reportingperiod",
            name="reporting_period_end_after_start",
        ),
        migrations.AddField(
            model_name="reportingperiod",
            name="fiscal_year",
            field=models.PositiveSmallIntegerField(default=2026),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="reportingperiod",
            name="period_start",
        ),
        migrations.RemoveField(
            model_name="reportingperiod",
            name="period_end",
        ),
        migrations.RemoveField(
            model_name="reportingperiod",
            name="period_label",
        ),
        migrations.AddConstraint(
            model_name="reportingperiod",
            constraint=models.UniqueConstraint(
                fields=("company", "fiscal_year", "currency"),
                name="uniq_reporting_year_for_company",
            ),
        ),
        migrations.AddIndex(
            model_name="reportingperiod",
            index=models.Index(fields=["company", "fiscal_year"], name="rpt_period_cmp_year_idx"),
        ),
        migrations.AlterModelOptions(
            name="reportingperiod",
            options={"ordering": ["-fiscal_year"]},
        ),
    ]
