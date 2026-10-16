# Report Data — Palmistry & Tarot Intelligence Platform

> **What this file is:** a complete factual inventory of the project, compiled directly from the repository (spec, source code, docs, changelog) on **2026-10-16**. It is the single source of truth for writing the final project report and building the presentation deck. Pure facts — no invented claims; every section cites where the fact comes from.

**Project root:** `C:\Users\ASUS\Desktop\Palmistry`
**Internal branding found in repo:** "MysticLens" (backend dev-server script comment; default email sender name `MysticLens Divination`).

**Accuracy conventions used below:**
- `[SPEC]` — from `PALMISTRY_TAROT_AI_AGENT_SPEC.md`, the authoritative master contract (~4,000+ lines, 50 sections, FR-001…FR-072).
- `[CODE]` — verified directly in the source code on 2026-10-16.
- `[DOC]` — from project documentation (README, CHANGELOG, AGENT_PROGRESS.md, PROGRESS.md, decisions, deployment docs).
- **Doc drift** is flagged explicitly where docs and code disagree.
- `[FILL]` — personal/team details you must fill in before submission.

---

## 0. Quick Numbers (one-screen summary)

| Metric | Value |
|---|---|
| User roles | 4 — user (seeker), tarot_reader, spiritual_consultant, admin |
| Backend | FastAPI 0.115.6 · Python 3.11 (written 3.12-compatible, D-001) · 124 files / 20,776 lines |
| Frontend | Next.js 16.3.2 (Pages Router) · React 19.2.8 · Tailwind CSS v4 · 131 files / 28,749 lines |
| Database | PostgreSQL 16 · 13 Alembic migrations · 23 tables (+ `alembic_version`) |
| REST API | 138 route handlers across 18 endpoint modules, under `/api/v1` |
| Frontend routes | 33 user-facing routes across 5 route spaces |
| Automated tests | 445 test functions · 30 test files · 8,112 lines (backend pytest) |
| Tarot content | 78-card Rider-Waite-Smith deck · 6 standard spreads · reader-authored custom spreads (1–10 positions) |
| Palm CV pipeline | MediaPipe HandLandmarker + OpenCV crease analysis · 5 lines · 6 mounts · palm shape · digit ratios |
| Report exports | PDF (ReportLab) + Excel (openpyxl, 3 sheets) + JSON |
| Notifications | In-app (bell + center) · APScheduler jobs (daily guidance 8:00, reading reminders, booking reminders) |
| Deployment stack | Docker + Docker Compose + GitHub Actions (CI + ECR push) + AWS Fargate/RDS runbook |
| Git history | 11 commits, 2026-10-12 → 2026-10-16 |
| Documented changelog | v0.5.2 (2026-09-08) → v0.12.0 (2026-09-26), plus 7 "[Unreleased]" feature blocks through Oct 2026 |

Counts measured 2026-10-16. Detailed evidence in §16.

---

## 1. Project Identity `[SPEC §1–§4]`

| Field | Value |
|---|---|
| Project name | **Palmistry & Tarot Intelligence Platform** |
| One-line description | "Build an AI-powered platform that analyzes palm images and tarot card selections to generate personalized spiritual insights related to personality traits, relationships, career growth, life trends, strengths, opportunities, and self-reflection." (§1.2) |
| Problem statement | The need for a single interactive platform combining palm-image analysis, tarot workflows, AI interpretation, personalization, guidance, reporting, analytics, and role-based user experiences (§1.6) |
| Purpose / motivation | Create customized spiritual experiences by combining palm analysis, tarot readings, AI interpretation, personality intelligence, trend analysis, recommendations, and interactive guidance (§1.7) |
| Target audiences | Spiritual enthusiasts · wellness platforms · tarot practitioners · life coaches · personal development communities (§1.4) |

### Platform combination (§1.3)
Computer vision · AI interpretation models · symbolic analysis · tarot reading workflows · interactive guidance systems.

### Core user journey `[SPEC §28.1]`
Open platform → Register/Login → Authenticate → Profile → choose Palm (upload image) or Tarot (spread + draw) → Generate Interpretation → Personalized Insights → Recommendations → Save to history → Dashboard/Report → Export PDF/Excel.

### Roles (§4.1, §49.3)

| Role (DB value) | Console | Responsibility |
|---|---|---|
| User / Seeker (`user`) | `/dashboard` seeker dashboard | Own profile, readings, reports, notifications, recommendations; books consultations |
| Tarot Reader (`tarot_reader`) | Reader workspace (`/reader/*`) | Reading access/oversight, reading analytics, report management, custom spread authoring; hosts live sessions |
| Spiritual Consultant (`spiritual_consultant`) | `/consultant/*` console | Trend analysis, consultation insights, guidance effectiveness, client roster; hosts live sessions |
| Administrator (`admin`) | `/admin/*` console | User governance, platform analytics, configuration, system reports, audit logs, monitoring. Deliberately **no** booking/session-hosting access (read-only oversight) |

RBAC is **backend-enforced**; frontend checks are supplementary (`[SPEC §49.3]`, `[CODE] backend/app/auth/rbac.py`).

### Objectives (§2)

- **Primary:** build the platform; palm analysis; tarot workflows; AI interpretations + personalized guidance; personality intelligence; life trend analysis; recommendations; dashboards/analytics/reports; Docker + cloud deployment.
- **Technical:** secure auth, JWT, OAuth2, RBAC; FE/BE integration; API validation & testing; E2E workflows; security testing; performance optimization; monitoring & logging; Docker; production deployment; documentation.
- **User-facing:** profiles & preferences; palm upload; tarot spread selection & card interactions; personalized readings; reading history; personality insights; palm & tarot reports; recommendations & guidance; dashboards & visual analytics; PDF/Excel export; notifications & engagement.

### In-scope capability groups (§3.1) — 13 modules
1. User authentication & RBAC · 2. User profile management · 3. Palm analysis engine · 4. Tarot reading engine · 5. AI interpretation engine · 6. Personality intelligence · 7. Life trend analysis · 8. Spiritual guidance scoring · 9. Recommendation engine · 10. Dashboards & analytics · 11. Notification & engagement system · 12. Reports & export · 13. Final integration, testing & deployment.

### Project milestones `[SPEC §17 / §38]`

| Milestone | Window | Focus | Spec evaluation criteria |
|---|---|---|---|
| M1 | Week 1–2 | Initialization, design, core setup, auth/RBAC, profiles, datasets | Init done, auth implemented, profiles functional, datasets integrated |
| M2 | Week 3–4 | Palm analysis & tarot intelligence, reading workflows, reports | Palm engine operational, tarot workflows functional, reading generation implemented |
| M3 | Week 5–6 | AI interpretation, personality, recommendations, life trends, dashboards | Interpretation engine operational, recommendation system functional, guidance workflows completed |
| M4 | Week 7–8 | Analytics, testing, deployment, docs, presentation | Deployed FE+BE, dashboards & reporting operational, E2E workflow demonstrated |

---

## 2. Technology Stack

### 2.1 Actually implemented (versions from manifests) `[CODE]`

| Layer | Technology | Version / detail |
|---|---|---|
| Frontend framework | Next.js (Pages Router) | 16.3.2 |
| Frontend runtime | React / React DOM | 19.2.8 |
| Styling | Tailwind CSS v4 (+ `@tailwindcss/postcss` v4) | semantic design tokens in `globals.css` `@theme` |
| Charts | chart.js ^4.5.1 + react-chartjs-2 ^5.3.1 | dashboard line/bar presets in `frontend/src/lib/chartjs.js` |
| Fonts / icons | Inter (body) + Fraunces (display); hand-built inline SVG icon set (40+ lucide-style strokes, "never use emoji as UI icons") | `frontend/src/components/icons.js` |
| Linting | ESLint ^9 + eslint-config-next 16.3.2 | `npm run lint` gate |
| Backend framework | FastAPI | 0.115.6 |
| Backend server | Uvicorn[standard] | 0.34.0 |
| Language | Python | 3.11.7 local (spec default 3.12; code written 3.12-compatible — D-001) |
| Validation | Pydantic / pydantic-settings | 2.10.4 / 2.7.1 |
| ORM / migrations | SQLAlchemy / Alembic | 2.0.36 / 1.14.0 |
| Database driver | psycopg[binary] | 3.2.3 |
| Database | PostgreSQL | 16 (local dev service; `postgres:16-alpine` in Compose) |
| Password hashing | argon2-cffi (Argon2id) | 23.1.0 |
| Tokens | PyJWT (HS256) | 2.10.1 |
| OAuth | authlib (Google adapter) | 1.5.1 |
| Email validation | email-validator | 2.2.0 |
| HTTP client | httpx | 0.28.1 |
| Computer vision | mediapipe (HandLandmarker .task model) | >= 1.0.0 · model asset `models/hand_landmarker.task` |
| Image processing | opencv-python-headless | >= 4.10.0 |
| Numeric / imaging | numpy >= 2.0 · pillow >= 11 | pipeline math + image IO |
| LLM providers | openai >= 1.0 · groq >= 0.11 | adapter order OpenAI → Groq → deterministic rule engine `[CODE llm_adapter.py]` |
| Data science | scikit-learn >= 1.5 · pandas >= 2.2 | present in requirements (recommendation engine reworked to LLM in v0.10.0) |
| PDF reports | reportlab >= 5 | mystical dark/gold multi-page dossier |
| Excel reports | openpyxl >= 3.1 | 3-sheet workbook |
| Scheduling | APScheduler >= 3.10 | notification + booking schedulers |
| Testing | pytest 8.3.4 · httpx | backend suites against `palmistry_test` |
| Containers | Docker (backend + frontend Dockerfiles, healthchecks) + Docker Compose | db + migrate + backend + frontend |
| CI/CD | GitHub Actions | `ci.yml` (tests/lint/build/docker) + `deploy.yml` (ECR push via OIDC) |
| Cloud target | AWS (Fargate/RDS/S3/ECR per runbook) | `docs/deployment/aws-production.md`; Vercel config present for the frontend, Neon-compatible Postgres check script included |

### 2.2 Spec-listed technologies NOT (yet) wired `[SPEC §16 + DOC]`

| Spec technology | Status |
|---|---|
| MongoDB (document store) | not wired — deferred (PROGRESS.md) |
| Redis (cache/session) | not wired — in-process rate limit + latency buffer instead (D-005/D-011) |
| Elasticsearch | not wired |
| Chroma / FAISS (vector DB) | not wired |
| Neo4j (knowledge graph) | not wired |
| InfluxDB (time-series) | not wired |
| TensorFlow / PyTorch | not trained/deployed; runtime CV is MediaPipe + OpenCV (`[CODE]` pipeline v1.0.0) |
| YOLO | YOLOv5 palm-line annotations exist in `dataset/`, not wired into the runtime pipeline |
| LangChain | not used — direct OpenAI/Groq SDK via adapter |
| Hugging Face Transformers | not used (no local model download path in requirements) |
| Sentence Transformers | listed in `.env.example` (`EMBEDDING_MODEL=all-MiniLM-L6-v2`) but embeddings module not implemented |
| Plotly | deferred to dashboards milestone (D-004); Chart.js used instead |
| Celery + Redis (async jobs) | not used — APScheduler in-process jobs |
| SendGrid / Twilio (email/SMS) | not integrated; in-app notifications only (email delivery removed, see §17) |
| Stripe / Razorpay (payments) | not implemented (spec default Razorpay; "do not invent pricing" §49.12) |
| Google Analytics | not integrated |

