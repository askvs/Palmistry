# D-013 — Profile data model: 1:1 profiles table, string catalogs, lazy creation

**Date:** 2026-08-31
**Status:** Accepted

**Context:** TASK-004 (FR-005) needs profile creation, spiritual interests,
spiritual goals, reading preferences, and profile customization. The spec
does not fix the database schema (§10.2 defers to §49 defaults), and PROGRESS.md
already anticipated "extending the users table via a new `profiles` migration".

**Decision:**
- Three tables in migration `0002_profiles`: `profiles` (1:1 with `users`,
  unique FK with ON DELETE CASCADE), `profile_interests` (association rows with a
  `(profile_id, interest)` unique constraint), and `profile_goals` (free-text rows,
  max 25 per profile). UUID PKs and UTC timestamps throughout (§37.2).
- Preference values (`default_deck`, `favorite_spread`, `tone`, `age_group`) are
  **validated strings**, not native PG enums. Rationale: §49.6 requires data-driven
  deck definitions so additional decks can be added without schema churn; closed
  native enums would need `ALTER TYPE` on every catalog change. Allowed values live
  in `app/services/profile/catalog.py` and are enforced by Pydantic validators
  (422 with the §49.14 envelope), with server defaults `Rider-Waite-Smith`,
  `Three Card`, `Gentle` (per WF-02), and notification flags `daily=on`,
  `reminders=on`, `sms=off` (per WF-02 checkboxes).
- Profile rows are created **lazily on first access** (get-or-create) rather than
  eagerly at registration. This covers pre-migration accounts, the admin seeder,
  and OAuth upserts without touching the auth service; migration `0002` also
  backfills one profile per existing user.
- Interests are replaced wholesale (`PUT /profile/interests`), matching the
  chip-multiselect UX; goals are individually managed
  (`POST/PATCH/DELETE /profile/goals`).
- Session history on the profile page is an **empty state** for now: readings
  tables belong to TASK-002 (remaining) / TASK-006 (Milestone 2). No readings
  schema was invented ahead of that milestone (§40.1 #4, consistent with D-012).

**Consequences:**
- Adding a deck, spread, tone, or interest later is a one-line catalog change plus
  frontend option list update — no migration.
- Invalid catalog values cannot reach the database through the API; direct DB
  writes are unvalidated (acceptable: API is the only write path).
- The users/profiles 1:1 relies on the unique FK; SQLAlchemy relationships on both
  sides keep deletes cascading cleanly.
