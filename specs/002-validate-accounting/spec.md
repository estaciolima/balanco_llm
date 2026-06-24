# Feature Specification: Accounting Validation

**Feature Branch**: `002-validate-accounting`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "O JSON estruturado gerado pela LLM é a entrada da validação contábil automatizada. Para documentos do tipo balanço, as regras contábeis pré-estabelecidas verificam coerência, aplicam correções determinísticas quando cabíveis, apontam inconsistências e registram as correções no Audit do documento analisado."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review accounting consistency (Priority: P1)

After an AI extraction has produced its structured balance JSON for a balance document, the system automatically evaluates the JSON against the established accounting rules. A reviewer opens the document analysis and sees whether the numbers are accounting-consistent, each identified issue, its severity, the values involved, and a plain-language explanation of the applied rule.

**Why this priority**: A structured JSON is not reliable enough for financial analysis until basic accounting relationships have been checked. This story makes suspicious results visible before they are used for decisions.

**Independent Test**: Process one balanced extraction and one extraction with intentionally inconsistent totals; verify that the first is marked consistent and the second lists the failed checks with the relevant values.

**Acceptance Scenarios**:

1. **Given** a structured JSON from a balance document with matching asset and liability-side totals, **When** automated validation finishes, **Then** the reviewer sees a consistent status and the successful checks.
2. **Given** a structured JSON where total assets differ from the reported liability-side total, **When** automated validation finishes, **Then** the reviewer sees a high-severity inconsistency containing both values and their difference.
3. **Given** a structured JSON with missing fields required for a selected check, **When** automated validation finishes, **Then** the check is reported as not assessable rather than as a false inconsistency.

---

### User Story 2 - Apply traceable accounting corrections (Priority: P2)

A reviewer can see corrections automatically applied when a pre-established accounting rule can determine an unambiguous corrected value, such as a recalculated liquidity ratio. The reviewer can compare the extracted value with the corrected value and see the rule and inputs that justified the correction.

**Why this priority**: Correcting deterministic calculations makes the financial analysis more useful while preserving the original extraction for review and traceability.

**Independent Test**: Supply a balance JSON whose declared liquidity ratio differs from the value derived from its available components; verify that the corrected result is available and names the rule and inputs used.

**Acceptance Scenarios**:

1. **Given** a balance JSON with all components for a liquidity ratio and a matching declared ratio, **When** validation runs, **Then** the ratio check succeeds and no correction is applied.
2. **Given** a balance JSON with all components for a liquidity ratio but a materially different declared ratio, **When** validation runs, **Then** the result identifies the inconsistency, applies the recalculated value as a correction, and reports the extracted and corrected values.

---

### User Story 3 - Audit corrections and inconsistencies (Priority: P3)

A reviewer can open the Audit history for a document and see every validation run, inconsistency, and automatic correction, including the original value, corrected value, rule, reason, and time of the action.

**Why this priority**: Financial corrections must be explainable and attributable; the audit history lets reviewers reconstruct how the validated analysis was produced.

**Independent Test**: Process a balance JSON that requires a deterministic correction and verify that the document Audit page records the correction and its supporting rule.

**Acceptance Scenarios**:

1. **Given** a balance JSON with a deterministic correction, **When** validation completes, **Then** the document Audit page contains an event with the extracted value, corrected value, rule identifier, and explanation.
2. **Given** a balance JSON with an inconsistency that cannot be corrected unambiguously, **When** validation completes, **Then** the document Audit page records the inconsistency without changing the extracted value.

### Edge Cases

