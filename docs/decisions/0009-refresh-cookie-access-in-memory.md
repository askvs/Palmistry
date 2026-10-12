# D-009 — Refresh token delivered as httpOnly cookie; access token in memory

**Date:** 2026-08-30
**Status:** Accepted
**Context:** The frontend (Next.js) must keep short-lived access tokens while surviving
page reloads. Storing tokens in `localStorage` exposes them to XSS.

**Decision:**
- Refresh token: `httpOnly` cookie `palmistry_refresh` (SameSite=Lax, Secure only in
  production, path `/api/v1/auth`) — unreadable to JavaScript.
- Access token: returned in the JSON body and held in module memory by the frontend
  auth service; lost on reload, restored via `/auth/refresh`.
- `/auth/refresh` reads the cookie, so CORS requests need `credentials: "include"`.

**Consequences:**
- XSS cannot read the refresh token; the access token's exposure window is 30 minutes.
- SameSite=Lax keeps the cookie out of most cross-site requests while allowing the
  top-level Google OAuth redirect flow to work.
- Frontend session restore = one refresh call on mount; unauthenticated users see a
  silent 401 and remain logged out.
