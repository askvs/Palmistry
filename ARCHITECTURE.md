# Architecture

Current architecture of the **Palmistry & Tarot Intelligence Platform**.
Authoritative contract: `PALMISTRY_TAROT_AI_AGENT_SPEC.md` (§5, §15, §49).

## System overview

```text
Next.js frontend (React 19, Pages Router, Tailwind CSS)  :3000
        │  fetch + credentials:include · Bearer access token · httpOnly refresh cookie
        ▼
FastAPI API Gateway / modular monolith  :8000
  ├── /api/v1 router (versioned REST, JSON, §49.14 envelope)
  ├── middleware: request-ID + access logs, CORS, auth rate limiting
  ├── auth: Argon2id passwords · JWT access tokens · rotating DB-backed
  │        refresh tokens · Google OAuth2 adapter · RBAC dependencies (§49.3)
  └── services/ (user, profile, palm_analysis, tarot, interpretation,
                 personality, trends, recommendations, notifications,
                 analytics, reports, admin, booking, reader)  [module skeletons; see PROGRESS.md]
        ▼
PostgreSQL 16 (transactional system of record; Alembic migrations)  :5432
```

## Implemented layers

### API Gateway (FastAPI, `backend/app`)

- App factory with lifespan logging; OpenAPI at `/api/openapi.json`, docs at `/api/docs`.
- `/api/v1` versioned router (§37.1).
- Consistent error envelope `{code, message, request_id[, fields]}` for HTTP errors,
  validation errors (422), auth errors (401/403/409/503), and unhandled 500s (§49.14/§49.18).
- `RequestContextMiddleware`: assigns/propagates `X-Request-ID`, structured access logs
  with duration.
- In-process fixed-window rate limiting on auth endpoints (D-011; Redis-backed gateway
  limit deferred per D-005).

### Authentication & RBAC (FR-001..FR-004, `backend/app/auth`)

| Concern | Implementation |
|---|---|
| Password hashing | Argon2id via `argon2-cffi` (§49.3) |
| Access token | JWT HS256, 30 min, claims `sub/role/type/iat/exp/jti` (PyJWT) |
| Refresh token | Opaque 256-bit token, SHA-256 hashed in `refresh_tokens` table, rotating; reuse of a revoked token revokes all of that user's sessions (D-008) |
| Cookie | `palmistry_refresh` httpOnly, SameSite=Lax, Secure in prod (D-009) |
| OAuth2 | Google via authlib behind `app/auth/oauth/google.py`; 503 `OAUTH_NOT_CONFIGURED` until credentials exist (D-010) |
| RBAC | `get_current_user` + `require_roles(*roles)` dependencies; backend-enforced (§49.3); role bundles: `require_user`, `require_tarot_reader`, `require_spiritual_consultant`, `require_admin`; plus the session bundles `require_consultant_role` (readers + consultants, deliberately **not** admin) and `require_session_role` (seekers + readers + consultants) that gate the live-consultation module |
| Monitoring | `ErrorMonitoringMiddleware` — outermost user middleware; records 5xx/401/403/429 responses into `error_logs` (deduplicated, `occurrences` counter) and keeps an in-process latency ring buffer for `/admin/system/performance` |
| Endpoints | `POST /auth/register` 201 · `POST /auth/login` · `POST /auth/refresh` (rotation) · `POST /auth/logout` 204 · `GET /auth/me` · `GET /auth/google/authorize` · `GET /auth/google/callback` |

### Data layer

- PostgreSQL 16 (local service `postgresql-x64-16`); DBs: `palmistry` (dev),
  `palmistry_test` (tests) — D-007.
- Alembic from the beginning (§49.10): `backend/alembic`, migration
  `0001_auth_rbac` creates `users` (UUID PK, lowercase unique email, native
  `user_role` enum, nullable password_hash for OAuth-only users, unique google_id,
  is_active, UTC timestamps) and `refresh_tokens` (FK cascade, unique token_hash,
  expires_at/revoked_at/rotated_from).
- Models: `app/models/{common,user,refresh_token}.py` — UUID PKs, timezone-aware
  UTC timestamps.
- MongoDB / Redis / Elasticsearch / Chroma / Neo4j / InfluxDB: not yet wired (later
  milestones; see PROGRESS.md).

### Frontend (Next.js 16 Pages Router, `frontend/src`)

- `services/api.js` — central fetch client: Bearer injection from module memory,
  `credentials: "include"`, error-envelope → `ApiError` mapping.
- `services/auth.js` — register/login/refresh/logout/me + Google authorize URL.
- `hooks/useAuth.js` — `AuthProvider` context: silent session restore on mount
  (refresh → user), `{user, loading, login, register, refresh, logout}`.
- Pages: `/login`, `/register` (WF-01: loading/error/empty states, field errors,
  password strength meter, Google button), `/dashboard` (protected stub with
  redirect-to-login), role-aware MainLayout (sign-in/sign-out, user name).
- All pages have LOADING/ERROR/SUCCESS states (§0.1 #10).

## Key decisions

See `docs/decisions/` — D-007 PostgreSQL local install, D-008 DB-backed rotating
refresh tokens, D-009 cookie/in-memory split, D-010 Google OAuth adapter,
D-011 in-process rate limiting. Earlier: D-001..D-006 in `PROGRESS.md`.

## Testing

- `backend/tests/` (pytest): health suite + auth suites — password hashing,
  endpoint flows (register/login/refresh rotation/reuse detection/logout/me),
  RBAC matrix (§49.3), Google adapter (mocked), rate limiting. Run against
  `palmistry_test` with Alembic-managed schema and per-test truncation.
- Postman: `backend/postman/palmistry-auth.postman_collection.json` (§49.15).
- Frontend: lint + production build gates; Vitest/RTL/Playwright land with their
  milestones (§49.15).

## Deployment (target)

- Docker Compose stack (`docker-compose.yml`: db + migrate + backend + frontend,
  volumes pgdata/uploads); GitHub Actions CI (`ci.yml`) + ECR push (`deploy.yml`);
  AWS default per docs/deployment/aws-production.md (§49.16). In-process rate
  limiting and latency buffer are per-worker until Redis lands.
