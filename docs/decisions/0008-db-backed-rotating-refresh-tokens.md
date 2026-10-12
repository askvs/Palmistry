# D-008 — Refresh tokens: opaque, DB-backed, rotating with reuse detection

**Date:** 2026-08-30
**Status:** Accepted
**Context:** §49.3 requires "JWT access tokens with short expiry and rotating refresh
tokens". Redis is not available locally (D-005), so server-side session state cannot
live in Redis yet.

**Decision:**
- Access token: JWT (HS256, `SECRET_KEY`, 30 min, claims `sub`, `role`, `type`, `iat`,
  `exp`, `jti`).
- Refresh token: opaque 256-bit random value (`secrets.token_urlsafe`), stored
  SHA-256-hashed in the `refresh_tokens` table with `expires_at`, `revoked_at`,
  `rotated_from`.
- Every `/auth/refresh` call revokes the presented token and issues a rotated successor
  (rotation chain tracked via `rotated_from`).
- Reuse detection: presenting an already-revoked token is treated as theft — ALL refresh
  tokens for that user are revoked and the request fails 401.

**Consequences:**
- Session persistence survives server restarts without Redis.
- Rotation + reuse detection satisfies §49.3 without external state.
- When Redis lands, the storage can move behind the same service interface.