> **Doc drift to be aware of:** `README.md` lists "Lucide React" under frontend; `package.json` has no lucide dependency (icons are a hand-built inline SVG set).

---

## 3. Repository Layout `[CODE]`

```text
Palmistry/
├── frontend/                  Next.js 16 app (src/pages, src/components, src/services, src/hooks, src/lib, src/layouts, src/styles)
│   ├── public/cards/          78 tarot card images (m00-m21, w01-w14, c01-c14, s01-s14, p01-p14)
│   ├── Dockerfile             production image (bakes NEXT_PUBLIC_API_BASE_URL)
│   └── AGENTS.md / README.md
├── backend/                   FastAPI app
│   ├── app/                   application code (api, auth, db, middleware, models, schemas, services, utils)
│   ├── alembic/versions/      13 migrations (0001…0013)
│   ├── tests/                 30 pytest files (445 test functions)
│   ├── postman/               auth contract collection
│   ├── scripts/               seeds + probes (seed_tarot, seed_palm_features, seed_roles, seed_consultants, create_admin, train_recommender…)
│   └── Dockerfile             production image (non-root appuser, /app/uploads)
├── data/                      curated reference catalogs (JSON): palmistry lines+mounts, RWS deck, 6 spreads, 64 recommendations, landmark schema
├── dataset/                   raw source data: "Hands and palm images dataset", palmline (YOLOv5 annotations), "Toroto card" (card imagery + meanings)
├── docs/
│   ├── decisions/             9 decision records (D-007…D-016)
│   ├── workflows/             core-user-journey, palm-analysis, tarot-reading, combined-intelligence (+README)
│   ├── wireframes/            9 wireframe specs (01-auth … 09-reports-export) + README
│   ├── deployment/aws-production.md
│   └── BOOKING_MODULE_PLAN.md
├── models/                    hand_landmarker.task (MediaPipe model asset)
├── scripts/                   verify_all.py, smoke_roles.py, verify_real_extraction.py, check_migrations.py, build_reference_data.py, backup_db.ps1, deploy_aws.ps1, run_with_watchdog.py, probe.js
├── tests/                     reserved for E2E/integration (README; e2e/ + integration/ planned)
├── uploads/                   runtime storage: avatars/, palm/
├── ai/                        AI artifact namespace (embeddings, interpretation, palm, personality, recommendations, tarot, trends)
├── docker-compose.yml         db + migrate + backend + frontend stack
├── run_dev_server.bat         dev backend runner (waits; logs to backend_dev_server.log)
├── check_neon.py              connectivity/table check script for a Neon-hosted Postgres
├── PALMISTRY_TAROT_AI_AGENT_SPEC.md   authoritative master spec (50 sections)
├── ARCHITECTURE.md            living architecture overview
├── README.md                  project overview + stack + prerequisites
├── CHANGELOG.md               versioned implementation history (detailed)
├── AGENT_PROGRESS.md          session-by-session implementation evidence
├── PROGRESS.md                living milestone/task status + decisions D-001…D-014
├── CLAUDE.md                  agent quick-reference (@AGENTS.md)
├── pytest-report.xml          partial pytest XML artifact (2026-10-11 snapshot)
└── .github/workflows/         ci.yml + deploy.yml
```

---

## 4. System Architecture `[DOC ARCHITECTURE.md + CODE]`

### 4.1 Overview

```text
Next.js frontend (React 19, Pages Router, Tailwind v4)      :3000 (dev) / :3001 (Compose)
        │  fetch + credentials:include · Bearer access token (in memory) · httpOnly refresh cookie
        ▼
FastAPI API Gateway / modular monolith                      :8000
  ├── /api/v1 router — versioned REST, JSON, uniform error envelope
  ├── middleware: RequestContext (X-Request-ID + access logs) · CORS · ErrorMonitoring · auth rate limiting
  ├── auth: Argon2id · JWT HS256 access tokens (30 min) · rotating DB-backed refresh tokens (14 d)
  │        with theft detection · Google OAuth2 adapter · RBAC dependencies
  └── services/: user · profile · palm_analysis · tarot · interpretation · personality · trends ·
                recommendations · notifications · analytics · reports · admin · booking · consultation ·
                reading · assistant · life_trends
        ▼
PostgreSQL 16 — transactional system of record (23 tables, Alembic migrations)      :5432
```

- OpenAPI at `/api/openapi.json`; Swagger UI at `/api/docs`.
- Lifespan startup: logging config + **both background schedulers** (notifications; booking) — idempotent `scheduler.running` guard `[CODE main.py]`.
- Spec §5 target architecture (microservices + Mongo/Redis/ES/Chroma/Neo4j/InfluxDB) is **not** the current implementation; the delivered system is a modular monolith on PostgreSQL (see §17).

### 4.2 Cross-cutting conventions

| Concern | Implementation |
|---|---|
| API prefix | `/api/v1` on every router `[SPEC §49.14]` |
| Error envelope | `{code, message, request_id}` (+ `fields` on 422 validation) — single `domain_error_handler` for 14 domain error classes (`[CODE main.py]`) |
| Error codes | e.g. `HTTP_<status>`, `VALIDATION_ERROR`, `INTERNAL_ERROR`, `OAUTH_NOT_CONFIGURED`, `GOAL_NOT_FOUND`, `AVATAR_TOO_LARGE`, `TAROT_UNKNOWN_CARD`, `RECOMMENDATION_TYPE_MISMATCH`, `GOAL_LIMIT_REACHED`… |
| Request tracing | `RequestContextMiddleware` assigns/propagates `X-Request-ID`; included in every error body; exported on CORS |
| Rate limiting | In-process fixed window (10 req/min per scope+IP) on auth scopes register/login/refresh (D-011); general 60 req/min defined in config `[SPEC §49.14]` |
| Monitoring | `ErrorMonitoringMiddleware` (outermost user middleware) records 5xx/401/403/429 into `error_logs` (deduplicated per kind+method+path+status+message with `occurrences` counter) + in-process latency ring buffer for `/admin/system/performance` |
| Auth model | Access token in frontend memory only; refresh token in `palmistry_refresh` httpOnly cookie (SameSite=Lax, Secure in prod; derived from request for cross-site deployments); silent session restore via refresh |
| Refresh token rotation | SHA-256-hashed rows; rotation on every refresh; **reuse of a rotated token revokes all of that user's sessions** (theft detection, D-008) |
| RBAC bundles | `require_user` · `require_tarot_reader` · `require_spiritual_consultant` · `require_admin` + session bundles `require_consultant_role` (reader+consultant, **not** admin) and `require_session_role` (seeker+reader+consultant) |
| Disclaimers | §49.19 safety disclaimer appears on all interpretation/insight surfaces (non-medical, non-financial, reflective-not-predictive) |

### 4.3 Frontend architecture `[CODE]`

- **Layout selection** in `pages/_app.js`: `/consultant` + `/consultant/*` → `ConsultantLayout`; `/admin` + `/admin/*` → `AdminLayout`; everything else → `MainLayout`.
- **Auth**: `hooks/useAuth.js` `AuthProvider` (refresh→user on mount; `{user, loading, login, register, refresh, logout}`); `services/api.js` central fetch client with single-flight refresh, `credentials: "include"`, error-envelope→`ApiError` mapping, FormData/`apiBlob` support.
- **Route guards**: `hooks/useRoleGuard.js` + `lib/roles.js` `pageAccess`/`STAFF_ONLY_PREFIXES` (`/consultant` → spiritual_consultant only, `/admin` → admin only); redirect to dashboard with `?blocked=<asPath>` notice; backend remains authoritative.
- **State/data**: `hooks/useAsyncData.js` for LOADING/EMPTY/ERROR/SUCCESS loads; per-domain service modules (16 files in `src/services/`).
- **UI kit**: `components/ui/` — Button (6 variants), Badge, Panel, PageHeader, States (EmptyState/ErrorState/InlineError/Spinner/Skeleton*), Toast (+ `useToast`, aria-live), ConfirmDialog (Esc-close), NotificationBell/Badge. Semantic tokens: `primary` violet (brand), `accent` tarot gold, emerald/slate/rose; `page-glow` backdrop; `fade-in`/`rise-in` animation tokens.

---

## 5. Database

### 5.1 Migration history (13 migrations) `[CODE backend/alembic/versions + DOC CHANGELOG]`

| # | File | Creates / changes |
|---|---|---|
| 0001 | `0001_auth_rbac_users_refresh_tokens.py` | `users` (UUID PK, lowercase unique email, native `user_role` enum, nullable password_hash for OAuth-only, unique google_id, is_active, UTC timestamps), `refresh_tokens` (SHA-256 token_hash unique, expires_at/revoked_at/rotated_from, FK cascade) |
| 0002 | `0002_profiles.py` | `profiles` (1:1 with users), `profile_interests` (unique per profile+interest, indexed), `profile_goals` (text ≤500, max 25/profile); backfilled existing users |
| 0003 | `0003_roles_data.py` | `readings` (JSONB result payloads), `consultations` (guidance threads), `audit_logs`; role data |
| 0004 | `0004_recommendations.py` | `recommendation_records` (UUID PK, type/status/scores/priority/payload), `recommendation_events` (shown/accepted/dismissed/completed/rated feedback stream) |
| 0005 | `0005_consultation_messages.py` | `consultation_messages` (per-thread seeker↔consultant messages) |
| 0006 | `0006_notifications.py` | `notifications` (in-app; `metadata` column), `notification_deliveries` (channel tracking) + `notification_type` enum |
| 0007 | `0007_booking.py` | Booking module (8 tables): expert/consultant profiles, availability_rules, availability_slots, bookings, booking_events, session_notes, session_feedbacks, calendar connections; extends `notification_type` with 6 booking values |
| 0008 | `0008_notification_event_types.py` | New notification event types (new_user, new_reading, new_question, insight_update…) |
| 0009 | `0009_rename_expert_to_consultant.py` | Pure rename: `expert_profiles`→`consultant_profiles`, `expert_id`→`consultant_id` everywhere, indexes/constraints renamed |
| 0010 | `0010_booking_proposals_and_chat.py` | `bookings.slot_id` nullable; adds `origin`, `last_proposed_by_id`; new `booking_messages` table (per-booking chat) |
| 0011 | `0011_error_logs.py` | `error_logs` (deduplicated monitoring records + occurrences counter) |
| 0012 | `0012_custom_spreads.py` | `custom_spreads` (reader-authored, 1–10 positions, private/shared visibility) |
| 0013 | `0013_remove_google_calendar.py` | Drops `consultant_calendar_connections` + booking calendar columns (`meet_code`, `google_event_id`, `google_calendar_id`, `calendar_sync_status`, `calendar_synced_at`, `calendar_error`); meeting links now shared manually |

