# Implementation Notes

## Validation Summary

- Environment: Python 3.12.10 in `.venv`
- Test command: `.venv\Scripts\python.exe -m pytest app/tests`
- Result: 26 tests passed, 3 tests skipped
- Skipped coverage: Playwright E2E tests are implemented but skip automatically when a local Chromium browser is not available

## Scope Completed

- Django monolith scaffold with Docker, Celery and pytest
- Company CRUD and authentication basics
- PDF upload with raw file preservation, duplicate detection and queued processing
- Extraction pipeline skeleton with raw evidence, candidate parsing and standardization
- Human review queue with approve, correct and reject actions
- Dashboard and audit list views with contract, unit and integration coverage

## Remaining Gaps

- Dashboard chart rendering is represented by serialized data, not a finalized interactive front end
- OCR fallback is a stub adapter and not yet wired to a real OCR execution flow
