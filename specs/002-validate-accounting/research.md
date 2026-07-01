# Research: Accounting Validation

## Decision: Use deterministic Python rules instead of another LLM call

**Rationale**: A necessidade principal é corrigir somas incorretas em campos
marcados como `tipo_obtencao = "soma_contas"` e verificar a identidade contábil
do balanço. Essas regras são aritméticas, previsíveis e precisam ser
auditáveis. Usar IA novamente aumentaria custo e variabilidade sem melhorar a
confiabilidade dessas checagens.

**Alternatives considered**:

- Nova chamada à OpenAI para reconciliar os números: rejeitada por custo,
  latência e menor determinismo.
- Correção manual apenas na tela: rejeitada porque a inconsistência pode ser
  detectada e corrigida automaticamente quando a regra é inequívoca.

## Decision: Store validation runs separately from the original extraction

**Rationale**: O JSON original da IA deve permanecer intacto. A validação gera
um resultado derivado: status, achados, correções e um snapshot validado. Isso
permite comparar a extração bruta com o resultado corrigido e preservar
histórico quando o documento for reprocessado.

**Alternatives considered**:

- Sobrescrever `RawExtraction.content`: rejeitada por perder rastreabilidade.
- Guardar apenas AuditEvent: rejeitada porque a tela precisará consultar
  status, contadores e achados estruturados de forma eficiente.

## Decision: Add a small accounting Django app

**Rationale**: A validação contábil é um domínio próprio. Um app `accounting`
com `rules.py`, `services.py` e modelos de persistência mantém a regra fora da
view e fora do pipeline de extração, mas ainda dentro da stack Django atual.

**Alternatives considered**:

- Colocar tudo em `extraction`: rejeitada porque mistura extração LLM com
  validação contábil pós-processamento.
- Colocar tudo em `documents`: rejeitada porque a view não deve conter regra de
  negócio.

## Decision: Use configurable decimal tolerances

**Rationale**: Balanços podem ter arredondamento por centavos, milhares ou
milhões. A tolerância precisa ser configurável para evitar falso positivo, mas
deve ter um padrão simples para o MVP.

**Alternatives considered**:

- Tolerância zero: rejeitada por fragilidade com arredondamento.
- Tolerância percentual apenas: rejeitada porque pequenas diferenças absolutas
  em valores altos e baixos se comportam de forma diferente.

## Decision: Run validation after successful AI extraction

**Rationale**: A validação depende do JSON estruturado. Executá-la no pipeline
logo após salvar `RawExtraction` garante que a página de análise já abra com
status, correções e inconsistências.

**Alternatives considered**:

- Validar sob demanda ao abrir a página: rejeitada porque mistura latência de
  cálculo com renderização e pode gerar resultados inconsistentes entre
  usuários.
- Validar em job separado obrigatório: adiado; o cálculo é leve o suficiente
  para rodar dentro do fluxo atual após a extração.
