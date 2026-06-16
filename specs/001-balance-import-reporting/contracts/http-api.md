# HTTP Interface Contract: Balance Import Reporting

The MVP is server-rendered, but these contracts define stable routes and
expected behavior for browser flows, tests and future JSON endpoints.

## Authentication

### GET /login/

Shows the login form.

### POST /login/

Authenticates a user and starts a session.

**Validation**:

- Invalid credentials return the login form with a clear error.
- Successful login redirects to the company list or prior requested page.

### POST /logout/

Ends the active session and redirects to login.

## Companies

### GET /companies/

Lists companies visible to the current user.

**Query Parameters**:

- `q`: optional name search
- `status`: optional active/archive filter

### GET /companies/{company_id}/

Shows one company, its reporting periods, uploaded documents and latest
processing statuses.

### POST /companies/

Creates a company.

**Required Fields**:

- `legal_name`

**Optional Fields**:

- `display_name`
- `tax_identifier`
- `country`

## Documents

### GET /companies/{company_id}/documents/new/

Shows the PDF upload form.

### POST /companies/{company_id}/documents/

Uploads a balance PDF for processing.

**Request**:

- Multipart form with `file`
- Required `fiscal_year`
- Optional `notes`

**Expected Behavior**:

- Accepts PDF files.
- Rejects unsupported file types.
- Computes a document checksum.
- Prevents silent duplicates.
- Creates a queued processing job.

### GET /documents/{document_id}/

Shows document metadata, source PDF access, processing runs, extracted items and
review status.

### POST /documents/{document_id}/reprocess/

Queues a new processing run for an existing PDF.

**Expected Behavior**:

- Creates a new `ProcessingRun`.
- Does not overwrite prior run evidence.
- Adds an audit event.

## Review

### GET /review/

Lists open review tasks.

**Query Parameters**:

- `company_id`
- `reason`
- `status`

### GET /review/{task_id}/

Shows a review workspace with source PDF evidence and extracted values.

### POST /review/{task_id}/approve/

Approves the suggested standardized value.

**Expected Behavior**:

- Creates or updates the active `StandardizedBalanceValue`.
- Marks the task approved.
- Adds an audit event.

### POST /review/{task_id}/correct/

Corrects extracted value, standard line mapping, period or currency.

**Required Fields**:

- `standard_line_item_id`
- `value`
- `currency`
- `reporting_period_id`
- `reason`

**Expected Behavior**:

- Marks the extracted item corrected.
- Publishes the corrected standardized value.
- Adds an audit event with before/after values.

### POST /review/{task_id}/reject/

Rejects a candidate extraction.

**Required Fields**:

- `reason`

## Dashboard

### GET /companies/{company_id}/dashboard/

Shows year-over-year comparison for approved standardized values.

**Query Parameters**:

- `start_year`: optional year selected from years already loaded for the company
- `end_year`: optional year selected from years already loaded for the company
- `category`
- `currency`

**Expected Behavior**:

- Displays only approved standardized values.
- Shows missing years explicitly.
- Links values back to the source document and review history.

## Audit

### GET /audit/

Lists audit events visible to administrators.

**Query Parameters**:

- `actor`
- `event_type`
- `target_type`
- `date_from`
- `date_to`
