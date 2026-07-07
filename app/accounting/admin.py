from django.contrib import admin

from accounting.models import AccountingValidationFinding, AccountingValidationRun


class AccountingValidationFindingInline(admin.TabularInline):
    model = AccountingValidationFinding
    extra = 0
    readonly_fields = (
        "rule_id",
        "field_path",
        "severity",
        "outcome",
        "original_value",
        "calculated_value",
        "difference",
        "created_at",
    )


@admin.register(AccountingValidationRun)
class AccountingValidationRunAdmin(admin.ModelAdmin):
    list_display = ("document", "status", "raw_extraction", "duration_ms", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("document__original_filename", "raw_extraction__id")
    readonly_fields = ("created_at",)
    inlines = [AccountingValidationFindingInline]


@admin.register(AccountingValidationFinding)
class AccountingValidationFindingAdmin(admin.ModelAdmin):
    list_display = ("rule_id", "field_path", "severity", "outcome", "validation_run")
    list_filter = ("rule_id", "severity", "outcome")
    search_fields = ("field_path", "message")
