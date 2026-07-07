# Data Model: Accounting Validation

## AccountingValidationRun

Represents one deterministic accounting validation for one structured AI
extraction.

Fields:

- `id`: UUID primary key.
- `document`: foreign key to `BalanceDocument`.
- `raw_extraction`: foreign key to the `RawExtraction` containing
  `llm_output`.
- `ai_extraction_run`: nullable foreign key to `AIExtractionRun` when available.
- `status`: `consistent`, `warning`, `inconsistent`, or `not_assessable`.
- `tolerance_amount`: decimal absolute tolerance used for monetary checks.
- `tolerance_ratio`: decimal tolerance used for ratio checks.
- `summary`: JSON with counts by severity/outcome.
- `validated_output`: JSON snapshot containing corrected values and metadata.
- `created_at`: timestamp.
- `duration_ms`: validation runtime.

Relationships:

- Has many `AccountingValidationFinding`.
- Has many corrections through findings with outcome `corrected`.
- Has corresponding `AuditEvent` entries.

Validation rules:

- A run belongs to exactly one raw extraction.
- Reprocessing creates a new run; it does not mutate prior runs.
- `validated_output` preserves enough information to render extracted vs.
  corrected values.

## AccountingValidationFinding

Represents one accounting rule evaluation.

Fields:

- `id`: UUID primary key.
- `validation_run`: foreign key to `AccountingValidationRun`.
- `rule_id`: stable identifier such as `SUM_ACCOUNTS_001`.
- `field_path`: JSON path or logical path, e.g.
  `campos_analise.total_ativo.valor`.
- `severity`: `info`, `warning`, or `high`.
- `outcome`: `passed`, `failed`, `corrected`, or `not_assessable`.
- `message`: plain-language explanation.
- `original_value`: decimal value when applicable.
- `calculated_value`: decimal value computed by the rule when applicable.
- `difference`: decimal difference when applicable.
- `inputs`: JSON with account values, field names, and formula components.
- `created_at`: timestamp.

Validation rules:

- Every finding has a stable `rule_id`.
- Corrections must include `original_value`, `calculated_value`, `difference`,
  and `inputs`.
- Skipped checks must explain missing inputs or unsupported scope.

## Validation Rule

Rules are implemented in code, not stored as user-editable records for the MVP.

Initial rules:

- `SUM_ACCOUNTS_001`: for each field where
  `tipo_obtencao = "soma_contas"`, recalculate `valor` from
  `contas_origem[].valor`.
- `BALANCE_EQUATION_001`: verify
  `ativos - passivos - patrimonio_liquido = 0`.
- `LIQUIDITY_RATIO_001`: optional follow-on rule for liquidity current, quick,
  and general ratios from existing structured values.

## Structured Extraction

Existing input stored in `RawExtraction.content`.

Relevant structure:

```json
{
  "llm_output": {
    "metadados": {
      "tipo_documento": "balanco_patrimonial",
      "moeda": "BRL",
      "escala_valores": "milhoes"
    },
    "campos_analise": {
      "campo": {
        "valor": 100.0,
        "tipo_obtencao": "soma_contas",
        "contas_origem": [
          {"descricao": "Conta A", "valor": 40.0},
          {"descricao": "Conta B", "valor": 60.0}
        ]
      }
    }
  }
}
```

## Document Audit Entry

Existing `AuditEvent` records validation milestones and corrections.

Required event types:

- `accounting.validation.started`
- `accounting.validation.completed`
- `accounting.validation.inconsistency_detected`
- `accounting.validation.correction_applied`

Correction event payload:

- `validation_run_id`
- `raw_extraction_id`
- `rule_id`
- `field_path`
- `original_value`
- `corrected_value`
- `difference`
- `explanation`
- `inputs`

## State transitions

```text
RawExtraction created
  -> AccountingValidationRun running
  -> consistent | warning | inconsistent | not_assessable
```

Outcomes:

- `consistent`: all assessable material checks passed.
- `warning`: no high-severity failure, but at least one warning or skipped
  check matters for review.
- `inconsistent`: at least one high-severity failed check.
- `not_assessable`: unsupported document type or insufficient required data for
  core checks.