### 5.2 Current table inventory (23 tables + `alembic_version`)

`users` · `refresh_tokens` · `profiles` · `profile_interests` · `profile_goals` · `readings` · `consultations` · `consultation_messages` · `audit_logs` · `recommendation_records` · `recommendation_events` · `notifications` · `notification_deliveries` · `consultant_profiles` · `availability_rules` · `availability_slots` · `bookings` · `booking_events` · `booking_messages` · `session_notes` · `session_feedbacks` · `error_logs` · `custom_spreads`

### 5.3 Schema properties `[CODE + DOC]`

- UUID primary keys and timezone-aware UTC timestamps throughout; native `user_role` enum; preference values stored as validated strings (data-driven catalogs, D-013 — no schema churn when catalogs grow).
- `bookings`: status flow `pending → accepted | rejected → completed | cancelled` (+ `countered` negotiation state) enforced by `ALLOWED_TRANSITIONS`; append-only `BookingEvent` audit trail; **partial unique index** (`status NOT IN ('cancelled','rejected')`) makes double-booking one slot impossible at DB level.
- `readings.result`: JSONB payload — full palm analysis JSON (landmarks, lines, mounts, shape, confidence) or tarot draw (cards, positions, interpretation synthesis).
- Databases: `palmistry` (dev) and `palmistry_test` (automated tests, Alembic-managed schema + per-test truncation).
- Model modules (12): `common`, `user`, `refresh_token`, `profile`, `reading`, `recommendation`, `notification`, `consultation`, `booking`, `custom_spread`, `error_log`.

## 6. Backend Modules — what each service actually does `[CODE]`

### 6.1 `app/auth/` — authentication & RBAC
- `password.py` — Argon2id hashing (`argon2-cffi`).
- `tokens.py` — JWT HS256 access tokens, 30-min expiry, claims `sub/role/type/iat/exp/jti` (PyJWT).
- `service.py` — register/login/authenticate; refresh-token issuing + rotation; **theft detection**: reuse of a revoked token revokes ALL sessions of that user (D-008).
- `cookies.py` — sets/clears the httpOnly `palmistry_refresh` cookie; `Secure`/`SameSite` derived from the incoming request (cross-site deploy support — latest commit "Derive refresh-cookie Secure/SameSite from the request").
- `rbac.py` — `get_current_user` + `require_roles(*roles)` dependency factory and all rule bundles (§4.2).
- `oauth/google.py` — Google OAuth2 adapter (authlib); returns `503 OAUTH_NOT_CONFIGURED` until credentials are configured (D-010).

### 6.2 `app/services/palm_analysis/` — palm computer vision
Pipeline `analyze_palm_image()` (`pipeline.py`), engine name **"MediaPipe HandLandmarker + OpenCV Crease Pipeline" v1.0.0**:
1. **Preprocess & validate** (`preprocessor.py`) — JPG/PNG/WEBP validation, orientation correction, resize, RGB conversion, denoising, contrast normalization (CLAHE), crease map; raises `PalmValidationError` (non-palm/empty/dorsal images rejected).
2. **Hand landmarks** (`hand_landmarker.py`) — MediaPipe HandLandmarker task (`models/hand_landmarker.task`) → 21 landmarks + handedness + palmar-orientation check.
3. **Palm shape** (`feature_extractor.py`) — elemental hand type (Fire/Earth/Air/Water) from width/height/aspect + finger-to-palm ratio; description + traits.
4. **Finger structure** — 2D:4D digit ratio + interpretation, pinky-reaches-ring-DIP trait, thumb angle + flexibility, per-finger lengths and ratios.
5. **Mounts** — 6 classical mounts (Jupiter, Saturn, Apollo, Mercury, Venus, Moon) with prominence + score from crease/CLAH evidence; center coordinates; meanings + core attributes.
6. **Line detection** (`line_detector.py`) — the 5 primary lines (Life, Head, Heart, Fate, Sun) with `detected`, `confidence`, `length_normalized`, `curvature`, `depth_clarity`, `continuity`, `variation_type` + description, and classical interpretation text; line coordinate polylines (used by the frontend SVG overlay).
7. **Overall confidence** = `mean(line confidences)·0.6 + mean(mount scores)·0.2 + handedness confidence·0.2` (rounded 2 dp) — kept in the analysis metadata together with model name/version/timestamp and original/analyzed resolutions.
- `catalog.py` — reference catalogs for interpretation; output is persisted as `readings.result` JSONB; source image stored at `uploads/palm/<reading_id>.img`.

### 6.3 `app/services/tarot/` — tarot engine
- `catalog.py` — loads the **78-card Rider-Waite-Smith deck** (upright + reversed meanings, keywords, arcana/suit/element) and the **6 standard spreads** (Single, Three Card, Relationship, Career, Celtic Cross, Life Path) from `data/tarot/*.json`.
- `interpretation.py` — rule-based, position-aware and orientation-aware engine:
  - per-card synthesis from catalog meanings + keywords + per-domain guidance (love/career/spiritual selected from spread category or question text);
  - spread analytics: **arcana balance** (Major/Minor), **classical elemental balance** (dominant + missing Fire/Water/Air/Earth), **reversal analysis**, **repeating numerology** with traditional number meanings;
  - composed narrative (opening → per-position body → closing synthesis + one-line summary), actionable guidance lines, §49.19 disclaimer, and metadata (engine/model name + version, UTC timestamp, data-completeness relevance score);
  - draw path uses **cryptographically secure Fisher-Yates**; deterministic seeds supported for tests (FR-013).
- `custom_spreads.py` — reader-authored spreads (1–10 positions, each with its own meaning); `to_definition()` converts them to the exact standard shape so they run through the **same interpretation engine** via `spread_override` (no special case).

### 6.4 `app/services/interpretation/` — AI interpretation engine
- `engine.py` — generates palm/tarot interpretations + guidance (FR-017…FR-021), `InterpretationError`, shared safety disclaimer constant.
- `llm_adapter.py` — `LLMAdapter` v1.0.0; provider order **OpenAI → Groq → deterministic rule engine** (`rulebook-1.0.0`); every response records provider/model/tokens/`rule_based` flag; LLM responses are validated against structured schemas before persistence (§49.7).
- Endpoints also expose `/interpretation/chat` and `/interpretation/synthesize` (combined palm+tarot synthesis).

### 6.5 `app/services/personality/` — Personality Intelligence (FR-022…FR-026)
- `PersonalityIntelligenceEngine` v1.0.0 — builds a personality profile from the latest completed palm reading (+ tarot when present): strengths, growth areas, behavioral insights, domain guidance.
- Element→trait model (Fire: courage/initiative…; Water: empathy/intuition…; Air: analytical/communication…; Earth: reliability/practicality…), trait→dimension mapping for behavioral insights, line-variation heuristics (strong vs faint line slugs from the CV detector).
- Optional LLM enrichment; deterministic fallback. Endpoints: `POST /personality/profile`, `POST /personality/enrich`.
- Safety: "interpretive guidance for self-reflection and entertainment only — not psychological diagnosis…" (§49.19).

### 6.6 `app/services/trends/engine.py` + `life_trends.py` — Life Trend Analysis (FR-027…FR-031)
- `LifeTrendEngine` v1.0.0, method `feature_based_trend_scoring` — transparent, **unsupervised** trend analysis over the user's stored reading history:
  1. per-reading 0–1 signals extracted from `Reading.result` JSONB (palm line strengths, mount/shape elements, digit ratio; tarot arcana/suit/court ratios, domain focus, relevance scores);
  2. **recency-weighted aggregation** (90-day half-life) into 6 life domains: career, relationships, emotional, growth, vitality, creativity;
  3. **direction** (rising/stable/declining) from recent-half vs older-half delta; **strength** = evidence amount × coverage; **confidence** = readings analyzed × coverage;
  4. growth-potential composite, life-path summary, opportunities + challenges each with **per-item signal attribution** (e.g. "Heart line depth & clarity: 0.72 avg across 3 readings") and a per-reading trend-history series for charting;
  5. profile goals/interests keyword-align to domains as self-declared focus signals (+0.075 per matched text, capped 0.15);
  6. `feature_vector` in every response (flattened domain scores/strengths/momentum + raw per-reading signal series) — the intended training shape for a *future* supervised forecasting model.
- Deliberately **no supervised-ML accuracy claims** (no ground-truth life outcomes exist); fixed domain weights are documented interpretation choices, not learned parameters.
- `life_trends.py` orchestrator — optional LLM pass may rephrase only the explanation paragraph around computed facts; scores are **never** LLM-generated; deterministic text on failure.
- Endpoint: `GET /life-trends`.

### 6.7 `app/services/recommendations/` — recommendation engine
- `engine.py` — `LLMRecommendationEngine` v2.0.0: ranking + content generation through the shared LLM adapter; recent feedback (last 30 accepted/dismissed/completed/rated events) summarized into the prompt and applied as signed item scores in the dependency-free heuristic fallback ranker.
- Score schema: `context_relevance`, `personalization`, `goal_alignment`, `blended` (mean of the three, also `confidence`).
- Tarot is a first-class source: `tarot_reading_id`/`tarot_data` alone is accepted (palm no longer mandatory); a tarot-only personality profile is synthesized from the cards' elemental balance.
- 64-item catalog (`data/recommendations/recommendations_catalog.json`) across 5 types (personal growth 19, relationship 12, career 11, goal alignment 11, spiritual development 11) — prompt grounding + fallback source.
- `metadata.generation_method` honestly reports `llm` vs `heuristic_fallback`.
- `service.py` — context assembly (profile goals/interests, palm elementals, tarot profile, personality strengths/weaknesses, behavioral insights, reading history), persistence (`recommendation_records`), feedback events (`recommendation_events`), metrics.
- Endpoints: `POST /recommendations/generate` · `GET /recommendations/me` · `GET /recommendations/metrics` · `PATCH /recommendations/{id}/feedback`.

### 6.8 `app/services/assistant/` — grounded dashboard AI assistant
- `context.py` — one role-scoped snapshot builder per role, each reusing the services that role's dashboard already calls (so the assistant can **never** reach data the role could not read): seeker → own readings/recommendations/guidance threads; reader → platform reading queue; consultant → guidance queue + responsiveness; admin → platform growth, engagement, role mix, audit trail + AI provider state. Snapshot = `metrics` (the only numbers the model may quote), `highlights`, `suggested_questions`, `scope`, `headline`, disclaimer.
- `chat.py` — the snapshot is serialized into the system prompt as an explicit fact list with hard rules: quote only supplied numbers, never invent readings/users/threads/dates, answer compactly, close with the disclaimer verbatim; `intent:"overview"` uses a fixed analysis prompt (headline → three signals → one gap → next action); history trimmed to last 12 turns; every returned turn is **server-stamped** (client timestamps dropped). Falls back to a deterministic rule engine when no LLM credentials exist.
- Endpoints: `GET /assistant/context` · `POST /assistant/chat`.

