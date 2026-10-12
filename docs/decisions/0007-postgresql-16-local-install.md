# D-007 — PostgreSQL 16 installed locally (not SQLite)

**Date:** 2026-08-30
**Status:** Accepted
**Context:** TASK-003 (auth) requires a real database. The spec (§49.10) fixes PostgreSQL
as the transactional system of record. Docker is unavailable on this machine (D-005), so
no containerized PostgreSQL was possible. The owner explicitly chose "Install PostgreSQL
now" over a SQLite dev/test fallback.

**Decision:** Install PostgreSQL 16 via winget (EDB installer), run it as the standard
Windows service `postgresql-x64-16`, and create `palmistry` (dev) and `palmistry_test`
(tests) databases. All access uses the local `postgres` superuser with a development
password; production credentials remain environment-provided (§20.2).

**Consequences:**
- Migrations are written for real PostgreSQL from day one (native UUID, timezone-aware
  timestamps, native enum `user_role`) — no SQLite-compatibility compromises.
- `DATABASE_URL` / `DATABASE_TEST_URL` in `.env` point at the local instance.
- Redis remains absent locally; Redis-backed features stay deferred (D-005).
- Connection credentials are development-only placeholders and must never ship.
