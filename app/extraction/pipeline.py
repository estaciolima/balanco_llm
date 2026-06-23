from django.conf import settings
from django.db import transaction

from extraction.events import PipelineEvent
from extraction.models import AIExtractionRun, ExtractedLineItem, RawExtraction
from extraction.ocr import run_ocr_fallback
from extraction.openai_balance import extract_balance_data
from extraction.parsers import parse_candidate_lines
from extraction.pdf_text import detect_has_text, extract_native_text
from extraction.tables import extract_tables


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

    llm_event = None
    if settings.OPENAI_BALANCE_EXTRACTION_ENABLED:
        llm_run = AIExtractionRun.objects.create(
            document=document,
            provider="openai",
            model_name=settings.OPENAI_BALANCE_EXTRACTION_MODEL,
            prompt_version="2026.06.23",
            parameters={"source_method": source_method, "page_count": len(text_rows)},
            status="running",
        )
        try:
            joined_text = "\n\n".join(
                f"[PÁGINA {row['page_number']}]\n{row['text']}" for row in text_rows
            )
            llm_data, llm_metadata = extract_balance_data(joined_text)
            llm_run.model_name = llm_metadata["model"]
            llm_run.output_hash = llm_metadata["output_hash"]
            llm_run.token_usage = llm_metadata["token_usage"]
            llm_run.status = "succeeded"
            llm_run.save(update_fields=["model_name", "output_hash", "token_usage", "status"])
            RawExtraction.objects.create(
                processing_run=processing_run,
                document=document,
                extraction_type=RawExtraction.ExtractionType.METADATA,
                content={"llm_output": llm_data, "llm_metadata": llm_metadata},
                source_method="openai_structured_output",
            )
            llm_event = PipelineEvent(
                event_type="document.llm.extracted",
                document_id=str(document.pk),
                processing_run_id=str(processing_run.pk),
                pipeline_version=processing_run.pipeline_version,
                payload={
                    "provider": "openai",
                    "model": llm_metadata["model"],
                    "status": "succeeded",
                },
            ).as_dict()
        except Exception:
            llm_run.status = "failed"
            llm_run.save(update_fields=["status"])
            raise

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
            extracted = ExtractedLineItem.objects.create(
                document=document,
                processing_run=processing_run,
                raw_extraction=first_raw,
                source_account_code=candidate.get("source_account_code", ""),
                source_parent_account_code=candidate.get("source_parent_account_code", ""),
                source_hierarchy_level=candidate.get("source_hierarchy_level", 0),
                source_balance_nature=candidate.get("source_balance_nature", ""),
                source_label=candidate["source_label"],
                raw_value=candidate["raw_value"],
                normalized_value=candidate["normalized_value"],
                currency=candidate["currency"],
                reporting_period=candidate["reporting_period"],
                confidence=candidate["confidence"],
                evidence=candidate["evidence"],
            )
            created_items.append(extracted)

    events = {
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
        "candidates_event": PipelineEvent(
            event_type="document.candidates.parsed",
            document_id=str(document.pk),
            processing_run_id=str(processing_run.pk),
            pipeline_version=processing_run.pipeline_version,
            payload={
                "candidate_count": len(candidates),
                "created_line_item_count": len(created_items),
            },
        ).as_dict(),
    }
    if llm_event:
        events["llm_event"] = llm_event
    return events
