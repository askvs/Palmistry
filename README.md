# Palmistry & Tarot Intelligence Platform

> An AI-powered spiritual intelligence platform that analyzes palm images and tarot card selections to generate personalized, holistic insights related to personality traits, relationships, career paths, and life trends.

Authoritative Specification: [`PALMISTRY_TAROT_AI_AGENT_SPEC.md`](file:///c:/Users/ASUS/Desktop/Palmistry/PALMISTRY_TAROT_AI_AGENT_SPEC.md)  
Current Implementation Status: [`AGENT_PROGRESS.md`](file:///c:/Users/ASUS/Desktop/Palmistry/AGENT_PROGRESS.md)  
Architecture Decisions & Overview: [`ARCHITECTURE.md`](file:///c:/Users/ASUS/Desktop/Palmistry/ARCHITECTURE.md)  
AI Agent & Developer Guide: [`AGENTS.md`](file:///c:/Users/ASUS/Desktop/Palmistry/AGENTS.md)

---

## Features Implemented to Date

- **Authentication & RBAC (TASK-003)**:
  - Argon2id password hashing.
  - JWT HS256 short-lived access tokens.
  - DB-backed rotating refresh tokens with token reuse / theft detection.
  - httpOnly `palmistry_refresh` cookie storage for refresh tokens.
  - 4 Role capabilities: `user`, `tarot_reader`, `spiritual_consultant`, `admin`.
  - In-process auth rate limiting (10 req/min per scope+IP).
  - Google OAuth2 adapter (mocked/configured for credentials).
- **User Profile Management (TASK-004)**:
  - User identity, age group, spiritual interests chips, and goals CRUD (25 goal cap).
  - Reading preferences (deck catalog, 6 spreads, interpretation tone).
  - Notification preference toggles (email, in-app, SMS).
  - Multipart avatar upload with magic-byte validation (JPG/PNG/WEBP ≤ 5 MB), local storage, and ETag/304 caching.
  - Frontend `/profile` page with silent session restoration.
- **Role workspaces (four dedicated consoles)**:
  - **Seeker** — `/dashboard` with readings, personality insights, recommendations and guidance threads.
  - **Tarot Reader** — reading queue with certification, reading analytics, **user-engagement insights**, **reading report management** (`/reader/reports`: filters + PDF/Excel export) and **spread authoring** (`/reader/spreads`: custom 1–10 position spreads that run through the same interpretation engine).
  - **Spiritual Consultant** — `/consultant/*` console with client trend analysis, guidance effectiveness, consultation insights, a **live client roster** (real seekers, their interests and spiritual goals) and a **goal-progress** panel paired with real reading/thread activity.
  - **Administrator** — `/admin/*` console with user governance & role assignment, platform analytics, read-only session oversight, an error & security monitor, the live RBAC permission matrix, authentication settings, system configuration & release information, and system reports. Administrators deliberately have **no** booking or session-hosting access.
- **Test Coverage**:
  - Automated backend tests across health, auth, RBAC, profile, palm, tarot, personality, readings, recommendations, notifications, booking, consultant, reader-workspace and admin-console suites.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16 (Pages Router), React 19, Tailwind CSS v4, Lucide React, Chart.js |
| **Backend** | FastAPI, Python 3.11/3.12, Pydantic v2, Uvicorn |
| **Database & ORM** | PostgreSQL 16 (local), SQLAlchemy 2.0, Alembic migrations |
| **Auth & Security** | Argon2id (`argon2-cffi`), PyJWT, Authlib, Secure httpOnly Cookies |
| **AI / CV** | MediaPipe (hand landmarks), YOLOv5 (palm line detection), OpenCV |
| **Testing** | Pytest, HTTPX, Next.js lint & build |

---

## Prerequisites

1. **Python**: 3.11 or 3.12 (`.venv` virtual environment in workspace root)
2. **Node.js**: 20+ and npm
3. **PostgreSQL 16**: Local service running on port 5432
   - Database `palmistry` (development)
   - Database `palmistry_test` (automated test suite)

---

## Quick Start

### 1. Environment Configuration
Ensure `.env` exists in the repository root (see [`.env.example`](file:///c:/Users/ASUS/Desktop/Palmistry/.env.example)):
```ini
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/palmistry
TEST_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/palmistry_test
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
COOKIE_SECURE=False
UPLOAD_DIR=uploads
```

### 2. Database Migrations
Run Alembic migrations to bring the database schema up to date:
```powershell
cd backend
..\.venv\Scripts\alembic upgrade head
cd ..
```

### 3. Start Backend API Server
```powershell
.\.venv\Scripts\uvicorn app.main:app --app-dir backend --reload --port 8000
```
- API Docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- OpenAPI Specification: [http://localhost:8000/api/openapi.json](http://localhost:8000/api/openapi.json)

### 4. Start Frontend Client
```powershell
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## Running Tests & Verification

### Run Full Test Suite (106 tests)
```powershell
.\.venv\Scripts\pytest backend/tests
```

### Run Frontend Lint & Production Build
```powershell
cd frontend
npm run lint
npm run build
cd ..
```

### Universal Verification Script
Run backend tests, frontend lint, and frontend build in a single pass:
```powershell
.\.venv\Scripts\python scripts/verify_all.py
```

### Role Smoke Test (against a running backend)
Exercises the four roles end-to-end over HTTP and prints one PASS/FAIL line per
requirement. Start the backend first
(`uvicorn app.main:app --app-dir backend --port 8000`), then:
```powershell
$env:PYTHONPATH = "backend"
.\.venv\Scripts\python scripts\smoke_roles.py
```
The script registers a fresh seeker / reader / admin / consultant per run and
promotes the staff accounts directly in the database, because a newly registered
account is always a seeker and dev has no invite code.

### Slow-suite watchdog
Several tests exercise the LLM-backed interpretation path, which takes tens of
seconds each, so a plain run looks hung. `scripts/run_with_watchdog.py` prints a
faulthandler traceback if a run really does stall and writes a JUnit report:
```powershell
.\.venv\Scripts\python scripts\run_with_watchdog.py backend\tests 2400
```

### Migration chain check
After adding a migration, confirm the chain still has exactly one head and no
dangling parents:
```powershell
.\.venv\Scripts\python scripts\check_migrations.py
```

> **Note on test-database state:** the suite truncates a fixed table list before
> every test (see `backend/tests/conftest.py`). After adding a migration, either
> `alembic upgrade head` (which the suite runs itself) or, if the schema was
> created before the new table existed, a schema reset:
> `psql -d palmistry_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`
> **Never run two pytest processes against `palmistry_test` at once** — they
> truncate each other's tables and appear to hang.

---

## Project Structure

```text
Palmistry/
├── AGENTS.md                  # Universal AI agent instructions & non-negotiable rules
├── CLAUDE.md                  # Claude Code instructions
├── .cursorrules               # Cursor AI rules
├── README.md                  # Master documentation
├── AGENT_PROGRESS.md          # Living task progress & decisions log
├── ARCHITECTURE.md            # Architecture specification & decisions
├── CHANGELOG.md               # Version changelog
├── PALMISTRY_TAROT_AI_AGENT_SPEC.md # Master 4116-line authoritative specification
├── backend/                   # FastAPI backend application
│   ├── alembic/               # Database migrations
│   ├── app/                   # App routes, models, schemas, and services
│   └── tests/                 # Backend test suite (106 tests)
├── frontend/                  # Next.js 16 frontend application
│   └── src/                   # Pages, components, services, and hooks
├── data/                      # Reference datasets (landmarks, palmistry, tarot)
├── dataset/                   # Raw datasets (YOLOv5 annotations, hands, cards)
├── docs/                      # Wireframes, workflows, and architecture decision records
├── scripts/                   # Verification and maintenance scripts
└── tests/                     # Top-level E2E integration test harness
```

---

## Deploy (Docker Compose)

1. Copy env: `copy .env.example .env` then fill `SECRET_KEY` and `POSTGRES_PASSWORD`.
2. Start: `docker compose up --build -d`
3. Migrate runs automatically via the `migrate` service (`alembic upgrade head`).
4. Open frontend `http://localhost:3000`, API docs `http://localhost:8000/api/docs`, health `http://localhost:8000/health`.
5. Stop: `docker compose down` (volumes `pgdata`/`uploads` persist data).

---

## Safety & Ethics Notice

Per §0.1 Rule 21 and §49.19 of the master specification, all palmistry, tarot, health, career, and life trend analyses provided by this platform are designed for **personal reflection, entertainment, and self-discovery**. They do not constitute professional medical, legal, psychological, or financial advice.
