# Research: Balance Import Reporting

## Decision: Django monolith for backend and frontend shell

**Rationale**: A single Django application gives one developer authentication,
authorization, migrations, ORM, forms, templates, admin screens and routing in
one coherent stack. The domain has transactional workflows, review queues and
auditing, which fit Django better than a thin API plus separate frontend in the
MVP.

**Alternatives considered**:

- FastAPI + React: stronger for API-first products, but adds frontend build,
  duplicated validation and extra auth integration work.
- Django REST Framework + SPA: good later if the dashboard becomes a client
  product, but heavier than needed for the first operational version.
- Streamlit/Dash: fast analytics prototypes, but weaker for document workflows,
  permissions and audit trails.

## Decision: PostgreSQL as primary database

**Rationale**: The product needs relational integrity for companies, reporting
periods, line items, reviews and audit events. PostgreSQL also supports `jsonb`,
which is useful for raw extraction payloads and pipeline snapshots whose shape
will evolve. PostgreSQL documentation notes that `jsonb` is stored in a
decomposed binary format, supports indexing and is generally preferred for most
applications storing JSON data.

**Alternatives considered**:

- SQLite: excellent local development, but too limited for concurrent document
  processing and production reporting.
- MongoDB/document database: flexible, but weaker for financial relationships,
  constraints and year-over-year queries.
- Data warehouse first: overkill before the product has enough volume and
  stable analytics needs.

## Decision: Preserve PDFs outside the database

**Rationale**: The database stores metadata, checksums, status and URIs; the PDF
binary lives in local storage during development and S3-compatible object
storage in production. This keeps database backups smaller and makes file
delivery, retention and future migration easier.

**Alternatives considered**:

- Store PDFs as database blobs: simpler conceptually, but makes backups and
  file streaming heavier.
- Use object storage only from day one: production-aligned, but local filesystem
  is faster for a solo-dev MVP.

## Decision: Celery + Redis for background processing

**Rationale**: OCR and PDF parsing are too slow and variable for synchronous
web requests. Celery is a mature Python task queue; its documentation describes
it as a system for distributing work across threads or machines. Redis is a
simple broker choice for the MVP and is easy to run in Docker Compose.

**Alternatives considered**:

- Synchronous processing after upload: easiest code, but creates poor upload UX
  and request timeouts.
- Django management command only: good for batch reprocessing, not enough for
  user-triggered uploads.
- RQ/Huey: simpler APIs, but Celery gives more growth room for retries, routing
  and scheduled jobs.

## Decision: PyMuPDF/pdfplumber first, OCR only when needed

**Rationale**: Many PDFs already contain selectable text. Extracting native text
is faster, cheaper and usually more accurate than OCR. For scanned PDFs,
OCRmyPDF with Tesseract is a pragmatic open-source fallback; Tesseract's
project documentation describes it as an OCR engine with user manuals and
trained language data support.

**Alternatives considered**:

- OCR every PDF: simpler pipeline, but slower and may degrade already digital
  documents.
- Cloud OCR first: often strong quality, but increases cost, privacy review and
  vendor dependency.
- LLM vision first: promising, but harder to audit and more variable for the
  MVP.

## Decision: Standardized financial line-item catalog

**Rationale**: Different companies and document layouts may use different
labels for comparable concepts. A shared catalog lets the dashboard compare
values consistently while still preserving raw labels and source evidence for
review.

**Alternatives considered**:

- Store only raw extracted labels: fastest ingestion, but weak comparisons.
- Force manual mapping for every item: accurate but too slow.
- Fully automated mapping: useful later, but needs human review until quality is
  proven.

## Decision: Human-in-the-loop review before publication

**Rationale**: Financial document extraction has ambiguity, formatting
variation and OCR risk. Review tasks keep uncertain or conflicting values out
of the dashboard until a person approves or corrects them.

**Alternatives considered**:

- Publish all extracted values immediately: faster, but risks incorrect
  dashboard data.
- Require manual approval for every value forever: safe but expensive; use it
  initially and relax only for high-confidence cases.

## Decision: Prepare for LLMs with interfaces and evidence, not dependency

**Rationale**: LLMs and agents are likely useful for extraction, mapping,
inconsistency review and narrative reporting. The MVP should store evidence,
pipeline versions and review decisions so an LLM can be introduced as a
replaceable worker later without becoming the system of record.

**Alternatives considered**:

- LLM-first extraction: attractive for speed of experimentation, but adds cost,
  variability and governance complexity.
- No AI preparation: simpler today, but makes future integration harder because
  source evidence and prompt audit data may be missing.

## References

- Django documentation: https://docs.djangoproject.com/
- PostgreSQL JSON types: https://www.postgresql.org/docs/current/datatype-json.html
- Celery introduction: https://docs.celeryq.dev/en/stable/getting-started/introduction.html
- Tesseract documentation: https://tesseract-ocr.github.io/tessdoc/
