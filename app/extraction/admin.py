from django.contrib import admin

from extraction.models import ExtractedLineItem, ProcessingRun, RawExtraction


@admin.register(ProcessingRun)
class ProcessingRunAdmin(admin.ModelAdmin):
    list_display = ("document", "pipeline_version", "status", "created_at")
    list_filter = ("status",)


@admin.register(RawExtraction)
class RawExtractionAdmin(admin.ModelAdmin):
    list_display = ("document", "extraction_type", "page_number", "created_at")


@admin.register(ExtractedLineItem)
class ExtractedLineItemAdmin(admin.ModelAdmin):
    list_display = ("source_label", "document", "confidence", "review_status", "created_at")
