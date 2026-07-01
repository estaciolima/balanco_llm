# Implementation Plan: Accounting Validation

**Branch**: `002-validate-accounting` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-validate-accounting/spec.md`

## Summary

Implementar uma etapa determinística de validação contábil após a extração
estruturada via LLM. A entrada será o JSON já salvo em `RawExtraction.content`
como `llm_output`; a validação não fará nova chamada à IA. O MVP terá foco em
documentos de balanço patrimonial e em duas famílias de regra:

1. corrigir campos cujo `tipo_obtencao` seja `soma_contas`, recalculando
   `valor` pela soma dos valores em `contas_origem`;
2. avaliar a coerência básica do balanço pela identidade
   `ativos - passivos - patrimonio_liquido = 0`, respeitando tolerância de
   arredondamento configurada.

Os resultados serão persistidos, exibidos na tela de análise do documento e
registrados no Audit com valor original, valor corrigido, regra aplicada e
explicação.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.x, Django ORM, Django templates, Celery,
Redis, PostgreSQL, pytest, pytest-django. Nenhuma dependência nova é necessária.

**Storage**: PostgreSQL para modelos relacionais e `jsonb`; `RawExtraction`
continua armazenando o JSON estruturado da IA; novos registros de validação
armazenam snapshots dos achados e correções.

**Testing**: pytest, pytest-django; testes unitários para regras de validação,
testes de integração para persistência/pipeline e teste de view para a tela de
análise do documento.

**Target Platform**: Aplicação web Linux empacotada com Docker Compose,
mantendo o monolito Django já existente.

**Project Type**: Monolito web Django com processamento de extração em
background e visualização server-rendered.

**Performance Goals**: Validar um JSON estruturado com até 30 campos analisados
em menos de 3 segundos após a extração estar disponível.

**Constraints**: MVP sem nova chamada à OpenAI; sem nova stack; regras
determinísticas e auditáveis; preservar JSON original; corrigir apenas quando a
regra produzir um único valor inequívoco.

**Scale/Scope**: Documentos de balanço patrimonial já suportados pela extração
LLM, dezenas de empresas e centenas a poucos milhares de documentos no MVP.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Code quality: PASS. O plano usa apps e padrões Django já existentes
  (`extraction`, `documents`, `audit`) e adiciona um serviço puro para regras
  contábeis, sem microserviço ou abstração desnecessária.
- Testing: PASS. O plano inclui testes unitários para cada regra, integração
  com o pipeline de extração e cobertura da tela de análise/audit.
- UX consistency: PASS. A validação será exibida na tela de análise já criada
  para o JSON da IA, usando cards/tabelas/estados atuais.
- Performance: PASS. O processamento é O(n) sobre os campos do JSON, com meta
  explícita de até 3 segundos para 30 campos.

## Phase 0 Research

Ver [research.md](./research.md).

Principais decisões:

- usar serviço determinístico em Python;
- persistir uma execução de validação associada à extração avaliada;
- criar registros de achados/correções para consulta e Audit;
- executar a validação logo após a extração LLM no pipeline e permitir
  reexecução manual futura.

## Phase 1 Design

Artefatos:

- [data-model.md](./data-model.md)
- [contracts/accounting-validation.md](./contracts/accounting-validation.md)
- [quickstart.md](./quickstart.md)

## Architecture

O fluxo planejado é:

```text
RawExtraction llm_output
        |
        v
accounting.validation.validate_structured_balance()
        |
        +--> corrige campos tipo_obtencao = soma_contas
        +--> checa ativos - passivos - patrimonio_liquido = 0
        +--> gera findings/corrections
        |
        v
AccountingValidationRun + Findings + AuditEvent
        |
        v
documents/document_ai_extraction.html
```

### Rule behavior

- `SUM_ACCOUNTS_001`: para cada campo em `campos_analise` com
  `tipo_obtencao = "soma_contas"`, somar `contas_origem[].valor`.
  - Se a diferença entre a soma e o `valor` extraído exceder a tolerância,
    registrar correção e expor o valor corrigido.
  - Preservar o valor original no achado e no Audit.
  - Atualizar o payload validado/snapshot, não apagar o JSON bruto original.
- `BALANCE_EQUATION_001`: calcular `ativos - passivos - patrimonio_liquido`
  usando os campos disponíveis.
  - Ativos: preferir `total_ativo`; se ausente, usar soma compatível de
    ativo circulante, realizável longo prazo e permanente quando disponíveis.
  - Passivos: preferir `passivo_circulante + exigivel_longo_prazo`; se houver
    um campo total de passivos no schema, ele pode ser usado diretamente.
  - Patrimônio líquido: `patrimonio_liquido`.
  - Diferença dentro da tolerância passa; diferença material vira
    inconsistência de alta severidade.

## Project Structure

### Documentation (this feature)

```text
specs/002-validate-accounting/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- accounting-validation.md
`-- checklists/
    `-- requirements.md
```

### Source Code (repository root)

```text
app/
|-- accounting/
|   |-- __init__.py
|   |-- apps.py
|   |-- models.py
|   |-- services.py
|   |-- rules.py
|   `-- migrations/
|-- audit/
|   `-- services.py
|-- documents/
|   |-- views.py
|   `-- urls.py
|-- extraction/
|   |-- pipeline.py
|   `-- models.py
|-- templates/
|   `-- documents/
|       `-- document_ai_extraction.html
`-- tests/
    |-- unit/
    |   `-- test_accounting_validation_rules.py
    |-- integration/
    |   |-- test_accounting_validation_pipeline.py
    |   `-- test_ai_extraction_view.py
    `-- contract/
        `-- test_accounting_validation_contract.py
```

**Structure Decision**: Adicionar um app Django `accounting` para isolar regras
e persistência da validação contábil. A UI permanece em `documents`, a geração
do JSON permanece em `extraction`, e eventos continuam centralizados em
`audit`.

## Complexity Tracking

Nenhuma exceção constitucional prevista.
