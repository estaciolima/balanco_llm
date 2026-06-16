# Balanco LLM

Aplicacao para receber PDFs de balancos empresariais, preservar os arquivos
originais, extrair e padronizar os dados e disponibilizar comparacoes em
dashboard.

## O que o projeto faz

- upload de PDFs por empresa
- preservacao do arquivo bruto
- pipeline de extracao e padronizacao
- fila de revisao humana
- dashboard com comparacao entre periodos
- trilha de auditoria

## Requisitos

- Python 3.12
- `pip`
- Docker Desktop opcional, para subir toda a stack com Postgres e Redis

## Como rodar

Voce pode rodar de duas formas:

1. localmente, com SQLite e sem containers
2. com Docker Compose, usando Postgres e Redis

## Opcao 1: rodar localmente

### 1. Criar e ativar o ambiente virtual

Se o `.venv` ja existir:

```powershell
.venv\Scripts\Activate.ps1
```

Se ainda nao existir:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Configurar variaveis de ambiente

Para rodar localmente de forma simples, voce pode usar o fallback do SQLite e
nao precisa definir `DATABASE_URL`.

Se quiser manter um arquivo de ambiente local:

```powershell
Copy-Item .env.example .env
```

Ajustes recomendados no `.env` para execucao local sem Docker:

```text
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
CELERY_TASK_ALWAYS_EAGER=true
MEDIA_ROOT=app/media
MEDIA_URL=/media/
```

Observacao: a `DATABASE_URL` do `.env.example` aponta para o servico `postgres`
do Docker Compose. Fora do Docker, remova essa variavel ou troque por uma URL
valida do seu banco.

### 4. Aplicar migrations e carregar dados iniciais

```powershell
python app/manage.py migrate
python app/manage.py load_standard_line_items
python app/manage.py bootstrap_roles
python app/manage.py createsuperuser
```

### 5. Subir a aplicacao

```powershell
python app/manage.py runserver
```

Abra:

- `http://127.0.0.1:8000/login/`
- `http://127.0.0.1:8000/admin/`

### 6. Rodar testes

```powershell
python -m pytest app/tests
```

## Opcao 2: rodar com Docker Compose

Essa opcao sobe:

- Django web
- Celery worker
- Celery beat
- PostgreSQL
- Redis

### 1. Subir os containers

```powershell
docker compose up --build
```

### 2. Aplicar migrations e carregar dados iniciais

Em outro terminal:

```powershell
docker compose exec web python app/manage.py migrate
docker compose exec web python app/manage.py load_standard_line_items
docker compose exec web python app/manage.py bootstrap_roles
docker compose exec web python app/manage.py createsuperuser
```

### 3. Acessar a aplicacao

- `http://127.0.0.1:8000/login/`
- `http://127.0.0.1:8000/admin/`

### 4. Rodar testes via container

```powershell
docker compose exec web pytest app/tests
```

## Worker e processamento

No modo local simples, usar `CELERY_TASK_ALWAYS_EAGER=true` ajuda bastante:
as tasks rodam no mesmo processo do Django e voce nao precisa iniciar Redis nem
worker para testar upload e processamento.

Se quiser rodar Celery localmente com Redis:

```powershell
celery -A config.celery_app worker -l info
celery -A config.celery_app beat -l info
```

## Comandos uteis

```powershell
python app/manage.py migrate
python app/manage.py createsuperuser
python app/manage.py load_standard_line_items
python app/manage.py bootstrap_roles
python app/manage.py import_balance_pdfs --help
python app/manage.py reprocess_documents --help
python -m pytest app/tests
```

## Estrutura principal

```text
app/
  companies/         cadastro de empresas
  documents/         upload e armazenamento de PDFs
  extraction/        pipeline de extracao
  standardization/   padronizacao dos dados
  review/            revisao humana
  dashboard/         consultas e visualizacoes
  audit/             trilha de auditoria
  config/            settings, urls e celery
```

## Estado atual

- testes automatizados passam localmente
- E2E com Playwright existem, mas podem ser ignorados se o browser nao estiver instalado
- OCR fallback ainda esta em modo inicial

## Fluxo recomendado para desenvolvimento

Para iterar mais rapido no dia a dia:

1. ativar `.venv`
2. rodar com `CELERY_TASK_ALWAYS_EAGER=true`
3. executar `python app/manage.py runserver`
4. rodar `python -m pytest app/tests`

Isso evita depender de Postgres, Redis e worker enquanto voce evolui tela,
modelo e regras de negocio.