### 6.9 `app/services/notifications/` — notification & engagement system (FR-039)
- `service.py` — create/list/mark-read/mark-all-read/unread-count/preferences.
- `scheduler.py` — APScheduler jobs: **daily guidance at 8:00**, reading reminders (based on last reading), admin announcements fanout; idempotent job registration (`replace_existing=True` + running guard).
- Event-driven creation (isolated DB session, fully failure-tolerant — a notification can never break or roll back the triggering request): new user registers → admins; new palm/tarot analysis → owner (`reading_completed`) + staff (`new_reading`); consultation question → consultants; consultant reply → seeker.
- Types include `daily_guidance`, `reading_reminder`, `insight_update`, `growth_alert`, `platform_announcement`, `reading_completed`, plus booking categories.
- **Current channel: in-app only** — the email service and templates were removed; preferences persist per profile flags (`notify_insights`, `notify_growth`, `notify_announcements`, …). SMS never configured.
- Frontend: header bell with unread badge + dropdown (poll unread-count, per-item + mark-all-read) wired for every signed-in role; `/notifications` center with filters + preference toggles.

### 6.10 `app/services/booking/` — live consultation & booking module
- `service.py` — consultant profile CRUD, availability management, booking lifecycle with **cancellation windows**, consultant session notes (private ⇄ shared with seeker), seeker feedback (1–5 stars + review, unique per booking, recomputes `avg_rating`/`review_count`).
- `availability.py` — consultants describe their week with recurring `AvailabilityRule` rows; `materialise_rule` expands them into concrete UTC `AvailabilitySlot` rows **21 days ahead**, interpreting wall-clock times in the rule's own timezone per date (DST-correct); a scheduler job rolls the horizon forward daily at 1:00.
- `scheduler.py` — reminders at **24 h and 1 h** lead times (idempotent via `reminder_sent_at`/`short_reminder_sent_at` + keys), availability rollout, auto-completion of ended sessions (unlocks feedback).
- `notifications.py` — booking events ride the existing in-app notification channel (visible in the header bell for every role).
- Flow: `pending → accepted | rejected → completed | cancelled`, plus **`countered`** negotiation state — either party can counter-propose until both agree; seekers can also propose a custom time (hybrid with published slots, `origin="proposal"`).
- Per-booking chat: direct seeker↔consultant thread (`booking_messages`) visible only to that booking's parties + admins.
- Meeting links: **manual Google Meet link sharing** (calendar auto-integration was removed in migration 0013); either party can paste the link; "Join Google Meet" unlocks 30 minutes before start.
- API: 42 handlers across `/consultants`, `/consultants/me/...`, `/bookings` (directory, profiles, rules, slots, requests, counter, confirm, cancel, messages, notes, feedback, reviews, meeting link, stats).
- Frontend: `/consultants` directory (search/specialisation/price filters), `/consultants/[id]` profile + day-strip slot picker + booking form, `/sessions` seeker hub, `/consultant-studio` consultant console; `SeekerSessionsPanel` on the seeker dashboard, `ConsultantSessionsPanel` on reader + consultant dashboards.

### 6.11 `app/services/consultation/` — guidance consultations (FR-037)
- Seeker side: create/list guidance threads + messaging (`/consultations`, `/consultations/{id}/messages`).
- Consultant side (`/consultant/*` router): guidance queue, dispatch guidance, effectiveness breakdown, client trend analysis, consultation insights, and the **live client roster** (`GET /consultant/clients` folds the guidance queue with real `profiles`/interests/goals + reading counts).
- Goal-progress panel pairs each client goal with that client's real reading/thread activity (no invented completion scores).

### 6.12 `app/services/reading/` — reading lifecycle
- Create palm reading (runs the real CV pipeline, persists analysis JSON + source image, status `completed`), create tarot reading (runs interpretation engine, stores cards + full synthesis in `result.interpretation`).
- List with type/status filters + pagination; get with access matrix **owner / tarot_reader / admin**; PATCH owner notes/title; DELETE; `GET /readings/analytics/me` (totals by status/type/day).

### 6.13 `app/services/reports/` — reports & export (FR-057/058/062/063)
- `generator.py` — normalizes palmistry reports (FR-057: elemental hand type, finger ratios, 5-line metrics, 6-mount prominence, §49.9-style confidence label) and tarot reports (FR-058: spread overview, orientations, position meanings, elemental/arcana synthesis, core guidance); injects the mandatory §49.19 disclaimer + engine/version/timestamp metadata.
- `pdf_exporter.py` — ReportLab; mystical dark/gold multi-page dossier: styled cover, metric tables, narrative interpretation, domain guidance, boxed safety disclaimer; streamed as `application/pdf` attachment.
- `excel_exporter.py` — openpyxl; 3-sheet workbook: Overview / Analysis Details / Guidance & Actions; streamed as `.xlsx`.
- Endpoints: `GET /reports/reading/{id}` (JSON) · `/pdf` · `/excel` — gated to owner/reader/consultant/admin. (D-016: in-process streamed exports.)

### 6.14 `app/services/admin/service.py` — admin console backend
- Platform analytics, reading statistics, **read-only session oversight** (aggregates + next scheduled sessions with consultant/time/duration — no action buttons anywhere; admins intentionally cannot host or book).
- User governance (list/update/role assignment), audit logs.
- **Live RBAC permission matrix** (`GET /admin/permissions`) — documents the real `require_*` bundles + drift check.
- Authentication settings (`/admin/settings/auth`) — token policy, cookie, OAuth readiness, admin self-signup policy, rate limits; **secrets only as presence flags**.
- System configuration & release (`/admin/settings/system`) — environment, version, API prefix, DB target, Alembic revision, AI provider/model, upload limits, scheduler registration, uptime.
- Error & security monitor (`/admin/errors`, `/errors/stats`, `POST /errors/{id}/acknowledge` — audited, never destructive) backed by the `error_logs` table + middleware.
- Performance (`/admin/system/performance`) — in-process latency percentiles + slowest routes (process-local by design; the panel says so).

### 6.15 Namespace-only packages
`app/services/analytics/` and `app/services/user/` currently contain only `__init__.py` — platform analytics live in the admin service and reading fixtures (documented here so nobody assumes a hidden module).

---

## 7. API Surface — 138 route handlers across 18 modules `[CODE]`

All routes under **`/api/v1`** (OpenAPI: `/api/openapi.json`, docs: `/api/docs`). Auth = Bearer access token unless stated. Counts measured 2026-10-16 by source scan.

| Module | Count | Key endpoints / scope | Access |
|---|---|---|---|
| `health` | 1 | `GET /health` (DB-checked, used by Docker healthcheck) | public |
| `auth` | 7 | `POST /auth/register` 201 · `/auth/login` · `/auth/refresh` (rotation) · `/auth/logout` 204 · `GET /auth/me` · `GET /auth/google/authorize` · `/auth/google/callback` | public + Bearer |
| `portals` | 2 | `POST /auth/{portal}/register` · `/auth/{portal}/login` for portals `user / tarot-reader / spiritual-consultant / admin` (admin registration needs invite code) | public, rate-limited |
| `profile` | 10 | `GET/PATCH /profile` · `PUT /profile/interests` · `GET/POST /profile/goals` · `PATCH/DELETE /profile/goals/{id}` · `PUT/DELETE/GET /profile/avatar` (ETag/304) | owner |
| `palm` | 4 | `POST /palm/analyze` (CV pipeline) · `GET /palm/lines` · `GET /palm/mounts` (catalogs) · `POST /palm/check-frame` (webcam pre-check) | per endpoint |
| `tarot` | 5 | `GET /tarot/shuffle` (FR-013, seedable) · `/tarot/decks` · `/tarot/spreads` · `POST /tarot/draw` (persists for signed-in) · `POST /tarot/interpret` (explicit selection) | guest-capable, persists when authed |
| `readings` | 10 | `POST /readings/palm` 201 · `/readings/tarot` 201 · `GET /readings` (type/status filters + pagination) · `GET/PATCH/DELETE /readings/{id}` · `GET /readings/analytics/me` · + reader-router additions (staff queue / review-certification) | owner / staff matrix |
| `reports` | 3 | `GET /reports/reading/{id}` · `/pdf` · `/excel` | owner / reader / consultant / admin |
| `interpretation` | 4 | `POST /interpretation/palm` · `/tarot` · `/chat` · `/synthesize` (combined intelligence) | authenticated |
| `personality` | 2 | `POST /personality/profile` · `/personality/enrich` | authenticated |
| `life-trends` | 1 | `GET /life-trends` | authenticated |
| `recommendations` | 4 | `POST /recommendations/generate` · `GET /me` · `GET /metrics` · `PATCH /{id}/feedback` | authenticated |
| `assistant` | 2 | `GET /assistant/context` · `POST /assistant/chat` | authenticated (role-scoped) |
| `notifications` | 8 | `GET /notifications` · `/unread-count` · `PATCH /{id}/read` · `PATCH /read-all` · `GET/PUT /preferences` · `POST/GET /admin/announcements` (admin) | authenticated |
| `consultations` | 10 | seeker: `POST/GET /consultations`, `GET/POST /{id}/messages`; consultant router: queue, guidance dispatch, insights/effectiveness/trends, `GET /consultant/clients` | seeker / spiritual_consultant |
| `reader` | 6 | `GET /reader/spreads` (+ standard+custom) · `POST/PATCH/DELETE /reader/spreads...` · `GET /reader/reports` (filters; owner email, spread, review state) · `GET /reader/engagement` | tarot_reader |
| `admin` | 17 | users · analytics (+sessions oversight) · reading statistics · audit logs · permissions · settings/auth · settings/system · reports · errors (+stats, acknowledge) · performance | admin |
| `booking` | 42 | `/consultants` directory + profiles + availability rules/slots + propose · `/consultants/me/...` studio (bookings queue, accept/reject/counter, notes, meeting link, slot generation) · `/bookings` seeker hub (create, upcoming/past, cancel, counter, confirm, `messages`, feedback) | seeker / reader / consultant (never admin) |

Conventions: uniform error envelope (§4.2); 422 validation errors include `fields`; auth endpoints rate-limited 10/min per scope+IP; general limit 60/min/user per spec §49.14.

---

## 8. Frontend — routes, components, services `[CODE]`

### 8.1 Route map — 34 pages (33 application routes + custom 404), 36 page files incl. `_app`/`_document`

