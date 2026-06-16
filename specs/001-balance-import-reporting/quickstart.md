# Quickstart: Balance Import Reporting

This guide validates the planned feature end to end. Commands are expected to
be finalized during implementation, but the scenarios below define the required
operational flow.

## Prerequisites

- Docker and Docker Compose installed
- A sample balance PDF with selectable text
- A sample scanned balance PDF for OCR fallback validation
- Test user with reviewer permissions

## Environment

Required environment variables:

```text
DATABASE_URL=postgres://...
REDIS_URL=redis://...
MEDIA_ROOT=./var/media
SECRET_KEY=local-development-secret
DJANGO_DEBUG=true
```

Production additionally requires:

```text
S3_BUCKET=...
S3_ENDPOINT_URL=...
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
```

## Setup

1. Build and start services:

```bash
docker compose up --build
```

2. Run migrations:

```bash
docker compose exec web python manage.py migrate
```

3. Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

4. Load the initial standard line-item catalog:

```bash
docker compose exec web python manage.py load_standard_line_items
```

## Validation Scenario 1: Upload and Preserve Raw PDF

1. Log in as a reviewer.
2. Create or open a company.
3. Upload a valid balance PDF.
4. Confirm the document appears with status `queued` or `processing`.
5. Confirm the raw PDF can be opened from the document detail page.
6. Confirm duplicate upload of the same PDF is blocked or clearly flagged.

**Expected outcome**: The PDF is preserved, checksum is recorded and processing
starts without blocking the upload page.

## Validation Scenario 2: Extract and Standardize Data

1. Wait for the processing run to complete.
2. Open the document detail page.
3. Confirm raw extraction evidence is available.
4. Confirm candidate line items are mapped to standard line items.
5. Confirm uncertain values create review tasks.

**Expected outcome**: The system stores both raw extraction payloads and
standardized processed values linked to the source document.

## Validation Scenario 3: Human Review

1. Open the review queue.
2. Select a pending item.
3. Compare the extracted value with the source PDF evidence.
4. Approve a correct item.
5. Correct a wrong item and provide a reason.
6. Reject an invalid item and provide a reason.

**Expected outcome**: Approved or corrected values become available for the
dashboard, and every action creates an audit event.

## Validation Scenario 4: Dashboard Comparison

1. Open a company with at least two reporting periods.
2. Go to the dashboard.
3. Filter by category or period range.
4. Confirm values are grouped by standard line item and year.
5. Confirm missing years are shown as gaps, not fabricated values.
6. Open a value's source link and verify it traces back to the document and
   review history.

**Expected outcome**: Users can compare all available years for a company from
a single dashboard view.

## Validation Scenario 5: OCR Fallback

1. Upload a scanned PDF.
2. Confirm processing detects lack of selectable text.
3. Confirm OCR runs and produces text evidence.
4. Confirm uncertain OCR-derived values require review.

**Expected outcome**: Scanned PDFs are processed through OCR, with confidence
and evidence preserved.

## Test Commands

Expected implementation test commands:

```bash
docker compose exec web pytest
docker compose exec web pytest app/tests/integration
docker compose exec web pytest app/tests/contract
docker compose exec web pytest app/tests/e2e
```

Current local shortcut during development:

```powershell
.venv\Scripts\python.exe -m pytest app/tests
```

## Performance Checks

- PDF upload request completes within 5 seconds for files up to 25 MB.
- Typical PDF processing completes within 5 minutes.
- Company dashboard renders within 2 seconds for up to 10 years of data.

## References

- Data model: [data-model.md](./data-model.md)
- HTTP contracts: [contracts/http-api.md](./contracts/http-api.md)
- Pipeline events: [contracts/pipeline-events.md](./contracts/pipeline-events.md)
