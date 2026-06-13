# Implementation Plan: Balance Import Reporting

**Branch**: `001-balance-import-reporting` | **Date**: 2026-06-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-balance-import-reporting/spec.md`

## Summary

Construir uma aplicacao web para receber PDFs de balancos empresariais,
preservar os arquivos originais, extrair informacoes financeiras, padronizar os
dados processados e apresentar comparacoes por empresa e por ano em um
dashboard. A arquitetura prioriza simplicidade para um unico desenvolvedor:
monolito Django, PostgreSQL como banco principal, armazenamento de arquivos
separado, jobs assíncronos para processamento de PDFs e frontend server-rendered
com componentes interativos apenas onde agregarem valor.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.x, Django ORM, Django Admin, Celery, Redis,
PyMuPDF, pdfplumber, OCRmyPDF/Tesseract, Pandas, Pydantic, Plotly.js, HTMX,
Tailwind CSS

**Storage**: PostgreSQL 16+ para dados relacionais e `jsonb`; filesystem local
em desenvolvimento para PDFs; armazenamento S3-compativel em producao

**Testing**: pytest, pytest-django, factory_boy, Playwright para fluxos web
criticos

**Target Platform**: Aplicacao web Linux, empacotada com Docker Compose

**Project Type**: Monolito web com processamento assíncrono em background

**Performance Goals**: Upload aceito em ate 5 segundos para PDFs de ate 25 MB;
dashboard de uma empresa renderizado em ate 2 segundos para ate 10 anos de
dados; processamento de um PDF tipico concluido em ate 5 minutos no MVP

**Constraints**: Manter baixo custo operacional; evitar microservicos no MVP;
preservar rastreabilidade entre dado processado e PDF original; permitir revisao
humana antes do uso analitico dos dados

**Scale/Scope**: MVP para dezenas de empresas, centenas a poucos milhares de
documentos, um a poucos usuarios internos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Code quality: PASS. O desenho usa um monolito modular e bibliotecas maduras,
  evitando uma separacao prematura entre backend, frontend e workers em
  servicos independentes.
- Testing: PASS. O plano inclui testes unitarios para normalizacao, testes de
  integracao do pipeline, testes de contrato para endpoints e testes E2E para
  upload, revisao e dashboard.
- UX consistency: PASS. A interface sera server-rendered com padroes
  consistentes para lista, detalhe, revisao, estados de processamento e
  dashboard.
- Performance: PASS. O plano define metas de upload, processamento e dashboard,
  com tarefas pesadas fora do request web.

## Arquitetura Geral

O sistema sera dividido em modulos dentro de um unico projeto Django:

- `documents`: upload, validacao, checksum, armazenamento bruto e status de
  processamento.
- `extraction`: leitura de texto/tabelas, OCR, parsing inicial e rastreabilidade
  por pagina/linha.
- `standardization`: mapeamento de campos extraidos para um catalogo comum de
  linhas financeiras.
- `review`: fila de revisao humana, edicoes, aprovacao e trilha de auditoria.
- `companies`: cadastro de empresas, aliases e periodos reportados.
- `dashboard`: consultas agregadas e visualizacoes comparativas.
- `accounts`: usuarios, permissoes e auditoria.

Fluxo principal:

1. Usuario envia PDF.
2. Aplicacao calcula checksum, salva metadados e preserva o arquivo bruto.
3. Job assíncrono detecta texto nativo; se necessario, executa OCR.
4. Pipeline extrai candidatos de campos e tabelas.
5. Normalizador mapeia candidatos para linhas financeiras padronizadas.
6. Registro entra em revisao humana quando houver baixa confianca, conflitos ou
   dados faltantes.
7. Dados aprovados alimentam o dashboard por empresa e ano.

## Backend

Escolha: Django 5.x como monolito web.

Justificativa:

- Entrega rapida com ORM, autenticacao, migracoes, forms, templates e Admin no
  mesmo framework.
- Menos cola entre ferramentas do que uma combinacao FastAPI + SPA + painel
  administrativo separado.
- Django Admin acelera o backoffice inicial para empresas, documentos,
  revisoes e auditoria.
- Facil evoluir para endpoints JSON sem abandonar o monolito.

Estrutura recomendada:

- Views server-rendered para fluxos humanos.
- Services puros em Python para extracao, normalizacao e validacao.
- Models Django para persistencia e regras de integridade.
- Tasks Celery para processamento demorado.
- Management commands para reprocessamento em lote e manutencao.

## Frontend

Escolha: Django templates + HTMX + Tailwind CSS + Plotly.js.

Justificativa:

- Evita uma SPA completa no MVP.
- Mantem UX suficientemente rica para upload, filtros, revisao e dashboard.
- HTMX cobre interacoes pontuais sem criar uma aplicacao frontend separada.
- Plotly.js entrega graficos interativos adequados para series historicas e
  comparacoes financeiras.

Telas principais:

- Login.
- Lista de empresas.
- Detalhe da empresa com documentos, periodos e status.
- Upload de PDF.
- Tela de revisao com PDF original ao lado dos dados extraidos.
- Dashboard com comparacao ano a ano por linha financeira.
- Auditoria de alteracoes e processamento.

## Banco de Dados

Escolha: PostgreSQL.

Modelo de armazenamento:

- Tabelas relacionais para empresas, documentos, periodos, registros
  padronizados, revisoes e auditoria.
- `jsonb` para payloads de extracao bruta, metadados variaveis e snapshots de
  pipeline.
- Indices relacionais para consultas frequentes por empresa, periodo, status e
  linha financeira.
- Indices GIN em `jsonb` apenas quando houver consulta real sobre payloads
  semi-estruturados.

Arquivos PDF:

- Desenvolvimento: pasta local versionada fora do Git, configurada via ambiente.
- Producao: bucket S3-compativel.
- Banco guarda URI, hash, tamanho, content type e metadados, nao o binario do
  PDF.

## OCR e Processamento de PDFs

Escolha inicial:

- PyMuPDF para extrair texto e metadados de PDFs digitais.
- pdfplumber para extracao de tabelas e layout tabular quando o PDF tiver texto
  pesquisavel.
- OCRmyPDF + Tesseract como fallback para documentos escaneados.
- Pandas apenas para transformacoes tabulares internas, nao como camada de
  persistencia.

Estrategia:

- Detectar se o PDF tem texto pesquisavel antes de OCR.
- Executar OCR somente quando necessario.
- Guardar evidencias: pagina, texto bruto, coordenadas quando disponiveis,
  metodo de extracao e nivel de confianca.
- Tratar extracao como pipeline reexecutavel e versionado.

## Pipeline de Extracao

Estagios:

1. `ingest`: valida PDF, calcula hash, cria documento.
2. `classify`: detecta tipo de documento, idioma provavel e se ha texto nativo.
3. `extract_text`: extrai texto nativo ou aplica OCR.
4. `extract_tables`: identifica tabelas e candidatos de linhas financeiras.
5. `parse_candidates`: transforma blocos em campos candidatos.
6. `standardize`: mapeia candidatos para catalogo padrao.
7. `validate`: checa periodo, moeda, totais, duplicidade e consistencia.
8. `review_route`: aprova automaticamente itens confiaveis ou envia para
   revisao.
9. `publish`: disponibiliza dados aprovados ao dashboard.

Cada execucao do pipeline registra versao, status, duracao, erro, parametros e
artefatos gerados. Isso prepara a arquitetura para reprocessar documentos
quando regras ou modelos melhorarem.

## Modelo de Dados

Entidades centrais:

- `Company`: empresa analisada.
- `CompanyAlias`: nomes alternativos detectados nos documentos.
- `BalanceDocument`: PDF bruto, hash, status e metadados.
- `ProcessingRun`: execucao versionada do pipeline.
- `RawExtraction`: texto, tabelas e evidencias extraidas.
- `ReportingPeriod`: ano ou intervalo do balanco.
- `StandardLineItem`: catalogo padrao de linhas financeiras comparaveis.
- `ExtractedLineItem`: item extraido antes da aprovacao.
- `StandardizedBalanceValue`: valor aprovado para empresa, periodo e linha.
- `ReviewTask`: item pendente de revisao humana.
- `AuditEvent`: trilha de alteracao, processamento e acesso.

O detalhamento esta em [data-model.md](./data-model.md).

## Estrategia de Revisao Humana

Regra de ouro: dado incerto nao deve entrar silenciosamente no dashboard.

Fluxo:

- Itens com alta confianca e sem conflito podem ir para revisao rapida ou
  aprovacao automatica configuravel.
- Itens com baixa confianca, divergencia de totais, campos faltantes ou
  conflito com registros existentes entram em fila de revisao.
- Tela de revisao mostra PDF original, trecho extraido, item padronizado
  sugerido, valor, moeda, periodo e motivo da pendencia.
- Toda correcao humana gera `AuditEvent` e preserva o valor anterior.
- Aprovacao publica o dado no conjunto comparavel do dashboard.

## Autenticacao e Auditoria

Escolha: autenticacao nativa do Django no MVP.

Perfis:

- `admin`: configura catalogo, usuarios e parametros.
- `reviewer`: envia documentos, revisa extracoes e aprova valores.
- `viewer`: consulta empresas e dashboards.

Auditoria obrigatoria:

- Upload, exclusao logica, reprocessamento, aprovacao, correcao e login.
- Quem alterou, quando, antes/depois, origem da alteracao e justificativa
  quando aplicavel.
- Soft delete para documentos e valores revisados.

Evolucao:

- SSO/OIDC quando houver usuarios externos ou clientes.
- MFA para administradores.
- Politicas de retencao e criptografia por ambiente.

## Deploy

MVP:

- Docker Compose com `web`, `worker`, `beat`, `postgres`, `redis` e volume de
  arquivos.
- Deploy em uma VPS simples ou plataforma PaaS que suporte containers.
- Nginx/Caddy como proxy reverso.
- Backups diarios do PostgreSQL e do armazenamento de PDFs.

Producao inicial:

- Bucket S3-compativel para PDFs.
- Logs estruturados em stdout.
- Monitoramento basico de erros, filas e tempo de processamento.
- Separacao de variaveis por ambiente.

Escala posterior:

- Workers separados por fila: OCR pesado, extracao leve, reprocessamento.
- Autoscaling de workers se o volume crescer.
- CDN ou URLs assinadas para acesso controlado aos PDFs.

## Roadmap

### MVP

- Login e perfis simples.
- Cadastro/listagem de empresas.
- Upload de PDF.
- Preservacao do PDF bruto.
- Extracao de texto nativo e OCR fallback.
- Normalizacao inicial com catalogo pequeno de linhas financeiras.
- Tela de revisao humana.
- Dashboard por empresa com comparacao anual basica.
- Auditoria de upload, revisao e publicacao.

### Versao 1

- Melhor deteccao de tabelas.
- Reprocessamento por versao de pipeline.
- Regras de validacao por tipo de linha financeira.
- Importacao em lote.
- Exportacao CSV/XLSX.
- Painel de qualidade da extracao.

### Versao Avancada

- Modelos assistidos por LLM para extracao e reconciliacao.
- Agentes para revisar inconsistencias, sugerir mapeamentos e gerar sumarios.
- Catalogos setoriais de linhas financeiras.
- Comparacao entre empresas.
- Alertas de variacao relevante entre anos.
- Relatorios narrativos customizados.
- Multi-tenant e SSO.

## Preparacao para LLMs e Agentes de IA

Preparar sem depender deles no MVP:

- Persistir texto bruto, tabelas, paginas, evidencias e versao do pipeline.
- Separar `RawExtraction`, `ExtractedLineItem` e `StandardizedBalanceValue`.
- Registrar confianca, origem e metodo de cada valor.
- Criar interfaces internas de extracao e normalizacao que possam trocar uma
  regra deterministica por um extrator LLM no futuro.
- Guardar prompts, respostas, modelo, parametros e custo em tabelas proprias
  quando LLMs forem introduzidos.
- Manter aprovacao humana para qualquer sugestao gerada por IA antes de
  publicar no dashboard.
- Projetar agentes como trabalhadores assíncronos auditaveis, nao como a fonte
  direta da verdade.

## Justificativas Tecnicas

- Django reduz complexidade operacional e oferece Admin, ORM, auth e templates
  prontos.
- PostgreSQL permite combinar modelo relacional forte com `jsonb` para payloads
  de extracao que mudam ao longo do tempo.
- Celery com Redis separa OCR e parsing do ciclo de request, preservando UX de
  upload responsiva.
- Tesseract/OCRmyPDF e bibliotecas locais reduzem custo inicial e dependencia de
  APIs pagas.
- HTMX + templates evita manter uma SPA enquanto ainda permite interacoes
  modernas.
- Plotly.js atende dashboards comparativos com baixo esforco de implementacao.
- Armazenamento S3-compativel facilita migrar de desenvolvimento local para
  producao sem mudar o modelo de dados.

## Alternativas Consideradas e Trade-offs

| Alternativa | Trade-off | Decisao |
|-------------|-----------|---------|
| FastAPI + React | Mais flexivel para API-first, mas duplica projetos, build, auth e validacao de UI | Adiar ate haver necessidade real de SPA/API publica |
| Django REST + SPA | Boa separacao, mas aumenta manutencao para um dev solo | Nao usar no MVP |
| Streamlit/Dash | Muito rapido para prototipos, mas pior para auth, revisao humana, auditoria e workflows transacionais | Nao usar como app principal |
| Microservicos | Escala organizacional, mas aumenta deploy, observabilidade e contratos | Evitar; usar modulos internos |
| Banco NoSQL | Flexivel para documentos, mas pior para integridade e consultas financeiras relacionais | Usar PostgreSQL com `jsonb` |
| OCR via API cloud | Melhor qualidade em alguns casos, mas maior custo e dependencia externa | Considerar depois para documentos dificeis |
| LLM no MVP | Pode acelerar extracao, mas adiciona custo, variabilidade e auditoria complexa | Preparar arquitetura, nao depender dele inicialmente |

## Project Structure

### Documentation (this feature)

```text
specs/001-balance-import-reporting/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- http-api.md
|   `-- pipeline-events.md
`-- checklists/
    `-- requirements.md
```

### Source Code (repository root)

```text
app/
|-- manage.py
|-- config/
|-- accounts/
|-- companies/
|-- documents/
|-- extraction/
|-- standardization/
|-- review/
|-- dashboard/
|-- audit/
|-- templates/
|-- static/
`-- tests/
    |-- unit/
    |-- integration/
    |-- contract/
    `-- e2e/

docker/
|-- web.Dockerfile
`-- worker.Dockerfile

docker-compose.yml
```

**Structure Decision**: Usar monolito Django modular. A separacao por apps
mantem dominio claro sem criar servicos separados antes da necessidade.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