| Space | Route | Purpose |
|---|---|---|
| Public | `/` | Landing (platform intro, status, CTAs) |
| Public | `/login` · `/login/[role]` | Sign-in + per-role portals |
| Public | `/register` · `/register/[role]` | Registration + per-role portals (WF-01 states, password strength meter, Google button) |
| Seeker | `/dashboard` | Role-aware dashboard (readings, insights, recommendations, assistant, panels; role switcher) |
| Seeker | `/readings` | Reading hub — filter tabs (All/Palmistry/Tarot), search, per-card View/PDF/Excel/Delete |
| Seeker | `/readings/palm` | Palm upload + webcam auto-capture + CV result screen + AI insights + export |
| Seeker | `/readings/tarot` | Interactive draw ritual (spread → shuffle → pick → reveal → interpretation) |
| Seeker | `/readings/[id]` | Reading detail viewer (palm metrics or tarot spread layout, notes, exports, disclaimer) |
| Seeker | `/personality` | Full personality profile surface |
| Seeker | `/life-trends` | Life trend dashboard (domains, opportunities/challenges, trend-over-time chart) |
| Seeker | `/profile` | WF-02 profile: avatar, identity, interests chips, goals CRUD, reading preferences, notification toggles, session history |
| Seeker | `/notifications` | Notification center (filters, preferences, mark-all-read) |
| Seeker | `/consultants` · `/consultants/[consultantId]` | Consultant directory + public profile, availability day-strip, booking form, propose-a-time |
| Seeker | `/sessions` | Seeker session hub (upcoming/past, Join Meet, cancel, feedback, notes, history) |
| Reader | `/reader/spreads` | Spread Studio — ordered position editor, reorder, rename, visibility, retire |
| Reader | `/reader/reports` | Reading report management — filters + PDF/Excel export + one-click certification |
| Consultant | `/consultant` (→ dashboard) · `/consultant/dashboard` | Consultant console dashboard (stat cards, client trend chart, upcoming consultations, guidance queue) |
| Consultant | `/consultant/clients` · `/consultant/clients/[clientId]` | Live client roster + client detail (overview meters, palm summary, tarot history, AI insights, notes, goal progress) |
| Consultant | `/consultant/consultations` · `/consultant/consultations/[consultationId]` | Consultation list + three-column workspace (6 tabs + summary rail) |
| Consultant | `/consultant/insights` | Guidance effectiveness breakdown + consultation insights (charts) |
| Consultant | `/consultant/reports` | Consultation reports table (filters, PDF download, share) |
| Consultant | `/consultant-studio` | Booking console (profile editor, availability rules + slot manager, requests, sessions, notes, meeting links) |
| Admin | `/admin` · `/admin/users` · `/admin/analytics` · `/admin/security` · `/admin/system` | Overview, user governance, platform analytics, security & errors, system config — own shell `AdminLayout` |
| Utility | `/404` | Styled not-found page |

### 8.2 Components — 67 files in 12 groups `[CODE]`

| Group | Files | Notable |
|---|---|---|
| `ui/` (11) | Button, Badge, Panel, PageHeader, States, Toast, ConfirmDialog, NotificationBell, NotificationBadge, BellIcon, index | The shared kit; single source for interactive chrome |
| `dashboards/` (9) | UserDashboard, ReaderDashboard, ConsultantDashboard, AdminDashboard, LifeTrendDashboard, PersonalityInsightsCard, DashboardAssistant, ConsultationThread, shared (StatCard, MeterBar, PerDayBars, Segmented) | Role dashboards + assistant panel |
| `palm/` (3) | CameraCaptureModal, PalmVisualizer, PalmAnalysisDetails | Auto-capture webcam (hand presence, skin-density, exposure, Laplacian sharpness; auto shutter + progress ring; Auto ON/OFF); SVG line overlay on the photo (Life emerald, Head sky, Heart rose, Fate violet, Sun amber) with layer toggles + hover sync |
| `tarot/` (4) | ShuffleAnimation, CardSelection, CardReveal, ReadingAnalysisPanel | Spread geometry from `layout_coordinate` (Celtic Cross crossing card rotated 90°), 180° reversed cards + orientation badges, card backs pre-draw |
| `consultant/` (16) | ClientTrendChart, UpcomingConsultations, RecentClients, ClientOverview, ClientDirectory, PalmAnalysisSummary, TarotHistoryTable, AIInsightCard, GuidanceEffectiveness, ConsultationInsights, ConsultationWorkspace, GoalProgressPanel, ConsultantNotes, StartConsultationDialog, ConsultationReportsTable, shared | full FR-037 console surface |
| `admin/` (6) | UserGovernancePanel, AnalyticsPanels, SessionOversightPanel, SecurityMonitor, AuditLogPanel, SystemPanels | console panels |
| `booking/` (5) | SeekerSessionsPanel, ConsultantSessionsPanel, BookingChat, TimeProposalForm, shared (SessionCard, ConsultantCard, SlotPicker, RatingStars, FeedbackForm, BookingTimeline) | booking surfaces |
| `reader/` (3) | SpreadStudio, ReadingReportsTable, ReaderEngagementPanel | reader workspace |
| `ai/` (4) | AiInsightsPanel (shared AI section), ChatBot, LoadingSpinner, ChartToggle | one implementation of the AI block used by palm/tarot/detail pages |
| `recommendations/` (2) | RecommendationsSection, RecommendationCard | generate + feedback + score breakdown |
| `life-trends/` (1) | shared | trend widgets |
| root (3) | BackendStatus, PortalAuthForm, icons.js | status pill; role portal form; 40+ icon set |

### 8.3 Services, hooks, layouts, lib `[CODE]`

- `services/` (16): `api.js` (single-flight refresh client) · `auth.js` · `profile.js` · `palm.js` · `tarot.js` · `readings.js` · `reports.js` (blob download) · `recommendations.js` · `personality.js` · `notifications.js` · `consultant.js` (+ `consultantDemoData.js` labelled demo dataset) · `booking.js` · `reader.js` · `assistant.js` · `roles.js`.
- `hooks/` (3): `useAuth` (silent session restore), `useRoleGuard` (seeker pages + staff prefixes incl. dynamic patterns, `?blocked=` redirect notices), `useAsyncData` (canonical async states).
- `layouts/` (3): `MainLayout` (public+seeker), `ConsultantLayout` (own sidebar/header shell, responsive drawer), `AdminLayout` (governance shell).
- `lib/` (5): `roles.js` (role labels/badges/icons/CTAs registry + `pageAccess` + `STAFF_ONLY_PREFIXES`), `chartjs.js` (chart.js registration + line/bar presets), `datetime.js` (native Date/Intl helpers, `canJoinMeet` 30-min window), `format.js` (initials/relative dates/percent/greeting), `pdf.js` (dependency-free fallback PDF writer for consultation reports not attached to a reading).
- Design system: semantic tokens in `styles/globals.css` (`primary` violet, `accent` gold, emerald/slate/rose, fade-in/rise-in animations, `page-glow`); Inter + Fraunces; consistent `rounded-3xl` cards; one primary CTA per view; visible focus rings; all pages implement LOADING/EMPTY/ERROR/SUCCESS; "no fabricated UI data" policy (removed length-derived charts; honest request-lifecycle loading states).

## 9. Features by Role (as documented & verified) `[DOC README/AGENT_PROGRESS + CODE]`

### 9.1 Seeker (`user`)
- Registration/login: email + password, Google OAuth adapter, per-role portals (`/login/user`, `/register/user`), silent session restore, password strength meter, Google button (WF-01 states: loading/error/429 banners, inline field errors).
- Profile: avatar upload/change/remove (blob rendering), identity (name + age group, syncs the nav via `reloadUser`), interests chips with live counter, goals CRUD (inline edit, 25 cap), reading preferences (deck / spread / tone, immediate save), notification toggles, session-history preview.
- Palm reading: upload **or** webcam auto-capture; full CV analysis (lines, mounts, shape, finger ratios); interactive SVG line overlay synchronized with the detail cards; AI interpretation section; PDF/Excel export; saved to history.
- Tarot reading: deck info, 6 spreads with geometric layout rendering, card backs → pick → reveal, reversals with orientation badges, per-card + synthesis interpretation, guidance, disclaimer, engine metadata; auto-persisted for signed-in users.
- Readings hub + detail: filter tabs, search, per-reading View/PDF/Excel/Delete; detail viewer with confidence bars, mount prominence, spread layout, notes editor, disclaimer.
- Personality insights, life-trend dashboard (6 domains, opportunities/challenges, trend chart when ≥2 readings exist), personalized recommendations with accept/dismiss/complete/rate feedback.
- Notifications: header bell + unread badge + dropdown; center with filters and preferences; daily guidance + reading reminders from the scheduler.
- Consultations: guidance threads with a spiritual consultant (create thread, message, receive replies).
- Booking: consultant directory (search/spec/price filters), public profile + availability day-strip + slot picker, or propose a custom time; negotiation via counter-proposals; per-booking chat; cancel within policy; Join Google Meet within 30 min; session notes; 1–5-star feedback after completion.
- Dashboard: date-range metrics, recent readings/recommendations, panel set, grounded AI assistant ("Overall analysis" + free-text questions).

### 9.2 Tarot Reader (`tarot_reader`)
- Reading oversight: platform queue + **certification** of readings (review endpoint, one-click from the reports table).
- Reading report management (`/reader/reports`): every platform reading with owner email, spread name, card count, review state; filters by type/status/review state/owner/title; PDF + Excel export.
- Engagement insights (`/reader/engagement`): distinct / returning / first-time querents, readings per querent, review coverage, top querents, most-drawn spreads — derived from existing tables, no invented metrics.
- Spread Studio (`/reader/spreads`): author custom 1–10-position spreads with per-position meanings, reorder, rename, description, private/shared visibility, retire; custom spreads run through the same interpretation engine.
- Live sessions: accept/reject/counter bookings, session notes (private/shared), meeting link, auto-completion → seeker feedback recomputes ratings.
- Notifications on new readings/questions via the shared channel.

### 9.3 Spiritual Consultant (`spiritual_consultant`)
- Console (`/consultant/*`) with dedicated shell: dashboard (stat cards, interactive client trend analysis with chart.js, upcoming consultations, recent clients, live guidance queue).
- Guidance queue + dispatch; effectiveness breakdown; consultation insights (line + bar charts).
- Live client roster (real seekers from guidance threads + interests/goals/reading counts) and client detail: overview score meters, palm analysis summary, tarot history, AI insight cards (portions labelled **demo data** — see §17), consultation history, private notes, goal-progress panel driven by real activity.
- Consultation workspace: three-column shell (client info · 6-tab work surface · summary rail); guided start-consultation flow that **requires an explicit "I have reviewed these insights" acknowledgement** and human-written guidance text before save.
- Reports page (filters, PDF download, share). Data-honesty badges: every payload labelled `live` / `demo` / `local`.
- Live sessions: same booking powers as readers.

### 9.4 Administrator (`admin`)
- Governance: user list/search/role assignment (`/admin/users`), audit logs.
- Platform analytics (+ reading statistics) and **read-only session oversight** — aggregated counts (by status, upcoming confirmed, pending requests, profiles, avg rating, unique seekers) + next scheduled sessions; no booking or hosting access anywhere (deliberate §49.3 alignment).
- Security & errors: error/security log with dedup counter, stats, acknowledge (audited); rate-limit/401/403/5xx capture via middleware.
- System: configuration & release info (env, version, Alembic revision, AI provider, upload limits, scheduler jobs, uptime), auth settings (presence flags only), live RBAC permission matrix with drift check, performance percentiles, announcements fanout.

