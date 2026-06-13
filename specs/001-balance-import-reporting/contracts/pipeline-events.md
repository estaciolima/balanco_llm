# Pipeline Event Contract: Balance Import Reporting

Pipeline stages are internal tasks, but each stage must emit auditable status
events so retries, review and future AI workers remain traceable.

## Common Event Envelope

```json
{
  "event_id": "uuid",
  "event_type": "document.processing.started",
  "occurred_at": "2026-06-12T12:00:00Z",
  "document_id": "uuid",
  "processing_run_id": "uuid",
  "pipeline_version": "2026.06",
  "actor": "system",
  "payload": {}
}
```

## Required Event Types

### document.uploaded

Emitted after a PDF is accepted and persisted.

**Payload**:

- `company_id`
- `filename`
- `sha256`
- `file_size_bytes`

### document.processing.started

Emitted when a worker starts a processing run.

**Payload**:

- `started_at`
- `pipeline_version`

### document.text.extracted

Emitted after text extraction or OCR completes.

**Payload**:

- `source_method`: native_text or ocr
- `page_count`
- `detected_language`
- `confidence`

### document.tables.extracted

Emitted after table extraction completes.

**Payload**:

- `table_count`
- `pages_with_tables`
- `confidence`

### document.standardization.completed

Emitted after candidate line items are mapped to standard line items.

**Payload**:

- `candidate_count`
- `standardized_count`
- `review_required_count`

### review.task.created

Emitted when a human review task is required.

**Payload**:

- `review_task_id`
- `reason`
- `extracted_line_item_id`

### balance.value.approved

Emitted when an approved value becomes available for the dashboard.

**Payload**:

- `company_id`
- `reporting_period_id`
- `standard_line_item_id`
- `value`
- `currency`

### document.processing.failed

Emitted when a processing run fails.

**Payload**:

- `error_code`
- `error_message`
- `failed_stage`
- `retryable`

## Contract Rules

- Events are append-only.
- Every event must link to a document and processing run when applicable.
- Failed stages must preserve enough context for retry or manual inspection.
- Future LLM or agent stages must use the same envelope and include provider,
  model, prompt version and output hash in payload metadata.
