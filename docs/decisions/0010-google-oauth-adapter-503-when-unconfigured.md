# D-010 — Google OAuth2 behind an adapter; 503 when unconfigured

**Date:** 2026-08-30
**Status:** Accepted
**Context:** §49.3 fixes Google as the default OAuth2 provider. No Google credentials
exist yet; §0.1 rule 22 requires implementing the adapter + configuration + validation +
test path, documenting the blocker, and continuing.

**Decision:**
- `app/auth/oauth/google.py` wraps authlib's Starlette client behind a narrow adapter
  (`is_configured`, `authorize_redirect`, `authorize_access_token`, `extract_profile`).
- `GET /api/v1/auth/google/authorize` returns a controlled 503
  (`OAUTH_NOT_CONFIGURED`, §49.18) when `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` are
  unset.
- Callback upserts users by email; OAuth-only users have `password_hash = NULL`;
  existing password accounts are linked, not duplicated.
- Tests mock the provider — no real Google calls in CI. Full end-to-end verification
  is blocked until credentials are supplied (blocker recorded in PROGRESS.md).

**Consequences:**
- Another provider can be added by implementing the same adapter interface (§0.1 #7).
- The frontend "Continue with Google" button surfaces the 503 as a provider-error
  banner with email/password login unaffected.