- A balance may legitimately omit optional accounts such as inventories; related checks must be marked not assessable unless the absence itself contradicts a stated total.
- Values may be reported in units, thousands, or millions; checks must compare values only within the same declared scale.
- Rounding differences must not create an inconsistency when they fall within the documented tolerance.
- The MVP accepts balance documents only; a document classified as another type must not receive balance validation or automatic corrections and must clearly state that it is outside the MVP scope.
- The latest extraction for a document may be replaced by a reprocessing run; its validation result must remain clearly associated with the extraction it evaluated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST use each successful structured JSON extraction for a balance document as the input to an automatic accounting-validation run and retain the outcome with that extraction.
- **FR-002**: The system MUST classify the overall outcome as consistent, warning, inconsistent, or not assessable.
- **FR-003**: The system MUST verify whether reported total assets, reported liability-side totals, and the declared balance total agree within a documented rounding tolerance when the relevant values are available.
- **FR-004**: The system MUST verify that a stated subtotal is not contradicted by its available component accounts and flag material differences.
- **FR-005**: The system MUST recalculate declared liquidity current, quick, and general ratios whenever all required components are available and compare them with the extracted values.
- **FR-006**: The system MUST identify impossible or suspicious relationships, including negative values where the extracted account category does not permit them, component values exceeding their stated subtotal, and incompatible document period, currency, or value scale information.
- **FR-007**: The system MUST apply a correction only when a pre-established accounting rule produces one unambiguous corrected value from available JSON inputs.
- **FR-008**: The system MUST preserve the extracted value alongside any corrected value and MUST associate the correction with the rule, inputs, and explanation that produced it.
- **FR-009**: Every validation finding MUST include a stable rule identifier, severity, plain-language explanation, the fields and values used, and whether the check was passed, failed, corrected, or not assessable.
- **FR-010**: The document analysis page MUST display the overall validation status, counts by severity, the complete list of findings, and any extracted-versus-corrected values alongside the existing structured analysis.
- **FR-011**: The system MUST create a document Audit entry for every validation run, inconsistency, and automatic correction; correction entries MUST include the original value, corrected value, rule identifier, and explanation.
- **FR-012**: The system MUST preserve prior validation outcomes and Audit entries for prior extraction runs so reviewers can distinguish current results from reprocessed results.
- **FR-013**: The system MUST not apply a correction when required inputs are missing, the rule is ambiguous, the document is outside the balance-document MVP scope, or the result would require an accounting judgement.
- **FR-014**: The system MUST allow reviewers to see why a check was skipped, including missing inputs, an unsupported document type, incompatible units, or an ambiguous rule result.

### Non-Functional Requirements

- **NFR-001**: Validation states, severity labels, empty states, and findings MUST follow the existing document-analysis visual patterns and be understandable without accounting-system internals.
- **NFR-002**: For a structured extraction containing up to 30 analysed fields, validation results MUST be available within 3 seconds after the extraction result is available, excluding the AI extraction time.
- **NFR-003**: Automated coverage MUST include balanced, inconsistent, rounded, missing-data, unsupported-document, and recalculated-ratio scenarios, plus the document-analysis display of results.
- **NFR-004**: Validation rules and their tolerances MUST be traceable and consistently applied to the same extraction input.

### Key Entities *(include if feature involves data)*

- **Accounting Validation Run**: The automatic validation outcome for one structured balance JSON, including status, execution time, applied tolerance, and summary counts.
- **Accounting Validation Finding**: One rule evaluation with its severity, outcome, explanation, evidence fields, compared values, rule identifier, and any corrected value.
- **Accounting Correction**: A traceable change from an extracted value to an unambiguous rule-derived value, retaining the source inputs and reason.
- **Validation Rule**: A named accounting-consistency check, such as balance equality, subtotal reconciliation, or liquidity-ratio recalculation.
- **Structured Extraction**: The existing AI-generated balance analysis JSON that provides the values, metadata, formulas, and evidence to validate.
- **Document Audit Entry**: The document-level historical record of validation runs, detected inconsistencies, and applied corrections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reviewers can determine whether a processed balance is consistent and identify its highest-severity finding within 30 seconds of opening the document analysis.
- **SC-002**: All test extractions with deliberately mismatched asset and liability-side totals are flagged as inconsistent.
- **SC-003**: All test extractions with matching totals within the configured rounding tolerance are not falsely flagged for a balance-total inconsistency.
- **SC-004**: All test balance JSONs with materially incorrect declared liquidity ratios are flagged with the affected ratio and the rule-derived corrected value.
- **SC-005**: At least 95% of validations for supported structured balance analyses complete within 3 seconds after extraction data is available.
- **SC-006**: Reviewers can distinguish passed, failed, corrected, and not-assessable checks without opening the raw JSON.
- **SC-007**: All automatic corrections in test balance JSONs have a corresponding document Audit entry containing the original value, corrected value, rule identifier, and explanation.

## Assumptions

- The existing structured extraction JSON remains the source of values for this feature; the validation stage does not call an AI model.
- The MVP scope is limited to documents classified as balance documents and to balance-sheet checks plus the three liquidity ratios already present in the structured analysis.
- A small, configurable rounding tolerance is appropriate for initially reported monetary totals and ratios.
- Pre-established rules may automatically correct only deterministic values; any accounting judgement remains an inconsistency for reviewer analysis.
- The original extracted JSON is preserved; corrections produce a traceable validated result and do not erase the original extraction.
- Existing authenticated reviewers can access validation outcomes for documents they can already view.
