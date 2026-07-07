from django.contrib import admin

from review.models import ReviewTask
from standardization.models import StandardizedBalanceValue


@admin.register(ReviewTask)
class ReviewTaskAdmin(admin.ModelAdmin):
    list_display = ("document", "reason", "status", "created_at")


@admin.register(StandardizedBalanceValue)
class StandardizedBalanceValueAdmin(admin.ModelAdmin):
    list_display = ("company", "reporting_period", "standard_line_item", "value", "approval_status")
