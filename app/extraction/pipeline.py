from django.db import transaction
from django.utils import timezone

from extraction.events import PipelineEvent
from extraction.models import ExtractedLineItem, RawExtraction
from extraction.ocr import run_ocr_fallback
from extraction.parsers import parse_candidate_lines
from extraction.pdf_text import detect_has_text, extract_native_text
from extraction.tables import extract_tables
from extraction.validators import determine_review_reason
from review.services import create_review_task
from standardization.services import match_standard_line_item


def process_document(document, processing_run):
    pdf_path = document.file.path
    has_text = detect_has_text(pdf_path)
    document.detected_has_text = has_text
    document.save(update_fields=["detected_has_text", "updated_at"])

    if has_text:
        text_rows = extract_native_text(pdf_path)
        source_method = "native_text"
    else:
        text_rows = run_ocr_fallback(pdf_path)
        source_method = "ocr"

    raw_text_extractions = [
        RawExtraction(
            processing_run=processing_run,
            document=document,
            extraction_type=RawExtraction.ExtractionType.NATIVE_TEXT
            if source_method == "native_text"
            else RawExtraction.ExtractionType.OCR_TEXT,
            page_number=row.get("page_number"),
            content=row,
            confidence=row.get("confidence"),
            source_method=source_method,
        )
        for row in text_rows
    ]
    RawExtraction.objects.bulk_create(raw_text_extractions)

    table_rows = extract_tables(pdf_path)
    for table in table_rows:
        RawExtraction.objects.create(
            processing_run=processing_run,
            document=document,
            extraction_type=RawExtraction.ExtractionType.TABLE,
            page_number=table.get("page_number"),
            content=table,
            source_method="pdfplumber",
        )

    candidates = parse_candidate_lines(text_rows, reporting_period=document.reporting_period)
    created_items = []
    with transaction.atomic():
        first_raw = document.raw_extractions.filter(processing_run=processing_run).first()
        for candidate in candidates:
            matched_item, match_confidence = match_standard_line_item(
                candidate["source_label"],
                source_account_code=candidate.get("source_account_code", ""),
            )
            final_confidence = max(candidate["confidence"], match_confidence)
            extracted = ExtractedLineItem.objects.create(
                document=document,
                processing_run=processing_run,
                raw_extraction=first_raw,
                source_account_code=candidate.get("source_account_code", ""),
                source_parent_account_code=candidate.get("source_parent_account_code", ""),
                source_hierarchy_level=candidate.get("source_hierarchy_level", 0),
                source_balance_nature=candidate.get("source_balance_nature", ""),
                source_label=candidate["source_label"],
                suggested_standard_line_item=matched_item,
                raw_value=candidate["raw_value"],
                normalized_value=candidate["normalized_value"],
                currency=candidate["currency"],
                reporting_period=candidate["reporting_period"],
                confidence=final_confidence,
                evidence=candidate["evidence"],
            )
            review_reason = determine_review_reason(
                confidence=final_confidence,
                normalized_value=extracted.normalized_value,
                suggested_standard_line_item=matched_item,
            )
            if review_reason:
                create_review_task(
                    document=document,
                    extracted_line_item=extracted,
                    reason=review_reason,
                )
            created_items.append(extracted)

    return {
        "text_event": PipelineEvent(
            event_type="document.text.extracted",
            document_id=str(document.pk),
            processing_run_id=str(processing_run.pk),
            pipeline_version=processing_run.pipeline_version,
            payload={
                "source_method": source_method,
                "page_count": len(text_rows),
                "detected_language": document.detected_language or "",
                "confidence": 1.0 if has_text else 0.6,
            },
        ).as_dict(),
        "tables_event": PipelineEvent(
            event_type="document.tables.extracted",
            document_id=str(document.pk),
            processing_run_id=str(processing_run.pk),
            pipeline_version=processing_run.pipeline_version,
            payload={
                "table_count": len(table_rows),
                "pages_with_tables": [table.get("page_number") for table in table_rows],
                "confidence": 0.8 if table_rows else 0.0,
            },
        ).as_dict(),
        "standardization_event": PipelineEvent(
            event_type="document.standardization.completed",
            document_id=str(document.pk),
            processing_run_id=str(processing_run.pk),
            pipeline_version=processing_run.pipeline_version,
            payload={
                "candidate_count": len(candidates),
                "standardized_count": len([item for item in created_items if item.suggested_standard_line_item]),
                "review_required_count": document.review_tasks.filter(status="open").count(),
            },
        ).as_dict(),
    }