---

## 10. Specification → Implementation Mapping & Key Formulas

### 10.1 Spec modules (§8) → delivery

| Spec module | Implemented as | Evidence |
|---|---|---|
| M1 Auth & RBAC | `app/auth` + endpoints | 45-test auth snapshot; §49.3 bundles live |
| M2 Profile management | `app/services/profile` + `/profile` | 85-test snapshot incl. 40 profile tests |
| M3 Palm Analysis Engine | `app/services/palm_analysis` pipeline v1.0.0 | real-CV reading tests; live smoke |
| M4 Tarot Reading Engine | `app/services/tarot` | engine v0.x rule-based; 20 tarot tests; 6 spreads |
| M5 AI Interpretation Engine | `app/services/interpretation` | adapter + endpoint tests; LLM live-verified with Groq |
| M6 Personality Intelligence | `app/services/personality` | personality test suite; dashboard card |
| M7 Life Trend Analysis | `app/services/trends` + `life_trends.py` | 12 engine/orchestrator/endpoint tests; user-specific outputs live-verified |
| M8 Spiritual Guidance Scoring | consultant effectiveness/insights + interpretation scoring metadata; **no single composite score** (see §17) | consultation insight tests |
| M9 Recommendation Engine | `app/services/recommendations` v2.0.0 | 53 recommendation tests; 270/270 suite snapshot |
| M10 Dashboards & Analytics | 4 role dashboards + admin analytics + reading analytics | console builds live-verified |
| M11 Notification & Engagement | `app/services/notifications` | bell/center wired; scheduler idempotency fix |
| M12 Reports & Export | `app/services/reports` (PDF/Excel/JSON) | 8 report tests incl. `%PDF-` and `PK` magic bytes |
| M13 Integration, Testing & Deployment | CI + Compose + AWS runbook + docs | ci.yml 3 jobs; smoke scripts |

### 10.2 Formula / algorithm quick reference
- **Palm overall confidence** = 0.6·mean(line confidences) + 0.2·mean(mount scores) + 0.2·handedness confidence.
- **Life trend direction** = sign of (recent-half mean − older-half mean); aggregation recency weight = **90-day half-life**; goal boost = +0.075 per matched goal/interest keyword, capped 0.15.
- **Recommendation blended score** = mean(`context_relevance`, `personalization`, `goal_alignment`) — also used as confidence.
- **Tarot draw** = cryptographically secure Fisher-Yates (seedable for tests).
- **Spec §49.9 Overall Insight Score** (0.30 palm + 0.25 tarot + 0.20 personality + 0.15 context + 0.10 consistency; labels Low/Moderate/High/Very High) — specified in the master contract; **not found as a single composite in the codebase** (verified by search 2026-10-16). Component-level scores exist (palm `overall_confidence`, tarot relevance, interpretation metadata). Honest gap — see §17.
- Every engine reports metadata: model/engine name + version + UTC timestamp (+ relevance/data-completeness where applicable) per spec "rule 11".

