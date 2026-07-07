from __future__ import annotations

import hashlib
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from audit.services import record_audit_event
from companies.models import ReportingPeriod
from documents.models import BalanceDocument
from documents.storage import get_document_storage
from extraction.events import PipelineEvent
from extraction.tasks import queue_processing_run


class UnsupportedDocumentError(ValueError):
    pass


class DuplicateDocumentError(ValueError):
    def __init__(self, document: BalanceDocument):
        self.document = document
        super().__init__("A document with the same checksum already exists.")


def _sha256_for_uploaded_file(uploaded_file: UploadedFile) -> str:
    digest = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


def get_or_create_reporting_year(*, company, fiscal_year: int, currency: str = "BRL") -> ReportingPeriod:
    reporting_period, _created = ReportingPeriod.objects.get_or_create(
        company=company,
        fiscal_year=fiscal_year,
        currency=currency,
    )
    return reporting_period


def create_balance_document(
    *, company, uploaded_file: UploadedFile, actor_user, fiscal_year: int, currency: str = "BRL"
) -> BalanceDocument:
    content_type = getattr(uploaded_file, "content_type", "application/pdf") or "application/pdf"
    file_size = getattr(uploaded_file, "size", None)
    if file_size is None:
        uploaded_file.seek(0, 2)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)

    if content_type != "application/pdf" and not uploaded_file.name.lower().endswith(".pdf"):
        raise UnsupportedDocumentError("Only PDF files are supported.")

    sha256 = _sha256_for_uploaded_file(uploaded_file)
    duplicate = BalanceDocument.objects.filter(sha256=sha256).first()
    if duplicate:
        raise DuplicateDocumentError(duplicate)

    storage = get_document_storage()
    stored_name = storage.save(uploaded_file.name, uploaded_file)
    reporting_period = get_or_create_reporting_year(
        company=company,
        fiscal_year=fiscal_year,
        currency=currency,
    )
    document = BalanceDocument.objects.create(
        company=company,
        reporting_period=reporting_period,
        original_filename=uploaded_file.name,
        file=stored_name,
        file_uri=storage.url(stored_name),
        sha256=sha256,
        content_type=content_type,
        file_size_bytes=file_size,
        uploaded_by=actor_user,
        upload_status=BalanceDocument.UploadStatus.UPLOADED,
    )

    upload_event = PipelineEvent(
        event_type="document.uploaded",
        document_id=str(document.pk),
        processing_run_id=None,
        pipeline_version="2026.06",
        payload={
            "company_id": str(company.pk),
            "reporting_period_id": str(reporting_period.pk),
            "fiscal_year": fiscal_year,
            "filename": uploaded_file.name,
            "sha256": sha256,
            "file_size_bytes": file_size,
        },
    )
    record_audit_event(
        event_type=upload_event.event_type,
        target_type="BalanceDocument",
        target_id=str(document.pk),
        actor_user=actor_user,
        after=upload_event.as_dict(),
    )

    if settings.CELERY_TASK_ALWAYS_EAGER:
        queue_processing_run(str(document.pk))
    else:
        queue_processing_run.delay(str(document.pk))
    return document


def requeue_processing(document: BalanceDocument, actor_user) -> str:
    if settings.CELERY_TASK_ALWAYS_EAGER:
        run_id = queue_processing_run(str(document.pk))
    else:
        run_id = queue_processing_run.delay(str(document.pk))
    record_audit_event(
        event_type="document.reprocessed",
        target_type="BalanceDocument",
        target_id=str(document.pk),
        actor_user=actor_user,
        after={"queued_processing_run": str(run_id)},
    )
    return str(run_id)


def document_download_name(document: BalanceDocument) -> str:
    return Path(document.original_filename).name
