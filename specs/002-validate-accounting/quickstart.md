# Quickstart: Accounting Validation

## Prerequisites

- Existing Django environment configured.
- Database migrated.
- At least one document with successful AI structured extraction saved in
  `RawExtraction.content.llm_output`.

## Run checks locally

```powershell
.\.venv\Scripts\python.exe -m pytest app\tests\unit\test_accounting_validation_rules.py
.\.venv\Scripts\python.exe -m pytest app\tests\integration\test_accounting_validation_pipeline.py
.\.venv\Scripts\python.exe -m pytest app\tests\integration\test_ai_extraction_view.py
.\.venv\Scripts\python.exe -m pytest app\tests\unit\test_accounting_validation_audit.py
.\.venv\Scripts\python.exe -m pytest app\tests\integration\test_audit_accounting_validation.py
.\.venv\Scripts\python.exe -m pytest app\tests\integration\test_accounting_validation_performance.py
.\.venv\Scripts\python.exe app\manage.py check
```

## Manual validation scenario

1. Start Django:

   ```powershell
   .\.venv\Scripts\python.exe app\manage.py runserver
   ```

2. Process or open a document that has AI structured output.

3. Open the AI extraction/analysis page for the document.

4. Confirm the page displays a section for accounting validation.

Expected outcomes:

- Fields with `tipo_obtencao = "soma_contas"` show the corrected value when
  `valor` differs from the sum of `contas_origem`.
- The original extracted value remains visible.
- The Audit page has entries for validation completion and each correction.
- If `ativos - passivos - patrimonio_liquido` differs materially from zero, the
  page shows a high-severity inconsistency.

## Test fixture examples

### Incorrect sum

Input:

```json
{
  "campos_analise": {
    "exemplo": {
      "valor": 90,
      "tipo_obtencao": "soma_contas",
      "contas_origem": [
        {"descricao": "A", "valor": 40},
        {"descricao": "B", "valor": 60}
      ]
    }
  }
}
```

Expected:

- original value: `90`
- corrected value: `100`
- outcome: `corrected`
- rule: `SUM_ACCOUNTS_001`

### Balanced accounting equation

Input values:

```text
ativos = 1.000
passivos = 700
patrimonio_liquido = 300
```

Expected:

- `ativos - passivos - patrimonio_liquido = 0`
- outcome: `passed`

### Inconsistent accounting equation

Input values:

```text
ativos = 1.000
passivos = 650
patrimonio_liquido = 300
```

Expected:

- difference: `50`
- outcome: `failed`
- severity: `high`
