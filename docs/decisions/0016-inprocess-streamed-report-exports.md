# D-016 — Reports render in-process and stream bytes (no object storage)

**Date:** 2026-09-15
**Status:** Accepted
**Related:** implementation_plan.md (Milestone 2, reports), Spec Module 12, FR-057, FR-058, FR-062, FR-063

## Context

Reading reports (JSON, PDF, XLSX) must be generated on demand for any stored reading. Object storage credentials (S3/etc.) are unavailable (rule 22), and report content is fully derivable from the `readings.result` JSONB plus user profile — regenerating is always possible, so durable artifacts add no source of truth, only cleanup burden.

## Decision

- `backend/app/services/reports/generator.py` normalizes `Reading.result` into a versioned report dict (palmistry per FR-057, tarot per FR-058) with rule 11 metadata and the §49.19 disclaimer injected unconditionally.
- `pdf_exporter.py` (ReportLab) and `excel_exporter.py` (openpyxl) render that dict to `bytes` in-process; endpoints stream them with `Content-Disposition` attachment headers. Nothing is written to disk or object storage.
- `reportlab>=5.0.0` and `openpyxl>=3.1.0` pinned in `backend/requirements.txt` (D-006 continuation: heavy deps install with the milestone that uses them).
- Access: report endpoints mirror reading access rules — owner, tarot reader, spiritual consultant, or admin; strangers get 403/404 and unauthenticated callers 401.

## Consequences

- Reports are deterministic per reading state at request time; if a reading is edited, the next export reflects it automatically.
- Large-report CPU cost is on-request (acceptable at current scale); async generation can be layered in TASK-016 notifications/queueing without breaking the API contract.
