# Contract: Accounting Validation

This feature exposes an internal service contract and a document-analysis UI
contract. It does not add a public HTTP API in the MVP.

## Internal service

Function:

```text
validate_structured_balance(raw_extraction, *, actor_user=None) -> AccountingValidationRun
```

Preconditions:

- `raw_extraction.extraction_type` is metadata/AI structured output.
- `raw_extraction.content.llm_output` exists.
- `llm_output.metadados.tipo_documento` is a supported balance document type.

Behavior:

1. Load `llm_output`.
2. If document type is unsupported, create a `not_assessable` run.
3. For every item in `llm_output.campos_analise`:
   - when `tipo_obtencao` is `soma_contas`, compute
     `sum(contas_origem[].valor)`;
   - compare with the extracted `valor`;
   - when materially different, create a correction finding and write corrected
     value to the validated snapshot.
4. Evaluate `ativos - passivos - patrimonio_liquido = 0` using corrected
   values when available.
5. Persist run and findings.
6. Create Audit events for the run, inconsistencies, and corrections.

Postconditions:

- Original `RawExtraction.content` is not modified.
- A new validation run exists for the raw extraction.
- All automatic corrections are traceable by `rule_id`, original value,
  corrected value and inputs.

## Finding object shape

```json
{
  "rule_id": "SUM_ACCOUNTS_001",
  "field_path": "campos_analise.impostos_parcelados_diferidos_longo_prazo.valor",
  "severity": "warning",
  "outcome": "corrected",
  "message": "O valor extraído não corresponde à soma das contas de origem.",
  "original_value": "22852600.43",
  "calculated_value": "102899592.39",
  "difference": "80046991.96",
  "inputs": {
    "tipo_obtencao": "soma_contas",
    "contas_origem": [
      {"descricao": "IMPOSTOS DIFERIDOS", "valor": "1570915.57"},
      {"descricao": "PARCELAMENTO DE TRIBUTOS", "valor": "101328676.82"}
    ]
  }
}
```

## Validated output snapshot

The snapshot must keep extracted and corrected values side by side.

```json
{
  "metadados": {"tipo_documento": "balanco_patrimonial"},
  "campos_analise": {
    "campo": {
      "valor": 100.0,
      "valor_validado": 120.0,
      "corrigido": true,
      "regra_correcao": "SUM_ACCOUNTS_001"
    }
  },
  "validacao_contabil": {
    "status": "inconsistent",
    "run_id": "uuid",
    "summary": {"corrected": 1, "failed": 1, "passed": 4}
  }
}
```

## Document analysis UI

The existing AI extraction page must display:

- overall accounting validation status;
- counts by outcome/severity;
- table of corrections with field, original value, corrected value, difference
  and rule;
- list of inconsistencies;
- skipped/not-assessable checks with reason;
- link or section to related Audit entries.

Empty state:

- If no validation run exists, show that accounting validation has not run yet.

Unsupported state:

- If the document is outside the balance-document MVP, show not assessable and
  do not apply corrections.
