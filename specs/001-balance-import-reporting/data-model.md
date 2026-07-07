# Data Model: Balance Import Reporting

## Company

Represents the business entity whose balance documents are stored and analyzed.

**Fields**:

- `id`: UUID primary key
- `legal_name`: canonical company name
- `display_name`: name shown in the UI
- `tax_identifier`: optional national/company identifier
- `country`: optional country code
- `status`: active, archived
- `created_at`, `updated_at`

**Relationships**:

- Has many `CompanyAlias`
- Has many `BalanceDocument`
- Has many `ReportingPeriod`

**Validation Rules**:

- `legal_name` is required.
- `tax_identifier` is unique when present.

## CompanyAlias

Alternative company names found in source documents.

**Fields**:

- `id`: UUID primary key
- `company_id`: Company
- `alias`: extracted or manually added name
- `source`: manual, extraction
- `created_at`

**Validation Rules**:

- Alias must be unique per company.

## BalanceDocument

Raw PDF source file submitted for processing and preserved for reference.

**Fields**:

- `id`: UUID primary key
- `company_id`: Company, nullable until matched
- `original_filename`
- `file_uri`
- `sha256`
- `content_type`
- `file_size_bytes`
- `upload_status`: uploaded, rejected, queued, processing, processed, failed
- `detected_has_text`: boolean
- `detected_language`
- `uploaded_by_id`
- `created_at`, `updated_at`

**Relationships**:

- Has many `ProcessingRun`
- Has many `RawExtraction`
- Has many `ExtractedLineItem`

**Validation Rules**:

- File must be PDF.
- `sha256` prevents silent duplicate documents.
- `file_uri` must be present for accepted documents.

## ProcessingRun

Versioned execution of the extraction and standardization pipeline.

**Fields**:

- `id`: UUID primary key
- `document_id`: BalanceDocument
- `pipeline_version`
- `status`: pending, running, succeeded, failed, cancelled
- `started_at`, `finished_at`
- `duration_ms`
- `error_code`
- `error_message`
- `parameters`: jsonb
- `metrics`: jsonb

**Relationships**:

- Belongs to `BalanceDocument`
- Produces `RawExtraction`
- Produces `ExtractedLineItem`

**State Transitions**:

- pending -> running -> succeeded
- pending -> running -> failed
- pending -> cancelled

## RawExtraction

Raw text, tables and evidence produced from a processing run.

**Fields**:

- `id`: UUID primary key
- `processing_run_id`: ProcessingRun
- `document_id`: BalanceDocument
- `extraction_type`: native_text, ocr_text, table, metadata
- `page_number`
- `content`: jsonb
- `confidence`
- `source_method`
- `created_at`

**Validation Rules**:

- `content` must preserve enough evidence to trace extracted values back to the
  source document.

## ReportingPeriod

The year or interval represented by a balance document.

**Fields**:

- `id`: UUID primary key
- `company_id`: Company
- `period_start`
- `period_end`
- `period_label`
- `currency`
- `created_at`, `updated_at`

**Relationships**:

- Has many `StandardizedBalanceValue`

**Validation Rules**:

- Period end must be on or after period start.
- Company, period label and currency should be unique together unless a
  correction workflow explicitly supersedes a prior period.

## StandardLineItem

Catalog of comparable financial lines used by the dashboard.

**Fields**:

- `id`: UUID primary key
- `code`: stable identifier, such as `cash_and_equivalents`
- `display_name`
- `category`: asset, liability, equity, revenue, expense, other
- `normal_balance`: debit, credit, neutral
- `is_active`
- `sort_order`

**Relationships**:

- Has many `LineItemAlias`
- Has many `ExtractedLineItem`
- Has many `StandardizedBalanceValue`

**Validation Rules**:

- `code` is unique and never reused for a different meaning.

## LineItemAlias

Source labels that map to a standard line item.

**Fields**:

- `id`: UUID primary key
- `standard_line_item_id`: StandardLineItem
- `alias_text`
- `language`
- `created_by_id`
- `created_at`

**Validation Rules**:

- Alias text should be unique per language and standard item unless explicitly
  reviewed.

## ExtractedLineItem

Candidate financial value extracted from a document before or during review.

**Fields**:

- `id`: UUID primary key
- `document_id`: BalanceDocument
- `processing_run_id`: ProcessingRun
- `raw_extraction_id`: RawExtraction
- `source_label`
- `suggested_standard_line_item_id`
- `raw_value`
- `normalized_value`
- `currency`
- `reporting_period_id`
- `confidence`
- `review_status`: pending, approved, rejected, corrected
- `evidence`: jsonb
- `created_at`, `updated_at`

**Validation Rules**:

- `source_label`, `raw_value` and evidence are required.
- Values below the confidence threshold require review.

## StandardizedBalanceValue

Approved value used in comparisons and dashboards.

**Fields**:

- `id`: UUID primary key
- `company_id`: Company
- `reporting_period_id`: ReportingPeriod
- `standard_line_item_id`: StandardLineItem
- `source_extracted_line_item_id`: ExtractedLineItem
- `value`
- `currency`
- `approval_status`: approved, superseded
- `approved_by_id`
- `approved_at`
- `created_at`, `updated_at`

**Relationships**:

- Belongs to company, period and standard line item.
- Links back to the extracted source item.

**Validation Rules**:

- Only approved values appear in the dashboard.
- Company, period and standard line item have one active approved value.

## ReviewTask

Human review item for uncertain, conflicting or missing extraction data.

**Fields**:

- `id`: UUID primary key
- `document_id`: BalanceDocument
- `extracted_line_item_id`: ExtractedLineItem, nullable for document-level tasks
- `reason`: low_confidence, conflict, missing_field, duplicate, validation_error
- `status`: open, in_review, approved, rejected, corrected
- `assigned_to_id`
- `created_at`, `updated_at`, `completed_at`

**State Transitions**:

- open -> in_review -> approved
- open -> in_review -> corrected
- open -> in_review -> rejected

## AuditEvent

Immutable audit record for user and system actions.

**Fields**:

- `id`: UUID primary key
- `actor_user_id`
- `event_type`
- `target_type`
- `target_id`
- `before`: jsonb
- `after`: jsonb
- `reason`
- `ip_address`
- `user_agent`
- `created_at`

**Validation Rules**:

- Audit events are append-only.
- Sensitive values should be redacted before storage when needed.

## Future AI Entities

These are not required for the MVP tables but should be planned as extensions.

- `AIExtractionRun`: model/provider, prompt version, parameters, token/cost
  metadata, output hash and status.
- `PromptTemplate`: versioned prompts for extraction, standardization and
  report generation.
- `AgentTask`: auditable AI worker task linked to a document, review item or
  dashboard report.
