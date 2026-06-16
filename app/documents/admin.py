from django.contrib import admin

from documents.models import BalanceDocument


@admin.register(BalanceDocument)
class BalanceDocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "company", "upload_status", "created_at")
    search_fields = ("original_filename", "sha256")
    list_filter = ("upload_status",)
