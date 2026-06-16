from django.utils import timezone

from audit.services import record_audit_event
from extraction.events import PipelineEvent
from extraction.models import ExtractedLineItem
from review.models import ReviewTask
from standardization.models import StandardizedBalanceValue


def _supersede_existing_value(*, company, reporting_period, standard_line_item):
    StandardizedBalanceValue.objects.filter(
        company=company,
        reporting_period=reporting_period,
        standard_line_item=standard_line_item,
        approval_status=StandardizedBalanceValue.ApprovalStatus.APPROVED,
    ).update(approval_status=StandardizedBalanceValue.ApprovalStatus.SUPERSEDED)


def create_review_task(*, document, extracted_line_item, reason: str) -> ReviewTask:
    task = ReviewTask.objects.create(
        document=document,
        extracted_line_item=extracted_line_item,
        reason=reason,
    )
    event = PipelineEvent(
        event_type="review.task.created",
        document_id=str(document.pk),
        processing_run_id=str(extracted_line_item.processing_run_id) if extracted_line_item else None,
        pipeline_version="2026.06",
        payload={
            "review_task_id": str(task.pk),
            "reason": reason,
            "extracted_line_item_id": str(extracted_line_item.pk) if extracted_line_item else None,
        },
    )
    record_audit_event(
        event_type=event.event_type,
        target_type="ReviewTask",
        target_id=str(task.pk),
        after=event.as_dict(),
    )
    return task


def approve_review_task(*, review_task: ReviewTask, actor_user):
    item = review_task.extracted_line_item
    item.review_status = ExtractedLineItem.ReviewStatus.APPROVED
    item.save(update_fields=["review_status", "updated_at"])
    _supersede_existing_value(
        company=review_task.document.company,
        reporting_period=item.reporting_period,
        standard_line_item=item.suggested_standard_line_item,
    )
    value = StandardizedBalanceValue.objects.create(
        company=review_task.document.company,
        reporting_period=item.reporting_period,
        standard_line_item=item.suggested_standard_line_item,
        source_extracted_line_item_id=item.pk,
        value=item.normalized_value,
        currency=item.currency,
        approved_by_id=str(actor_user.pk),
        approved_at=timezone.now(),
    )
    review_task.status = ReviewTask.Status.APPROVED
    review_task.completed_at = timezone.now()
    review_task.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit_event(
        event_type="review.approved",
        target_type="ReviewTask",
        target_id=str(review_task.pk),
        actor_user=actor_user,
        after={"standardized_balance_value_id": str(value.pk)},
    )
    approval_event = PipelineEvent(
        event_type="balance.value.approved",
        document_id=str(review_task.document.pk),
        processing_run_id=str(item.processing_run_id),
        pipeline_version="2026.06",
        payload={
            "company_id": str(review_task.document.company_id),
            "reporting_period_id": str(item.reporting_period_id),
            "standard_line_item_id": str(item.suggested_standard_line_item_id),
            "value": str(value.value),
            "currency": value.currency,
        },
    )
    record_audit_event(
        event_type=approval_event.event_type,
        target_type="StandardizedBalanceValue",
        target_id=str(value.pk),
        actor_user=actor_user,
        after=approval_event.as_dict(),
    )
    return value


def reject_review_task(*, review_task: ReviewTask, actor_user, reason: str):
    if review_task.extracted_line_item:
        review_task.extracted_line_item.review_status = ExtractedLineItem.ReviewStatus.REJECTED
        review_task.extracted_line_item.save(update_fields=["review_status", "updated_at"])
    review_task.status = ReviewTask.Status.REJECTED
    review_task.completed_at = timezone.now()
    review_task.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit_event(
        event_type="review.rejected",
        target_type="ReviewTask",
        target_id=str(review_task.pk),
        actor_user=actor_user,
        reason=reason,
    )


def correct_review_task(
    *,
    review_task: ReviewTask,
    actor_user,
    standard_line_item,
    value,
    currency,
    reporting_period,
    reason: str,
):
    item = review_task.extracted_line_item
    item.suggested_standard_line_item = standard_line_item
    item.normalized_value = value
    item.currency = currency
    item.reporting_period = reporting_period
    item.review_status = ExtractedLineItem.ReviewStatus.CORRECTED
    item.save()
    _supersede_existing_value(
        company=review_task.document.company,
        reporting_period=reporting_period,
        standard_line_item=standard_line_item,
    )
    standardized_value = StandardizedBalanceValue.objects.create(
        company=review_task.document.company,
        reporting_period=reporting_period,
        standard_line_item=standard_line_item,
        source_extracted_line_item_id=item.pk,
        value=value,
        currency=currency,
        approved_by_id=str(actor_user.pk),
        approved_at=timezone.now(),
    )
    review_task.status = ReviewTask.Status.CORRECTED
    review_task.completed_at = timezone.now()
    review_task.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit_event(
        event_type="review.corrected",
        target_type="ReviewTask",
        target_id=str(review_task.pk),
        actor_user=actor_user,
        reason=reason,
        after={"standardized_balance_value_id": str(standardized_value.pk)},
    )
    approval_event = PipelineEvent(
        event_type="balance.value.approved",
        document_id=str(review_task.document.pk),
        processing_run_id=str(item.processing_run_id),
        pipeline_version="2026.06",
        payload={
            "company_id": str(review_task.document.company_id),
            "reporting_period_id": str(reporting_period.pk),
            "standard_line_item_id": str(standard_line_item.pk),
            "value": str(standardized_value.value),
            "currency": standardized_value.currency,
        },
    )
    record_audit_event(
        event_type=approval_event.event_type,
        target_type="StandardizedBalanceValue",
        target_id=str(standardized_value.pk),
        actor_user=actor_user,
        after=approval_event.as_dict(),
    )
    return standardized_value