### 10.3 Data-honesty principles enforced in the product
- `source: "live" | "demo" | "local"` badge on consultant payloads; demo dataset isolated in `services/consultantDemoData.js` and labelled in UI.
- No fabricated charts: previous length-derived/random UI data removed (v0.12.0); loading states reflect real request lifecycle.
- `metadata.generation_method` reports `llm` vs `heuristic_fallback`; assistant may quote only snapshot numbers.
- §49.19 disclaimer on every interpretive surface; AI guidance never auto-finalised (explicit acknowledgement + human-authored guidance text required).
- Docs policy: "Never claim a feature is implemented unless it actually exists" (spec §40.1 #14) and "record measured results rather than claiming unmeasured performance" (§37.15). No benchmark numbers are published in the repo.

---

## 11. Security & Safety Posture `[CODE + DOC]`

| Area | Implementation |
|---|---|
| Password storage | Argon2id (`argon2-cffi`) |
| Access tokens | JWT HS256, 30-min TTL, claims `sub/role/type/iat/exp/jti`, held in frontend memory only |
| Refresh tokens | Opaque 256-bit, SHA-256-hashed in DB, rotating, 14-day TTL; **reuse detection revokes all user sessions**; httpOnly cookie (`palmistry_refresh`), SameSite=Lax / Secure in prod, cross-site derivation for split deployments |
| OAuth | Google via authlib adapter; disabled state returns clean `503 OAUTH_NOT_CONFIGURED` instead of failing |
| RBAC | Server-enforced dependency bundles for all four roles + session bundles; route-level frontend guards are supplementary; admin excluded from booking/consulting by design; per-role portals validate expected role at login |
| Rate limiting | Fixed-window per scope+IP on register/login/refresh (10/min); returns 429 with the standard envelope |
| Error handling | Uniform `{code, message, request_id}`; validation errors list `fields`; unhandled exceptions return generic 500 (no internals leaked); every response traced by `X-Request-ID` |
| Security monitoring | `ErrorMonitoringMiddleware` records 5xx / 401 / 403 / 429 to `error_logs` (dedup + occurrences), admin acknowledge flow (audited, non-destructive) |
| Upload validation | Magic-byte validation (JPG/PNG/WEBP); avatars ≤ 5 MB (`413 AVATAR_TOO_LARGE`, wrong type `415`); general upload cap 10 MB (§49.4); avatars stored `uploads/avatars/<profile_id>.<ext>` with old-file cleanup and Bearer-gated ETag/304 serving; palm images stored server-side under `uploads/palm/` |
| Secrets hygiene | `.env.example` placeholders only; settings endpoints expose presence flags, never values; production guard for `DEBUG` in `config.py` |
| CORS | Explicit origin allowlist (`CORS_ORIGINS`), credentials on, only `X-Request-ID` exposed |
| CI gates | Migration check + full pytest on push/PR before anything ships; frontend lint + production build gate |
| Safety / ethics | §49.19 disclaimers: non-diagnostic health, non-guaranteed financial, reflective-not-predictive trends, no fear-based claims; consultant workflow never auto-finalises AI text |
| Backups | `scripts/backup_db.ps1` (pg_dump); automated scheduling + DR documented as deployment-time tasks (AWS runbook) |

---

## 12. Testing & Verification

### 12.1 Static inventory (measured 2026-10-16) `[CODE]`

| Item | Value |
|---|---|
| Test files | 30 (`backend/tests/`: 28 `test_*.py` + `conftest.py` + `__init__.py`) |
| Test functions | **445** |
| Test code | 8,112 lines |
| Test DB | PostgreSQL `palmistry_test`, Alembic-managed, per-test truncation (`conftest.py`) |
| API contract | Postman collection `backend/postman/palmistry-auth.postman_collection.json` |
| CI | `ci.yml`: migration check (`scripts/check_migrations.py`) → `pytest backend/tests` → frontend `npm ci/lint/build` → both Docker builds |
| Master verification | `scripts/verify_all.py`; role smoke `scripts/smoke_roles.py`; extraction check `verify_real_extraction.py` |

### 12.2 Suite inventory (28 test modules)

`test_health` · `test_auth_password` · `test_auth_endpoints` · `test_auth_rbac` (RBAC matrix §49.3) · `test_auth_google` (mocked adapter) · `test_auth_ratelimit` · `test_profile_endpoints` (defaults, validation, interests/goals CRUD+limits, avatar upload/fetch/ETag/413/415, per-user isolation) · `test_palm_analysis` · `test_tarot_interpretation` (determinism, structure, reversals, analytics, domain focus, error envelopes) · `test_reading_endpoints` (real-CV creation, rejections, access matrix, pagination, analytics) · `test_reading_reports` (FR-057/58 JSON, `%PDF-` magic, `PK` XLSX magic + sheets, access) · `test_personality` · `test_life_trend_analyzer` (signal extraction from real payloads, determinism, per-user divergence, goal boosts, attribution) · `test_recommendations` (catalog, heuristic fallback, LLM fakes, prompt content, clamping, tarot-only, persistence, feedback→prompt, metrics) · `test_llm_adapter` · `test_notifications`-covered-in-role suites + `test_consultation_messages` · `test_consultation_insights` · `test_consultant_clients` · `test_booking_endpoints` (52 tests, mocked calendar-era + lifecycle) · `test_booking_proposals_and_chat` · `test_reader_workspace` (spread authoring, custom-spread readings, reports) · `test_admin_console` · `test_assistant_endpoints` (18: auth 401s, 422s, per-role scoping, grounding, turn stamping, no cross-account leaks) · `test_role_portals` · `test_role_endpoints` · `test_system_reports` · `test_reference_datasets` (all 78 cards + catalogs load cleanly) · `test_deploy_config`.

### 12.3 Documented green-run snapshots (chronological, from CHANGELOG/AGENT_PROGRESS)

| Snapshot | Result |
|---|---|
| Auth/RBAC & profile era | 45 passed → **85 total passed** + live smoke (16 checks) |
| After TASK-005 datasets | CLAUDE.md quick-reference: "all 106 tests must pass" |
| Tarot engine (v0.6.0) | **154/154** passing; frontend lint + build clean |
| Readings + reports (v0.8.0) | **172/172** passing on `palmistry_test` |
| Recommendations (v0.9.0 → v0.10.0) | **268/268** → **270/270** passing; `verify_all.py` all green |
| Booking module | 52 new booking tests (50 passed / 2 skipped when run alone) + full suite; migrations applied cleanly; lint + build clean |
| Dashboard assistant | 18/18 assistant tests |
| Consultant FR-037 console | Lint clean, 28 routes built, live API + full browser walkthrough per route, zero console errors |
| Four-role completion session | Tests + lint + production build + docs verified; scheduler double-start bug fixed which unblocked running the suite end-to-end |
| Latest commits (Oct 12–16) | Docker build fixes, MediaPipe GLES/EGL fixes, cookie Secure/SameSite derivation, reader.py repair — deployment-path hardening |

> Note: root `pytest-report.xml` is a **stale partial snapshot** (2026-10-11, 20 tests) superseded by the later documented runs above. Static count is now 445 test functions.

### 12.4 Manual / live verification culture `[DOC]`
Session evidence logs include: full auth flow smoke (register 201 → me → refresh rotation → logout → refresh 401; duplicate 409; bad password 401), profile smoke (avatar upload/fetch/304/delete/404), live reading creation through the real CV pipeline, tarot draws with real catalog data, recommendations live-verified with real Groq credentials (`generation_method=llm`), assistant answers quoting only snapshot numbers for all four roles, booking end-to-end with mocked calendar client, email-free in-app notification end-to-end check, and browser walkthroughs of every console route.

## 13. Data & Assets `[CODE + DOC data/README.md]`

### 13.1 Curated reference data — `data/` (7 files, 7,472 lines)
| File | Content |
|---|---|
| `landmarks/hand_landmarks_schema.json` | MediaPipe 21-point hand landmark reference definition |
| `palmistry/lines_catalog.json` | 5 palm lines (Life, Head, Heart, Fate, Sun) — descriptions, significance, coordinates |
| `palmistry/mounts_catalog.json` | 6 mounts (Jupiter, Saturn, Apollo, Mercury, Venus, Moon) |
| `tarot/rider_waite_deck.json` | 78 cards — id/name/number/arcana/suit/keywords/upright+reversed meanings/image path |
| `tarot/spreads.json` | 6 standard spreads with positions, labels, meanings, layout coordinates |
| `recommendations/recommendations_catalog.json` | 64 recommendation items across 5 types (19 growth, 12 relationship, 11 career, 11 goal-alignment, 11 spiritual) |
| `README.md` | Raw→curated mapping table (TASK-005), JSON schemas, ingestion workflow, verification rule (all 78 cards + 5 lines load cleanly) |

### 13.2 Raw datasets — `dataset/` `[DOC data/README]`
| Source | Used for |
|---|---|
| `palmline/` — YOLOv5 formats ("Palm Line Detection.v2i", `dataset_seimbang`) | Life/Head/Heart/Fate line annotations (training/reference) |
| `Hands and palm images dataset/` | Palm morphology, lighting, skin tones, orientation test fixtures |
| `Toroto card/` (Tarot Deck + meanings + `tarot_dataset_offline`) | 78-card imagery and symbolic meanings |

### 13.3 Runtime assets
- `frontend/public/cards/` — **78 card images** exactly (m00–m21 majors = 22; w01–w14, c01–c14, s01–s14, p01–p14 minors = 56), rendered via `next/image`.
- `models/hand_landmarker.task` — MediaPipe HandLandmarker model consumed by the CV pipeline.
- `uploads/` — `avatars/` (profile photos) and `palm/` (`<reading_id>.img` source images).
- `ai/` — artifact namespace (embeddings, interpretation, palm, personality, recommendations, tarot, trends); no source files documented there in the reviewed docs.

### 13.4 Seeds & tooling `backend/scripts/`
`seed_roles.py` · `seed_tarot.py` (78 cards + spreads) · `seed_palm_features.py` · `seed_consultants.py` · `create_admin.py` (admin seeder) · `train_recommender.py` (legacy ML-era CLI, kept) · probe scripts (`probe_palm_endpoint.py`, `probe_pdf_export.py`).

---

## 14. Deployment & Operations `[CODE + DOC]`

### 14.1 Containers
| Component | Detail |
|---|---|
| `backend/Dockerfile` | production image, non-root `appuser`, `WORKDIR /app`, uploads volume mount point, healthcheck via `/health` |
| `frontend/Dockerfile` | production Next.js image; `NEXT_PUBLIC_API_BASE_URL` baked as build arg |
| `docker-compose.yml` | 4 services: **db** (postgres:16-alpine, `pg_isready` healthcheck, `pgdata` volume) → **migrate** (one-shot `alembic upgrade head`, waits for db healthy) → **backend** (uvicorn `--workers 2`, depends on migration completion, port 8000, uploads volume) → **frontend** (port 3001→3000, waits for backend healthy) |

### 14.2 CI/CD (`.github/workflows/`)
| Workflow | Jobs |
|---|---|
| `ci.yml` | **backend** (Postgres 16 service → `check_migrations.py` → `pytest backend/tests -q` on Python 3.11) · **frontend** (Node 20, `npm ci` → `lint` → `build`) · **docker** (builds both production images) |
| `deploy.yml` | on push to `main` / manual: AWS OIDC role assumption → ECR login → builds + pushes backend and frontend images tagged with `GITHUB_SHA` |

### 14.3 Cloud runbook & ops scripts
- `docs/deployment/aws-production.md` — AWS Fargate/RDS deployment runbook (per CHANGELOG deployment block).
- `scripts/deploy_aws.ps1` — deploy helper; `scripts/backup_db.ps1` — pg_dump backup; `check_neon.py` — Neon-hosted Postgres connectivity/table check; frontend Next config fixed for Vercel (commit `f079098`).
- Production config guard in `backend/app/config.py` (production + DEBUG rejected).
- Local dev: `run_dev_server.bat` (backend, waits; logs to `backend_dev_server.log`) + `npm run dev` (frontend).

### 14.4 Environment variables catalog `[CODE .env.example]`
| Group | Variables (defaults) |
|---|---|
| App | `APP_NAME`, `ENVIRONMENT=development`, `DEBUG=true`, `API_V1_PREFIX=/api/v1` |
| Security | `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`, `REFRESH_TOKEN_EXPIRE_DAYS=14`, `REFRESH_COOKIE_SECURE=false` |
| OAuth | `GOOGLE_CLIENT_ID/SECRET` (empty → 503), `GOOGLE_REDIRECT_URI`, `FRONTEND_URL=http://localhost:3000` |
| CORS | `CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]` |
| Database | `DATABASE_URL`, `DATABASE_TEST_URL` |
| AI | `OPENAI_API_KEY`/`OPENAI_MODEL=gpt-4o-mini` · `GROQ_API_KEY`/`GROQ_MODEL=qwen/qwen3.8-27b` · `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2` |
| Limits | `MAX_UPLOAD_SIZE_MB=10`, `RATE_LIMIT_PER_MINUTE=60`, `AUTH_RATE_LIMIT_PER_MINUTE=10` |
| Booking | `BOOKING_MIN_LEAD_MINUTES=60`, `BOOKING_MAX_ADVANCE_DAYS=60`, `BOOKING_CANCEL_WINDOW_HOURS=24`, `BOOKING_REMINDER_LEAD_MINUTES=1440`, `BOOKING_SHORT_REMINDER_LEAD_MINUTES=60`, `BOOKING_SLOT_HORIZON_DAYS=21`, `BOOKING_ROLLOUT_HOUR=1` |
| Email (legacy) | SMTP vars + `EMAIL_FROM_NAME="MysticLens Divination"` (email channel removed; vars remain in example) |
| Deploy | `POSTGRES_USER/PASSWORD/DB`, `PUBLIC_API_BASE_URL`, `AWS_REGION=us-east-1`, `ECR_BACKEND_REPO=palmistry-backend`, `ECR_FRONTEND_REPO=palmistry-frontend`, `RDS_DATABASE_URL`, `S3_UPLOADS_BUCKET` (empty keeps local disk) |

---

## 15. Documentation & Decision Records `[CODE]`

### 15.1 Documentation inventory
| Document | Role |
|---|---|
| `PALMISTRY_TAROT_AI_AGENT_SPEC.md` | Authoritative master contract — 50 sections, FR-001…FR-072, §49 implementation defaults (tech, media, tarot, LLM, scoring, API, testing, deployment, performance, safety) |
| `ARCHITECTURE.md` | Living architecture overview, key decisions, testing & deployment target |
| `CHANGELOG.md` | Versioned history v0.5.2 → v0.12.0 + 7 [Unreleased] feature blocks (most detailed feature source) |
| `AGENT_PROGRESS.md` | Session-by-session implementation evidence with verification results |
| `PROGRESS.md` | Milestone/task status + decisions log D-001…D-014 + blockers |
| `README.md` | Project overview, feature summary, tech stack table, prerequisites |
| `CLAUDE.md` | Agent quick-reference (test/lint/build commands, update policy) |
| `data/README.md` | Reference dataset catalog, schemas, ingestion workflow (TASK-005) |
| `tests/README.md` | Test-suite organization (backend here, E2E reserved top-level) |
| `docs/workflows/` | 4 documented flows: core user journey, palm analysis, tarot reading, combined intelligence (+README) |
| `docs/wireframes/` | 9 wireframe specs: 01 authentication → 09 reports/export (+README) |
| `docs/decisions/` | 9 decision records (listed below) |
| `docs/deployment/aws-production.md` | AWS production runbook |
| `docs/BOOKING_MODULE_PLAN.md` | Booking module design & phase plan |

### 15.2 Decision log D-001…D-016 (one-liners)
| # | Decision |
|---|---|
| D-001 | Local Python 3.11.7 (spec default 3.12); code kept 3.12-compatible · *file: 0001 (per PROGRESS)* |
| D-002 | Backend unit tests in `backend/tests/`; top-level `tests/` reserved for E2E |
| D-003 | Next.js **Pages Router** (`src/pages`) to match the spec structure |
| D-004 | Chart.js now; Plotly deferred to the dashboards milestone · *docs/decisions/0002* |
| D-005 | Docker Compose deferred until first migration (later delivered); Redis absent → in-process substitutes |
| D-006 | Heavy AI/CV dependencies installed with the milestones that use them, pinned per feature |
| D-007 | **PostgreSQL 16 installed locally** (not SQLite) · `0007-postgresql-16-local-install.md` |
| D-008 | **DB-backed rotating refresh tokens** (SHA-256) with reuse detection revoking all sessions · `0008-…` |
| D-009 | Refresh token in **httpOnly cookie**, access token in frontend memory · `0009-…` |
| D-010 | **Google OAuth behind adapter**; 503 when unconfigured; email-based upsert linking · `0010-…` |
| D-011 | **In-process fixed-window auth rate limiting** (10/min per scope+IP) until Redis · `0011-…` |
| D-012 | Email verification + password reset deferred to the notification milestone |
| D-013 | Profile data model: 1:1 `profiles` + interests + goals; **string catalogs, not PG enums**; lazy get-or-create + backfill · `0012-profile-model-string-catalogs.md` |
| D-014 | **Avatars: full image upload** (magic bytes, ≤5 MB), local disk, Bearer-gated with ETag/304 · `0013-avatar-upload-local-disk.md` |
| D-015 | **Tarot: rule-based interpretation engine** (data-driven, deterministic, testable) · `0015-tarot-rule-based-interpretation-engine.md` |
| D-016 | **In-process streamed report exports** (ReportLab PDF + openpyxl Excel) · `0016-inprocess-streamed-report-exports.md` |

Decision-file note: files exist for 0007–0016 (nine files; no 0014 file present); D-001…D-006 are recorded in PROGRESS.md.

---

## 16. Project Timeline & Statistics

### 16.1 Documented changelog timeline `[DOC CHANGELOG.md]`
| Version / block | Date | Headline |
|---|---|---|
| v0.5.2 | 2026-09-08 | Interactive palm visualizer overlay + webcam auto-capture scanner |
| v0.6.0 | 2026-09-11 | Tarot card interpretation engine (rule-based, 6 spreads, seeded draws) |
| v0.7.0 | 2026-09-11 | Tarot interactive draw UI wired to the real engine (78 card artworks) |
| v0.8.0 | 2026-09-15 | Unified reading workflows (real palm CV pipeline) + PDF/Excel report system |
| v0.8.1 | — | AI interpretation fixes (non-blocking, background fetch) |
| v0.9.0 | 2026-09-23 | Recommendation engine (first ML iteration) + 64-item catalog + feedback stream |
| v0.10.0 | 2026-09-24 | Recommendations reworked to **LLM engine** (Groq/OpenAI + heuristic fallback) |
| v0.11.0 | 2026-09-26 | **Life Trend engine** (feature-based, explainable) + personality dashboard panel |
| v0.12.0 | 2026-09-26 | UI/UX production polish: shared UI kit, design tokens, honest-data cleanup, error-handling consolidation |
| [Unreleased] 1 | — | Notification system → **in-app only** + header bell (email removed) |
| [Unreleased] 2 | — | **Dashboard AI assistant** (grounded, role-scoped) |
| [Unreleased] 3 | — | **Spiritual Consultant frontend console** (FR-037) |
| [Unreleased] 4 | — | **Live consultation & booking module** (+ seeker/consultant separation, proposals, chat, expert→consultant rename) |
| [Unreleased] 5 | — | **Four-role capability completion** (admin console, spread authoring, reader reports/engagement, live client roster) |
| [Unreleased] 6 | — | **Deployment** (Docker images, Compose, CI + ECR push, AWS runbook, backup script, config guard) |
| [Unreleased] 7 | — | Google Calendar removal → **manual Meet links** (migration 0013) |

### 16.2 Git history
- Repository initialized **2026-10-12** ("Initial commit: Palmistry & Tarot intelligence platform" — imports the completed work into a fresh repo).
- **11 commits** on `main` through **2026-10-16**, focused on deployment hardening: MediaPipe EGL/GLES fixes, Docker + cross-site session fixes, refresh-cookie Secure/SameSite derivation, reader.py repair, Vercel Next config, popular-spreads aggregation robustness, spread_name/card_count for reporting.

### 16.3 Measured statistics (2026-10-16)
| Metric | Value |
|---|---|
| Backend application | 124 `.py` files · 20,776 lines (`backend/app`) |
| Backend tests | 30 files · 8,112 lines · **445 test functions** |
| Frontend source | 131 files (130 `.js` + 1 `.css`) · 28,749 lines (`frontend/src`) |
| Reference data | 7 files · 7,472 lines (`data/`) |
| Rest of tree | spec (~4,000+ lines) · CHANGELOG (~670 lines) · AGENT_PROGRESS (~620 lines) · 9 wireframes · 4 workflows · 9 decision files |
| Endpoint modules | 18 · **138 route handlers** |
| Frontend structure | 34 pages · 67 component files / 12 groups · 16 services · 3 layouts · 3 hooks · 5 lib modules |
| Database | 13 migrations · 23 tables + `alembic_version` |
| Tarot assets | 78 card images + 6 spreads (+ custom authoring) |
| Roles / consoles | 4 roles · 4 console route spaces |

Re-measure commands (PowerShell, from repo root):
```powershell
# test function count
(Select-String -Path backend/tests/*.py -Pattern "def test_" | Measure-Object).Count
# endpoint count (all named routers)
(Select-String -Path backend/app/api/v1/endpoints/*.py -Pattern "@[A-Za-z_]+\.(get|post|put|patch|delete)\(" | Measure-Object).Count
# LOC per tree
.venv\Scripts\python.exe -c "import os;print({r:sum(len(open(os.path.join(dp,f),encoding='utf-8',errors='ignore').readlines()) for dp,_,fs in os.walk(r) if '__pycache__' not in dp for f in fs) for r in ['backend/app','backend/tests','frontend/src','data']})"
```

---

## 17. Known Gaps & Future Scope (honest list, from docs + code checks)

1. **Google OAuth live flow unverified** — adapter/tests mocked; returns `503 OAUTH_NOT_CONFIGURED` until `GOOGLE_CLIENT_ID/SECRET` are supplied (D-010 blocker).
2. **Notification channels**: in-app only. Email service/templates were removed; SendGrid/Twilio (spec aliases) not integrated; SMS never configured.
3. **Redis-class infrastructure deferred** (D-005/D-011): rate limiting and the latency ring buffer are **in-process / per-worker**; MongoDB, Elasticsearch, Chroma/FAISS, Neo4j, InfluxDB are not wired (spec §49.10 is the target architecture, not current state).
4. **Plotly deferred** (D-004) — Chart.js is used for all dashboards.
5. **Composite Overall Insight Score (spec §49.9 formula) not implemented as a single number** — searched 2026-10-16 (no `overall_insight`/weighted-formula code); component-level confidences are exposed instead. "Spiritual guidance scoring" is covered only through consultant effectiveness/insights.
6. **Frontend unit tests (Vitest/RTL) and Playwright E2E are not written** — top-level `tests/` is reserved; automated testing today is backend pytest (445 functions) + lint/build gates + documented live smoke checks.
7. **Async job infra not used** — APScheduler runs in-process (jobs stop with the API process; single-worker assumption documented).
8. **Consultant console demo slices** — per-client palm/tarot/personality/AI-insight cards remain a **labelled** demo dataset; consultant notes + started sessions persist to `localStorage`; assistant conversations are not persisted across reloads (all listed as next steps in the docs).
9. **Payments not implemented** (spec §49.12 default Razorpay; "do not invent pricing or paid features").
10. **YOLOv5 / trained CNNs not wired** — runtime palm CV is MediaPipe + OpenCV heuristics (pipeline v1.0.0); YOLOv5 line annotations exist under `dataset/` for a future training milestone.
11. **Production cloud rollout pending** — images, Compose, CI (with ECR push) and the AWS runbook are ready; live AWS deployment is still in the "[Unreleased]" deployment block. (Vercel frontend config + Neon DB check script exist, indicating hosted-environment practice.)
12. **Python 3.11 local** vs spec default 3.12 (D-001; code 3.12-compatible).
13. **Known UI issue**: `/login/[role]` can stall on "Opening portal…" on cold load/after sign-out (documented, pre-existing).
14. **Performance targets are engineering goals, not measured claims** — spec §49.17 (<500 ms typical API, <2.5 s dashboard, <10 s palm inference); no benchmark results published yet, consistent with the "record measured results" rule (§37.15).
15. **Doc-drift cleanup candidates**: README lists "Lucide React" (not a real dependency); README references a root `AGENTS.md` that is not present; `PROGRESS.md` milestone status lags the actual implemented scope (CHANGELOG/AGENT_PROGRESS are current); the spec's §40 master FR table still shows every FR as "Pending" — it predates implementation and must not be quoted as status.
16. **Stale artifacts in the repo root**: `pytest-report.xml` (partial 2026-10-11 snapshot) and dev-server logs — safe to exclude from submission or regenerate.

Future-scope items named by the project docs themselves: persist assistant conversations; `PATCH /consultant/sessions/{id}/notes` so notes leave localStorage; Redis for multi-worker rate limiting/temperature buffer; regenerate-insights action; more datasets/models (YOLO training) and measured benchmarks; user guides.

---

## 18. PPT-Ready Highlights (all verified facts)

**Concept & scope**
- A full-stack **Palmistry & Tarot Intelligence Platform** covering 13 capability modules from the master spec — from CV palm analysis to reports, notifications and a live consultation marketplace.
- **4 role consoles** in one product: Seeker, Tarot Reader, Spiritual Consultant, Administrator — with backend-enforced RBAC and deliberate separation of duties (admins cannot host sessions).
- **33 application routes** across 5 route spaces, built with a shared UI kit, semantic design tokens and a strict LOADING/EMPTY/ERROR/SUCCESS convention.

**AI & algorithms (grounded, explainable)**
- **Palm CV pipeline** (v1.0.0): MediaPipe 21-landmark detection + OpenCV crease analysis → 5 classical lines with per-line confidence/curvature/clarity, 6 mounts, elemental palm shape, 2D:4D digit ratio, thumb/pinky traits — every inference persisted with model version + confidence.
- **Tarot engine**: 78-card Rider-Waite-Smith deck, 6 standard spreads + reader-authored custom spreads, reversals, arcana/elemental/numerology synthesis, composed narrative, cryptographically secure seeded draws.
- **Grounded LLM layer**: provider-adaptive adapter (OpenAI/Groq/deterministic fallback) with structured, versioned outputs — plus a dashboard assistant that may quote **only** server-computed snapshot numbers (role-scoped, 12-turn memory, rule-engine fallback).
- **Life Trend engine**: transparent recency-weighted (90-day half-life) scoring across 6 life domains with per-item signal attribution, direction/strength/confidence and a feature vector for future supervised models — explicitly no fake accuracy claims.
- **Recommendations**: LLM engine v2.0.0 with a 64-item catalog, feedback-driven personalization, honest `generation_method` reporting and a dependency-free offline fallback.

**Product depth**
- Reports: JSON + **PDF dossier** (ReportLab) + **3-sheet Excel** (openpyxl) with mandatory safety disclaimer.
- Live consultation marketplace: availability rules → materialised 21-day slot horizon (DST-aware) → booking with negotiation states, per-booking chat, manual Google Meet links, reminders at 24 h/1 h, feedback ratings.
- Notifications & engagement: in-app bell + center, daily-guidance/reminder schedulers, event-driven fanout to the right roles.

**Engineering quality**
- **138 REST endpoints · 13 Alembic migrations · 23 tables · 445 automated tests · ~58,000 lines of first-party code** (backend 20.8k + tests 8.1k + frontend 28.7k, excluding data/spec/docs).
- Security-by-design: Argon2id, JWT + rotating refresh tokens with **theft detection**, per-route RBAC bundles, rate limiting, uniform error envelope with request IDs, upload magic-byte validation, security/error monitoring middleware.
- Deployment-ready: Dockerfiles + Compose stack with healthchecks, GitHub Actions CI (migrations + tests + lint + build + image builds) and ECR deploy workflow, AWS runbook, backup script, production config guard.
- Documentation discipline: 50-section master spec, architecture doc, detailed changelog, per-session evidence logs, 9 wireframes, 4 workflow docs, 16 recorded decisions.

---

## 19. Placeholders — fill before submission `[FILL]`

| Field | Value |
|---|---|
| Student name(s) | _[FILL]_ |
| Roll number(s) / registration | _[FILL]_ |
| Institution / university | _[FILL]_ |
| Department / programme | _[FILL]_ |
| Project guide / mentor | _[FILL]_ |
| Course code / semester | _[FILL]_ |
| Submission date | _[FILL]_ |
| Presentation duration & format | _[FILL]_ |
| Project display name | Either "Palmistry & Tarot Intelligence Platform" (spec) or "MysticLens" (in-repo branding) — _[FILL]_ |

**Suggested assets to capture for the report/PPT:** landing + auth screens; palm upload → result (with SVG overlay) → PDF export; tarot draw flow + spread layout; personality + life-trend dashboard (charts); recommendations; notification bell + center; consultant console (trend chart, workspace); reader spread studio; admin console (permissions matrix, security monitor, performance); booking directory + negotiation + chat; ER diagram (from §5); architecture diagram (from §4); test-suite summary screenshot.

---

*End of `report_data.md` — compiled 2026-10-16 from the repository's code, spec, changelog and documentation. Statistics re-measurable via the commands in §16.3. Where docs and code disagreed, code was taken as truth and the drift was flagged.*
