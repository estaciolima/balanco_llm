# Tasks: Balance Import Reporting

**Input**: Design documents from `/specs/001-balance-import-reporting/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required for behavior changes by the project constitution.

**Organization**: Tasks are grouped by user story so each story can be built,
tested and demonstrated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks
- **[Story]**: User story label for story phases only
- Every task includes an exact file path

## Phase 1: Setup

**Purpose**: Create the Django project skeleton, local runtime and test tooling.

- [X] T001 Create Python project metadata and dependencies in pyproject.toml
- [X] T002 Create Django project entrypoint in app/manage.py
- [X] T003 Create Django settings package in app/config/settings.py
- [X] T004 Create root URL configuration in app/config/urls.py
- [X] T005 Create WSGI/ASGI configuration in app/config/wsgi.py and app/config/asgi.py
- [X] T006 Create Docker Compose services for web, worker, beat, postgres and redis in docker-compose.yml
- [X] T007 Create web container definition in docker/web.Dockerfile
- [X] T008 Create worker container definition in docker/worker.Dockerfile
- [X] T009 Create local environment example in .env.example
- [X] T010 Configure pytest and pytest-django in pytest.ini
- [X] T011 [P] Create shared test fixtures in app/tests/conftest.py
- [X] T012 [P] Create base layout template in app/templates/base.html
- [X] T013 [P] Create static asset entrypoint in app/static/css/app.css

## Phase 2: Foundational

**Purpose**: Implement shared models, auth, audit, storage and pipeline plumbing that block all user stories.

- [X] T014 Create Django apps for accounts, companies, documents, extraction, standardization, review, dashboard and audit in app/config/settings.py
- [X] T015 Implement user role groups and permission bootstrap command in app/accounts/management/commands/bootstrap_roles.py
- [X] T016 Implement audit event model in app/audit/models.py
- [X] T017 Implement audit event writer service in app/audit/services.py
- [X] T018 [P] Add audit event unit tests in app/tests/unit/test_audit_events.py
- [X] T019 Implement Company and CompanyAlias models in app/companies/models.py
- [X] T020 Implement ReportingPeriod model in app/companies/models.py
- [X] T021 Implement StandardLineItem and LineItemAlias models in app/standardization/models.py
- [X] T022 Implement initial standard line item loader in app/standardization/management/commands/load_standard_line_items.py
- [X] T023 [P] Add model constraint tests for companies and standard line items in app/tests/unit/test_foundational_models.py
- [X] T024 Implement file storage abstraction for local and S3-compatible backends in app/documents/storage.py
- [X] T025 Implement Celery application configuration in app/config/celery.py
- [X] T026 Implement pipeline event envelope and emitter in app/extraction/events.py
- [X] T027 [P] Add contract tests for pipeline event envelope in app/tests/contract/test_pipeline_events.py
- [X] T028 Implement shared navigation and auth-aware shell in app/templates/base.html
- [X] T029 Add login, logout and role-based access tests in app/tests/integration/test_auth_flow.py

## Phase 3: User Story 1 - Import Company PDFs (Priority: P1)

**Goal**: A reviewer can create/open a company, upload a PDF, preserve the raw file, queue processing and see status.

**Independent Test**: Upload a valid PDF and verify raw preservation, duplicate detection, queued processing and status display.

### Tests for User Story 1

- [X] T030 [P] [US1] Add contract tests for company and document upload routes in app/tests/contract/test_document_upload_contract.py
- [X] T031 [P] [US1] Add integration test for valid PDF upload and raw file preservation in app/tests/integration/test_document_upload.py
- [X] T032 [P] [US1] Add integration test for unsupported file rejection in app/tests/integration/test_document_upload_validation.py
- [X] T033 [P] [US1] Add integration test for duplicate PDF checksum handling in app/tests/integration/test_duplicate_documents.py

### Implementation for User Story 1

- [X] T034 [US1] Implement BalanceDocument model and upload status choices in app/documents/models.py
- [X] T035 [US1] Implement ProcessingRun model and state transitions in app/extraction/models.py
- [X] T036 [US1] Create migrations for companies, standardization, documents, extraction and audit in app/*/migrations/
- [X] T037 [US1] Implement company list, detail and create views in app/companies/views.py
- [X] T038 [US1] Implement company URL routes in app/companies/urls.py
- [X] T039 [US1] Create company list, detail and form templates in app/templates/companies/
- [X] T040 [US1] Implement PDF validation, checksum and duplicate detection service in app/documents/services.py
- [X] T041 [US1] Implement document upload form in app/documents/forms.py
- [X] T042 [US1] Implement document upload, detail and reprocess views in app/documents/views.py
- [X] T043 [US1] Implement document URL routes in app/documents/urls.py
- [X] T044 [US1] Create document upload and detail templates in app/templates/documents/
- [X] T045 [US1] Implement Celery task to create queued ProcessingRun after upload in app/extraction/tasks.py
- [X] T046 [US1] Emit document.uploaded and document.processing.started events in app/documents/services.py and app/extraction/tasks.py
- [X] T047 [US1] Record upload and duplicate audit events in app/documents/services.py
- [X] T048 [US1] Add Django admin registrations for Company, BalanceDocument and ProcessingRun in app/companies/admin.py and app/documents/admin.py
- [X] T049 [US1] Add Playwright E2E test for login, company creation and PDF upload in app/tests/e2e/test_upload_flow.py

**Checkpoint**: User Story 1 is complete when a valid PDF can be uploaded, preserved and queued without exposing data from ignored local sample folders.

## Phase 4: User Story 2 - Review Structured Company Data (Priority: P2)

**Goal**: A reviewer can inspect extracted and standardized values, approve correct values, correct wrong values and reject invalid values.

**Independent Test**: Process a document into candidate line items, open the review queue and approve/correct/reject items with audit history.

### Tests for User Story 2

- [X] T050 [P] [US2] Add unit tests for native text extraction and OCR routing in app/tests/unit/test_pdf_text_extraction.py
- [X] T051 [P] [US2] Add unit tests for table candidate parsing in app/tests/unit/test_table_candidate_parser.py
- [X] T052 [P] [US2] Add unit tests for standard line item mapping in app/tests/unit/test_line_item_standardization.py
- [X] T053 [P] [US2] Add integration test for processing run producing raw extractions and review tasks in app/tests/integration/test_processing_pipeline.py
- [X] T054 [P] [US2] Add contract tests for review routes in app/tests/contract/test_review_contract.py
- [X] T055 [P] [US2] Add integration test for approve, correct and reject review actions in app/tests/integration/test_review_actions.py

### Implementation for User Story 2

- [X] T056 [US2] Implement RawExtraction and ExtractedLineItem models in app/extraction/models.py
- [X] T057 [US2] Implement ReviewTask model in app/review/models.py
- [X] T058 [US2] Implement StandardizedBalanceValue model in app/standardization/models.py
- [X] T059 [US2] Create migrations for extraction, review and standardized values in app/*/migrations/
- [X] T060 [US2] Implement PDF text detector and native text extractor using PyMuPDF in app/extraction/pdf_text.py
- [X] T061 [US2] Implement OCR fallback adapter for OCRmyPDF/Tesseract in app/extraction/ocr.py
- [X] T062 [US2] Implement table extraction adapter using pdfplumber in app/extraction/tables.py
- [X] T063 [US2] Implement candidate parsing service for labels, values, currency and period in app/extraction/parsers.py
- [X] T064 [US2] Implement standardization service mapping aliases to StandardLineItem in app/standardization/services.py
- [X] T065 [US2] Implement validation service for confidence, conflicts, missing fields and duplicate periods in app/extraction/validators.py
- [X] T066 [US2] Implement processing pipeline orchestration in app/extraction/pipeline.py
- [X] T067 [US2] Update Celery processing task to run extraction, standardization and review routing in app/extraction/tasks.py
- [X] T068 [US2] Emit document.text.extracted, document.tables.extracted, document.standardization.completed and review.task.created events in app/extraction/pipeline.py
- [X] T069 [US2] Implement review queue and review detail views in app/review/views.py
- [X] T070 [US2] Implement approve, correct and reject review actions in app/review/views.py
- [X] T071 [US2] Implement review forms in app/review/forms.py
- [X] T072 [US2] Implement review URL routes in app/review/urls.py
- [X] T073 [US2] Create review queue and review workspace templates in app/templates/review/
- [X] T074 [US2] Add PDF evidence panel partial template in app/templates/documents/_pdf_evidence.html
- [X] T075 [US2] Record review action audit events in app/review/services.py
- [X] T076 [US2] Add Django admin registrations for extraction, review and standardized value models in app/extraction/admin.py and app/review/admin.py
- [X] T077 [US2] Add Playwright E2E test for review approve and correction flow in app/tests/e2e/test_review_flow.py

**Checkpoint**: User Story 2 is complete when extracted values can be reviewed with source evidence and only approved/corrected values are published.

## Phase 5: User Story 3 - Compare Balances Over Time (Priority: P3)

**Goal**: A user can view approved standardized values by company and compare available years in a dashboard.

**Independent Test**: Open a company with multiple approved reporting periods and verify year-over-year comparison, missing-year gaps and source traceability.

### Tests for User Story 3

- [X] T078 [P] [US3] Add unit tests for dashboard aggregation by company, period and standard line item in app/tests/unit/test_dashboard_queries.py
- [X] T079 [P] [US3] Add integration test for dashboard using only approved values in app/tests/integration/test_dashboard_values.py
- [X] T080 [P] [US3] Add integration test for missing year gaps and single-period display in app/tests/integration/test_dashboard_gaps.py
- [X] T081 [P] [US3] Add contract tests for dashboard and audit routes in app/tests/contract/test_dashboard_contract.py

### Implementation for User Story 3

- [X] T082 [US3] Implement dashboard query service for approved standardized values in app/dashboard/services.py
- [X] T083 [US3] Implement dashboard filter form for period range, category and currency in app/dashboard/forms.py
- [X] T084 [US3] Implement company dashboard view in app/dashboard/views.py
- [X] T085 [US3] Implement dashboard URL routes in app/dashboard/urls.py
- [X] T086 [US3] Create dashboard template with year-over-year table and chart container in app/templates/dashboard/company_dashboard.html
- [X] T087 [US3] Implement Plotly chart data serializer in app/dashboard/serializers.py
- [X] T088 [US3] Add links from dashboard values to source document and review history in app/templates/dashboard/company_dashboard.html
- [X] T089 [US3] Implement audit list view for administrators in app/audit/views.py
- [X] T090 [US3] Implement audit URL routes in app/audit/urls.py
- [X] T091 [US3] Create audit list template in app/templates/audit/event_list.html
- [X] T092 [US3] Emit balance.value.approved event when review publishes a value in app/review/services.py
- [X] T093 [US3] Add Playwright E2E test for dashboard comparison flow in app/tests/e2e/test_dashboard_flow.py

**Checkpoint**: User Story 3 is complete when dashboard users can compare all approved available years for a company and trace values back to source evidence.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Harden quality, documentation, performance, security and future AI readiness.

- [X] T094 [P] Add import batch management command in app/documents/management/commands/import_balance_pdfs.py
- [X] T095 [P] Add reprocess document management command in app/extraction/management/commands/reprocess_documents.py
- [X] T096 [P] Add performance test for upload request timing in app/tests/integration/test_upload_performance.py
- [X] T097 [P] Add performance test for dashboard render query count in app/tests/integration/test_dashboard_performance.py
- [X] T098 Add indexes for document status, company periods, standard line items and approved values in app/*/migrations/
- [X] T099 Add structured logging configuration for web and worker processes in app/config/settings.py
- [X] T100 Add worker retry and failure handling for document.processing.failed events in app/extraction/tasks.py
- [X] T101 Add security settings for CSRF, secure cookies and allowed hosts in app/config/settings.py
- [X] T102 Add AI extension placeholders for AIExtractionRun, PromptTemplate and AgentTask in app/extraction/models.py
- [X] T103 Add documentation for local development commands in README.md
- [X] T104 Add quickstart validation notes for implemented commands in specs/001-balance-import-reporting/quickstart.md
- [X] T105 Run full test suite and record results in specs/001-balance-import-reporting/implementation-notes.md

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) has no dependencies.
- Foundational (Phase 2) depends on Setup completion and blocks all user stories.
- User Story 1 (Phase 3) depends on Foundational completion.
- User Story 2 (Phase 4) depends on User Story 1 document and processing-run foundation.
- User Story 3 (Phase 5) depends on User Story 2 approved standardized values.
- Polish (Phase 6) depends on the desired user stories being complete.

### User Story Dependencies

- US1 is the MVP and can be delivered first.
- US2 builds on documents and processing runs from US1.
- US3 builds on approved standardized values from US2.

### Within Each User Story

- Tests come before implementation for behavior changes.
- Models and migrations come before services.
- Services come before views and templates.
- Event/audit emission comes before E2E validation.
- Story checkpoint must pass before moving to the next priority.

## Parallel Opportunities

- T011, T012 and T013 can run in parallel after project metadata is in place.
- T018, T023 and T027 can run in parallel after foundational models/services are drafted.
- T030 through T033 can run in parallel before US1 implementation.
- T050 through T055 can run in parallel before US2 implementation.
- T078 through T081 can run in parallel before US3 implementation.
- T094 through T097 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
# Contract and integration tests can be prepared together:
Task: "T030 [P] [US1] Add contract tests for company and document upload routes in app/tests/contract/test_document_upload_contract.py"
Task: "T031 [P] [US1] Add integration test for valid PDF upload and raw file preservation in app/tests/integration/test_document_upload.py"
Task: "T032 [P] [US1] Add integration test for unsupported file rejection in app/tests/integration/test_document_upload_validation.py"
Task: "T033 [P] [US1] Add integration test for duplicate PDF checksum handling in app/tests/integration/test_duplicate_documents.py"
```

