# Tasks: Accounting Validation

**Input**: Design documents from `/specs/002-validate-accounting/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/accounting-validation.md](./contracts/accounting-validation.md), [quickstart.md](./quickstart.md)

**Tests**: Required. This feature changes validation behavior, persistence, pipeline integration, Audit records, and the document-analysis UI.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and demonstrated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and does not depend on an incomplete task.
- **[Story]**: User story label, only for story phases.
- Every task includes an exact file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Django app shell and make the project aware of the accounting-validation feature.

- [X] T001 Create the accounting Django app package files in app/accounting/__init__.py and app/accounting/apps.py
- [X] T002 Register the accounting app in app/config/settings.py
- [X] T003 [P] Add accounting-validation tolerance examples to .env.example
- [X] T004 [P] Create empty migration package in app/accounting/migrations/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the shared persistence, settings, and service boundaries needed by all user stories.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T005 Add ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE and ACCOUNTING_VALIDATION_RATIO_TOLERANCE decimal settings in app/config/settings.py
- [X] T006 Define AccountingValidationRun and AccountingValidationFinding models in app/accounting/models.py
- [X] T007 Create initial accounting migrations for validation models in app/accounting/migrations/0001_initial.py
- [X] T008 [P] Register AccountingValidationRun and AccountingValidationFinding in app/accounting/admin.py
- [X] T009 [P] Define rule IDs, enums, and Decimal helpers in app/accounting/rules.py
- [X] T010 [P] Create service module skeleton with validate_structured_balance(raw_extraction, *, actor_user=None) in app/accounting/services.py
- [X] T011 [P] Add model smoke tests for validation run and finding relationships in app/tests/unit/test_accounting_validation_models.py

**Checkpoint**: Foundation ready. Models, settings, and service entry point exist.

---

## Phase 3: User Story 1 - Review accounting consistency (Priority: P1) MVP

**Goal**: Automatically validate a structured balance JSON, classify the result, and show balance-equation findings on the document analysis page.

**Independent Test**: Process one balanced extraction and one extraction with intentionally inconsistent totals; confirm the first is consistent and the second displays a high-severity finding with the compared values and difference.

### Tests for User Story 1

- [X] T012 [P] [US1] Add unit tests for BALANCE_EQUATION_001 passed, failed, rounded, missing-data, and unsupported-document cases in app/tests/unit/test_accounting_validation_rules.py
- [X] T013 [P] [US1] Add contract tests for validate_structured_balance output shape and RawExtraction immutability in app/tests/contract/test_accounting_validation_contract.py
- [X] T014 [P] [US1] Add integration tests for persisted validation runs and findings from structured JSON in app/tests/integration/test_accounting_validation_pipeline.py
- [X] T015 [P] [US1] Add document-analysis UI tests for validation status, counts, findings, and empty state in app/tests/integration/test_ai_extraction_view.py

### Implementation for User Story 1

- [X] T016 [US1] Implement supported document detection and llm_output extraction in app/accounting/services.py
- [X] T017 [US1] Implement field-value lookup using validated/corrected values when available in app/accounting/rules.py
- [X] T018 [US1] Implement BALANCE_EQUATION_001 calculation for ativos - passivos - patrimonio_liquido in app/accounting/rules.py
- [X] T019 [US1] Persist validation run status, summary counts, validated_output snapshot, and findings in app/accounting/services.py
- [X] T020 [US1] Integrate accounting validation immediately after successful OpenAI RawExtraction creation in app/extraction/pipeline.py
- [X] T021 [US1] Add latest validation run and findings to document_ai_extraction context in app/documents/views.py
- [X] T022 [US1] Render accounting validation status, counts, findings, skipped checks, and empty state in app/templates/documents/document_ai_extraction.html
- [X] T023 [US1] Add validation-status and finding-table styles matching existing analysis page patterns in app/static/css/app.css
- [X] T024 [US1] Record a pipeline event payload for accounting validation completion in app/extraction/pipeline.py

**Checkpoint**: User Story 1 is complete when the page shows consistent, inconsistent, and not-assessable validation outcomes without opening the raw JSON.

---

## Phase 4: User Story 2 - Apply traceable accounting corrections (Priority: P2)

**Goal**: Correct fields where `tipo_obtencao = "soma_contas"` by summing `contas_origem[].valor`, preserve original values, and show extracted-versus-corrected values.

**Independent Test**: Supply a JSON where a `soma_contas` field has `valor = 90` and `contas_origem` sums to `100`; confirm the validation result stores original `90`, corrected `100`, rule `SUM_ACCOUNTS_001`, and uses the corrected value in later checks.

### Tests for User Story 2

- [X] T025 [P] [US2] Add unit tests for SUM_ACCOUNTS_001 corrected, passed, missing-contas-origem, non-numeric-value, and tolerance cases in app/tests/unit/test_accounting_validation_rules.py
- [X] T026 [P] [US2] Add integration tests confirming corrected values are saved in validated_output and original RawExtraction remains unchanged in app/tests/integration/test_accounting_validation_pipeline.py
- [X] T027 [P] [US2] Add UI tests for extracted-versus-corrected correction table in app/tests/integration/test_ai_extraction_view.py

### Implementation for User Story 2

- [X] T028 [US2] Implement SUM_ACCOUNTS_001 traversal over campos_analise fields in app/accounting/rules.py
- [X] T029 [US2] Implement correction metadata fields valor_validado, corrigido, regra_correcao, valor_original, and diferenca_validacao in validated_output in app/accounting/services.py
- [X] T030 [US2] Ensure BALANCE_EQUATION_001 uses corrected values from SUM_ACCOUNTS_001 when available in app/accounting/rules.py
- [X] T031 [US2] Add correction table context builder for document analysis in app/documents/views.py
- [X] T032 [US2] Render corrections with field, original value, corrected value, difference, rule, and explanation in app/templates/documents/document_ai_extraction.html
- [X] T033 [US2] Add corrected-value visual treatment to the financial summary table in app/templates/documents/document_ai_extraction.html

**Checkpoint**: User Story 2 is complete when automatic sum corrections are visible, traceable, and do not overwrite the original JSON.

---

## Phase 5: User Story 3 - Audit corrections and inconsistencies (Priority: P3)

**Goal**: Record every validation run, inconsistency, and automatic correction in the document Audit history.

**Independent Test**: Process a structured balance JSON requiring one correction and one uncorrectable inconsistency; confirm the document Audit page lists validation completion, correction-applied, and inconsistency-detected events with rule IDs and values.

### Tests for User Story 3

- [X] T034 [P] [US3] Add audit event tests for validation completed, inconsistency detected, and correction applied payloads in app/tests/unit/test_accounting_validation_audit.py
- [X] T035 [P] [US3] Add integration tests confirming validation audit events are created from pipeline execution in app/tests/integration/test_accounting_validation_pipeline.py
- [X] T036 [P] [US3] Add Audit page display tests for accounting validation event payloads in app/tests/integration/test_audit_accounting_validation.py

### Implementation for User Story 3

- [X] T037 [US3] Emit accounting.validation.started and accounting.validation.completed AuditEvent records in app/accounting/services.py
- [X] T038 [US3] Emit accounting.validation.inconsistency_detected AuditEvent records for failed high-severity findings in app/accounting/services.py
- [X] T039 [US3] Emit accounting.validation.correction_applied AuditEvent records with original value, corrected value, rule identifier, explanation, and inputs in app/accounting/services.py
- [X] T040 [US3] Add document filtering or linking support for validation Audit events in app/audit/views.py
- [X] T041 [US3] Render accounting validation Audit event payloads clearly in app/templates/audit/audit_event_list.html
- [X] T042 [US3] Add a link from the document analysis validation section to related Audit history in app/templates/documents/document_ai_extraction.html

**Checkpoint**: User Story 3 is complete when a reviewer can reconstruct every validation correction and inconsistency from Audit records.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate quality, performance, and developer handoff across the whole feature.

- [X] T043 [P] Add or update quickstart validation notes for implemented commands in specs/002-validate-accounting/quickstart.md
- [X] T044 [P] Add performance test for validating up to 30 analysed fields under 3 seconds in app/tests/integration/test_accounting_validation_performance.py
- [X] T045 [P] Run ruff over changed accounting, extraction, documents, audit, and tests files via pyproject.toml
- [X] T046 Run focused pytest suite for app/tests/unit/test_accounting_validation_rules.py, app/tests/integration/test_accounting_validation_pipeline.py, app/tests/integration/test_ai_extraction_view.py, app/tests/unit/test_accounting_validation_audit.py, and app/tests/integration/test_audit_accounting_validation.py
- [X] T047 Run Django system check for the updated INSTALLED_APPS, models, templates, and settings via app/manage.py
- [X] T048 Review document-analysis labels, empty states, severity colors, and table accessibility in app/templates/documents/document_ai_extraction.html

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **US1 (Phase 3)**: Depends on Phase 2; this is the MVP.
- **US2 (Phase 4)**: Depends on Phase 2 and can be implemented after or alongside US1, but its page rendering is clearer after US1 context exists.
- **US3 (Phase 5)**: Depends on Phase 2 and benefits from US1/US2 findings, but Audit emission can be developed independently against service outputs.
- **Polish (Phase 6)**: Depends on all intended stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Independent after foundational tasks; no dependency on US2 or US3.
- **User Story 2 (P2)**: Independent rule behavior after foundational tasks; UI integration depends on the document-analysis context pattern introduced by US1.
- **User Story 3 (P3)**: Independent Audit behavior after foundational tasks; highest value after US1/US2 generate findings/corrections.

### Within Each User Story

- Write tests before implementation and confirm they fail.
- Implement rules before services.
- Persist model state before rendering it in views/templates.
- Integrate pipeline after service behavior is covered.
- Complete each story checkpoint before moving to the next priority.

---

## Parallel Opportunities

- T003 and T004 can run in parallel with T001/T002.
- T008, T009, T010, and T011 can run in parallel after T006 is drafted.
- T012, T013, T014, and T015 can run in parallel for US1 test coverage.
- T025, T026, and T027 can run in parallel for US2 test coverage.
- T034, T035, and T036 can run in parallel for US3 test coverage.
- Polish tasks T043, T044, and T048 can run in parallel after stories are implemented.

## Parallel Example: User Story 1

```text
Task: "Add unit tests for BALANCE_EQUATION_001 passed, failed, rounded, missing-data, and unsupported-document cases in app/tests/unit/test_accounting_validation_rules.py"
Task: "Add contract tests for validate_structured_balance output shape and RawExtraction immutability in app/tests/contract/test_accounting_validation_contract.py"
Task: "Add integration tests for persisted validation runs and findings from structured JSON in app/tests/integration/test_accounting_validation_pipeline.py"
Task: "Add document-analysis UI tests for validation status, counts, findings, and empty state in app/tests/integration/test_ai_extraction_view.py"
```

## Parallel Example: User Story 2

```text
Task: "Add unit tests for SUM_ACCOUNTS_001 corrected, passed, missing-contas-origem, non-numeric-value, and tolerance cases in app/tests/unit/test_accounting_validation_rules.py"
Task: "Add integration tests confirming corrected values are saved in validated_output and original RawExtraction remains unchanged in app/tests/integration/test_accounting_validation_pipeline.py"
Task: "Add UI tests for extracted-versus-corrected correction table in app/tests/integration/test_ai_extraction_view.py"
```

## Parallel Example: User Story 3

```text
Task: "Add audit event tests for validation completed, inconsistency detected, and correction applied payloads in app/tests/unit/test_accounting_validation_audit.py"
Task: "Add integration tests confirming validation audit events are created from pipeline execution in app/tests/integration/test_accounting_validation_pipeline.py"
Task: "Add Audit page display tests for accounting validation event payloads in app/tests/integration/test_audit_accounting_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational models/settings/services.
3. Complete Phase 3: User Story 1 balance-equation validation and display.
4. Stop and validate with focused unit/integration/view tests.
5. Demo a balanced, inconsistent, and not-assessable document.

### Incremental Delivery

1. Foundation ready.
2. US1: reviewers can see accounting consistency.
3. US2: incorrect `soma_contas` values are corrected and visible.
4. US3: corrections and inconsistencies become reconstructable from Audit.
5. Polish: performance, UX labels, quickstart, ruff, pytest, Django check.

### Notes

- Preserve `RawExtraction.content` exactly as produced by the LLM.
- Store corrections only in validation models and `validated_output`.
- Do not call OpenAI or any other AI service during validation.
- Prefer Decimal for all monetary and ratio calculations.
- Keep the first implementation boring and explicit: rules in code, no user-editable rule engine.
