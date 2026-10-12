# D-011 — Auth rate limiting: in-process fixed window until Redis

**Date:** 2026-08-30
**Status:** Accepted (temporary)

**Context:** §49.14 requires rate limiting; credential-stuffing protection on
register/login/refresh is the minimum viable control for TASK-003. Redis is unavailable
locally (D-005), so a shared counter store is not yet possible.

**Decision:**
- `app/middleware/rate_limit.py` implements a fixed-window counter keyed by
  `scope:client_ip` in process memory (10 requests/minute per IP per auth scope,
  configurable via `AUTH_RATE_LIMIT_PER_MINUTE`).
- Applied to `register`, `login`, `refresh` only; exceeding the limit returns the
  standard error envelope with HTTP 429.

**Consequences:**
- Limits are per-worker; a multi-process deployment weakens them (acceptable for local
  development only).
- When Redis lands (with Celery, per D-005/D-006), the same dependency signature is
  re-implemented against Redis, and the global 60 req/min gateway limit (§49.14) is
  added at that point.