## Parallel Example: User Story 2

```bash
# Extraction, standardization and review tests touch separate files:
Task: "T050 [P] [US2] Add unit tests for native text extraction and OCR routing in app/tests/unit/test_pdf_text_extraction.py"
Task: "T052 [P] [US2] Add unit tests for standard line item mapping in app/tests/unit/test_line_item_standardization.py"
Task: "T054 [P] [US2] Add contract tests for review routes in app/tests/contract/test_review_contract.py"
```

## Parallel Example: User Story 3

```bash
# Dashboard query, display and contract coverage can start together:
Task: "T078 [P] [US3] Add unit tests for dashboard aggregation by company, period and standard line item in app/tests/unit/test_dashboard_queries.py"
Task: "T080 [P] [US3] Add integration test for missing year gaps and single-period display in app/tests/integration/test_dashboard_gaps.py"
Task: "T081 [P] [US3] Add contract tests for dashboard and audit routes in app/tests/contract/test_dashboard_contract.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for PDF upload, raw storage and queued processing.
3. Validate upload, duplicate handling and status display.
4. Stop and demo before implementing extraction quality and dashboard depth.

### Incremental Delivery

1. US1: upload and preserve PDFs.
2. US2: extract, standardize and review.
3. US3: publish approved values into dashboard comparisons.
4. Polish: performance, operations, AI extension points and docs.

### Validation Commands

```bash
docker compose exec web pytest
docker compose exec web pytest app/tests/integration
docker compose exec web pytest app/tests/contract
docker compose exec web pytest app/tests/e2e
```

## Notes

- Keep `data_example/` ignored and never use sensitive PDFs in committed tests.
- Use synthetic fixtures for automated tests in app/tests/fixtures/.
- Every published dashboard value must trace back to source document evidence.
- Any AI-generated suggestion must remain review-gated before dashboard publication.
