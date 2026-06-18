from celery import shared_task
from django.utils import timezone
import logging

from audit.services import record_audit_event
from documents.models import BalanceDocument
from extraction.events import PipelineEvent
from extraction.pipeline import process_document
from extraction.models import ProcessingRun

logger = logging.getLogger(__name__)


@shared_task
def queue_processing_run(document_id: str) -> str:
    document = BalanceDocument.objects.get(pk=document_id)
    document.upload_status = BalanceDocument.UploadStatus.QUEUED
    document.save(update_fields=["upload_status", "updated_at"])
    run = ProcessingRun.objects.create(
        document=document,
        pipeline_version="2026.06",
        status=ProcessingRun.Status.PENDING,
        parameters={"queued_at": timezone.now().isoformat()},
    )
    processing_event = PipelineEvent(
        event_type="document.processing.started",
        document_id=str(document.pk),
        processing_run_id=str(run.pk),
        pipeline_version=run.pipeline_version,
        payload={"started_at": timezone.now().isoformat()},
    )
    record_audit_event(
        event_type=processing_event.event_type,
        target_type="BalanceDocument",
        target_id=str(document.pk),
        actor_user=document.uploaded_by,
        after=processing_event.as_dict(),
    )
    if document.file and document.file.storage.exists(document.file.name):
        run_document_pipeline.delay(str(run.pk))
    return str(run.pk)


@shared_task
def run_document_pipeline(processing_run_id: str) -> str:
    run = ProcessingRun.objects.select_related("document").get(pk=processing_run_id)
    run.status = ProcessingRun.Status.RUNNING
    run.started_at = timezone.now()
    run.save(update_fields=["status", "started_at"])
    run.document.upload_status = BalanceDocument.UploadStatus.PROCESSING
    run.document.save(update_fields=["upload_status", "updated_at"])
    try:
        event_payloads = process_document(run.document, run)
        for event_name in ("text_event", "tables_event", "candidates_event"):
            payload = event_payloads.get(event_name)
            if payload:
                record_audit_event(
                    event_type=payload["event_type"],
                    target_type="ProcessingRun",
                    target_id=str(run.pk),
                    actor_user=run.document.uploaded_by,
                    after=payload,
                )
        run.status = ProcessingRun.Status.SUCCEEDED
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])
        run.document.upload_status = BalanceDocument.UploadStatus.PROCESSED
        run.document.save(update_fields=["upload_status", "updated_at"])
        record_audit_event(
            event_type="document.processing.completed",
            target_type="ProcessingRun",
            target_id=str(run.pk),
            actor_user=run.document.uploaded_by,
            after=event_payloads,
        )
    except Exception as exc:
        run.status = ProcessingRun.Status.FAILED
        run.error_code = exc.__class__.__name__
        run.error_message = str(exc)
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_code", "error_message", "finished_at"])
        run.document.upload_status = BalanceDocument.UploadStatus.FAILED
        run.document.save(update_fields=["upload_status", "updated_at"])
        failure_event = PipelineEvent(
            event_type="document.processing.failed",
            document_id=str(run.document.pk),
            processing_run_id=str(run.pk),
            pipeline_version=run.pipeline_version,
            payload={
                "error_code": run.error_code,
                "error_message": run.error_message,
                "failed_stage": "pipeline",
                "retryable": True,
            },
        )
        record_audit_event(
            event_type=failure_event.event_type,
            target_type="ProcessingRun",
            target_id=str(run.pk),
            actor_user=run.document.uploaded_by,
            after=failure_event.as_dict(),
        )
        logger.exception("Document processing failed for run %s", run.pk)
        raise
    return str(run.pk)
