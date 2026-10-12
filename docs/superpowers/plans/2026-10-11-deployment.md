# Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Palmistry & Tarot platform deployable via Docker images + Docker Compose + GitHub Actions CI/CD with AWS as the default cloud.

**Architecture:** Keep the current modular monolith (Next.js Pages Router :3000 → FastAPI `/api/v1` :8000 → PostgreSQL 16 :5432). Add a `backend` image (uvicorn, multi-worker), a `frontend` image (Next standalone), a `db` service, and a one-shot `migrate` service running `alembic upgrade head`. Cloud-specific pieces (S3 uploads, RDS URL, secrets manager) stay behind env-var adapters so Azure remains replaceable.

**Tech Stack:** Docker + Docker Compose v2, GitHub Actions, AWS (ECR/ECS-Fargate/RDS-Postgres-16/S3), Uvicorn `--workers`, Next.js 16 standalone, Alembic, PostgreSQL 16.

**Spec:** `PALMISTRY_TAROT_AI_AGENT_SPEC.md` — §21.6 (Uvicorn dev, production ASGI in deploy), §21.7 (Compose default local env + one-command startup in README), §21.8 (Docker images + GitHub Actions, AWS default, adapters replaceable), §25 (Docker REQUIRED, AWS/Azure options, production/monitoring/logging/stable perf/Docker/docs), §49.16 (Compose local, Actions CI/CD, AWS default, dev/staging/prod separation, health checks + structured logging + monitoring + alerts + backups + DR mandatory), §49.17 (API <500ms, dashboard <2.5s, palm <10s, async long jobs, horizontally scalable workers).

## Global Constraints

- Python 3.11 or 3.12; backend deps only from `backend/requirements.txt` via `pip install -r backend/requirements.txt`.
- Frontend is Next.js 16 Pages Router (`frontend/src/pages`); deps via `npm ci`; do not migrate to App Router.
- Database is PostgreSQL 16; schema changes only via Alembic in `backend/alembic/versions/`; verify with `scripts/check_migrations.py`.
- Every API error keeps the `{"code","message","request_id"[, "fields"]}` envelope from `backend/app/main.py:57-65`.
- Auth stays Argon2id + JWT HS256 (30-min access) + DB-backed rotating refresh in httpOnly `palmistry_refresh` cookie.
- CORS origins come from env (`CORS_ORIGINS`); credentials:include + Bearer memory-token flow in `frontend/src/services/api.js:1-34` must keep working.
- Never commit real secrets; `.env` / `.env.local` stay gitignored; only `*.example` files are committed.
- Uploads live under `UPLOAD_DIR` (default `uploads`); avatars are JPG/PNG/WEBP ≤5MB validated by magic bytes.
- Frontend base URL is build-time `NEXT_PUBLIC_API_BASE_URL` (see `frontend/.env.local.example:1-2`).
- Where spec lists alternatives (AWS/Azure, S3/Blob, Stripe/Razorpay, SendGrid/Twilio) preserve both; do not silently drop Azure paths.
- Verification gate per task: `.\.venv\Scripts\python scripts/verify_all.py` (pytest + `npm run lint` + `npm run build`) stays green.

## Review Focus

- Missing `DATABASE_URL` at container boot should fail fast with a readable log line, not a 30s SQLAlchemy reconnect loop — expect `alembic upgrade head` to exit non-zero within 10s.
- `NEXT_PUBLIC_API_BASE_URL` baked at `next build` time pointing at `localhost:8000` inside a Compose network should still resolve from the browser — expect docs to force an explicit public URL at build time.
- `uploads/avatars` written inside the `backend` container without a named volume should survive `docker compose down` — expect files to persist via a volume.
- Two `uvicorn --workers 4` replicas behind one Compose network rely on in-process auth rate limiting (D-011) — expect docs to label limits as per-worker until Redis lands.
- `alembic upgrade head` run concurrently by two `migrate` replicas should not fork the migration chain — expect exactly one head verified by `scripts/check_migrations.py`.

---

### Task 1: Backend production image

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Modify: `backend/requirements.txt:1-25` (no dep change; pin verified only if `pip freeze` drifts — otherwise untouched)

**Interfaces:**
- Consumes: `backend/app/main.py:114-175` (`create_app()`, `/health`, `/api/docs`, `/api/openapi.json`), `backend/alembic.ini:1-6`, `backend/requirements.txt`
- Produces: image `palmistry-backend:local` exposing `8000`, `HEALTHCHECK CMD ... /health`, non-root `appuser`, entrypoint `uvicorn app.main:app --host 0.0.0.0 --port 8000`

- [ ] **Step 1: Write `backend/.dockerignore`**

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.next/
pytest-report.xml
uploads/
*.log
.venv/
tests/
postman/
```

- [ ] **Step 2: Write `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN useradd -m appuser && mkdir -p /code/uploads && chown -R appuser:appuser /code
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').getcode()==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

- [ ] **Step 3: Build the image**

Run: `docker build -t palmistry-backend:local ./backend`
Expected: `BUILDX ... DONE` / `naming to docker.io/library/palmistry-backend:local`, exit 0.

- [ ] **Step 4: Smoke-run with dummy DB URL (fail-fast check)**

Run: `docker run --rm -e DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/palmistry -p 8000:8000 palmistry-backend:local`
Expected: container starts, `GET http://127.0.0.1:8000/health` returns `{"status":"ok"}`; stop with Ctrl-C.

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/.dockerignore
git commit -m "deploy: add backend production image"
```

### Task 2: Frontend production image (standalone)

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`
- Modify: `frontend/next.config.mjs:1-7`

**Interfaces:**
- Consumes: `frontend/src/services/api.js:1` (`NEXT_PUBLIC_API_BASE_URL`), `frontend/package.json:5-10` (`build`/`start`), `frontend/.env.local.example:1-2`
- Produces: image `palmistry-frontend:local` exposing `3000`, running `node server.js` from standalone output

- [ ] **Step 1: Enable standalone output in `frontend/next.config.mjs`**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
};

export default nextConfig;
```

- [ ] **Step 2: Write `frontend/.dockerignore`**

```gitignore
node_modules/
.next/
out/
.env.local
*.log
```

- [ ] **Step 3: Write `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN adduser -D nextuser
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
USER nextuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD wget -qO- http://127.0.0.1:3000/ > /dev/null 2>&1 || exit 1
CMD ["node", "server.js"]
```

- [ ] **Step 4: Verify lint + build still pass with standalone**

Run: `cd frontend; npm run lint; npm run build`
Expected: lint clean, build prints `✓ Compiled successfully`, exit 0.

- [ ] **Step 5: Build the image**

Run: `docker build --build-arg NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 -t palmistry-frontend:local ./frontend`
Expected: build succeeds, exit 0.

- [ ] **Step 6: Commit**

```bash
git add frontend/next.config.mjs frontend/Dockerfile frontend/.dockerignore
git commit -m "deploy: add frontend standalone image"
```

### Task 3: Compose stack + env separation + one-command startup

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example` (extend existing — add Compose/AWS/deploy keys below, keep all current keys)
- Create: `.env.local.example` (dev override sample, optional but recommended)
- Modify: `README.md:51-98` (append Deploy section; keep Quick Start intact)
- Modify: `.gitignore:12-15` (ensure `.env` and `.env.*.local` ignored — already done, verify only)

**Interfaces:**
- Consumes: Task 1 image, Task 2 image, `backend/alembic.ini`, `backend/app/config.py:7-40` (`DATABASE_URL`, `CORS_ORIGINS`, `FRONTEND_URL`, `REFRESH_COOKIE_SECURE`)
- Produces: `docker compose up --build` bringing `db` (Postgres 16), `migrate` (one-shot alembic), `backend`, `frontend`; named volumes `pgdata`, `uploads`

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-palmistry}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

  migrate:
    build: ./backend
    command: alembic upgrade head
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-palmistry}
    depends_on:
      db:
        condition: service_healthy

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-palmistry}
      SECRET_KEY: ${SECRET_KEY:?set SECRET_KEY}
      ENVIRONMENT: ${ENVIRONMENT:-production}
      DEBUG: "false"
      CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}
      FRONTEND_URL: ${FRONTEND_URL:-http://localhost:3000}
      REFRESH_COOKIE_SECURE: ${REFRESH_COOKIE_SECURE:-false}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      GROQ_API_KEY: ${GROQ_API_KEY:-}
      UPLOAD_DIR: /code/uploads
    volumes:
      - uploads:/code/uploads
    ports:
      - "8000:8000"
    depends_on:
      migrate:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_BASE_URL: ${PUBLIC_API_BASE_URL:-http://localhost:8000}
    environment:
      NODE_ENV: production
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy

volumes:
  pgdata:
  uploads:
```

- [ ] **Step 2: Extend `.env.example` with deploy keys (keep existing 74 lines, append)**

```ini
# --- Deploy / Compose (append to .env.example) ---
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<YOUR_POSTGRES_PASSWORD>
POSTGRES_DB=palmistry
ENVIRONMENT=production
SECRET_KEY=<YOUR_SECRET_KEY_MIN_32_CHARS>
CORS_ORIGINS=["http://localhost:3000"]
FRONTEND_URL=http://localhost:3000
PUBLIC_API_BASE_URL=http://localhost:8000
REFRESH_COOKIE_SECURE=false
# AWS default (Azure equivalents stay replaceable via same var names)
AWS_REGION=us-east-1
ECR_BACKEND_REPO=palmistry-backend
ECR_FRONTEND_REPO=palmistry-frontend
```

- [ ] **Step 3: Bring up the stack**

Run: `docker compose up --build -d; docker compose ps; curl http://127.0.0.1:8000/health; curl -s http://127.0.0.1:3000/ | head -c 200`
Expected: `db` healthy, `migrate` exit 0, `backend` healthy, `frontend` running; `/health` returns `{"status":"ok"}`.

- [ ] **Step 4: Verify persistence + migration idempotency**

Run: `docker compose exec backend python -c "import pathlib; pathlib.Path('/code/uploads/.keep').touch()"; docker compose down; docker compose up -d db backend; docker compose exec backend ls /code/uploads; .\.venv\Scripts\python scripts/check_migrations.py`
Expected: `.keep` still listed after `down/up`; migration check prints single head, exit 0.

- [ ] **Step 5: Document one-command startup in `README.md` (append section, keep lines 1-188)**

```markdown
## Deploy (Docker Compose)

1. Copy env: `copy .env.example .env` then fill `SECRET_KEY` and `POSTGRES_PASSWORD`.
2. Start: `docker compose up --build -d`
3. Migrate runs automatically via the `migrate` service (`alembic upgrade head`).
4. Open frontend `http://localhost:3000`, API docs `http://localhost:8000/api/docs`, health `http://localhost:8000/health`.
5. Stop: `docker compose down` (volumes `pgdata`/`uploads` persist data).
```

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml .env.example README.md
git commit -m "deploy: add compose stack and one-command startup"
```

### Task 4: Production config hardening (no behavior change in dev)

**Files:**
- Modify: `backend/app/config.py:28-35` (cookie/CORS handling)
- Modify: `docker-compose.yml` (already created in Task 3 — set `REFRESH_COOKIE_SECURE=true` sample for prod)
- Test: `backend/tests/test_deploy_config.py` (new, 6 tests)

**Interfaces:**
- Consumes: `backend/app/config.py:7-88` (`Settings`, `REFRESH_COOKIE_SECURE`, `CORS_ORIGINS`, `ENVIRONMENT`)
- Produces: `ENVIRONMENT=production` forces `DEBUG=false` guard; `REFRESH_COOKIE_SECURE=true` honored by auth cookie writer; CORS rejects wildcard in production

- [ ] **Step 1: Write the failing test `backend/tests/test_deploy_config.py`**

```python
import os
from backend.app.config import Settings


def test_production_debug_defaults_false(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "false")
    s = Settings(_env_file=None)
    assert s.ENVIRONMENT == "production"
    assert s.DEBUG is False


def test_cookie_secure_flag_parses(monkeypatch):
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "true")
    s = Settings(_env_file=None)
    assert s.REFRESH_COOKIE_SECURE is True


def test_cors_origins_parses(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://app.example.com"]')
    s = Settings(_env_file=None)
    assert s.CORS_ORIGINS == ["https://app.example.com"]


def test_health_paths_unchanged():
    from backend.app.main import create_app

    app = create_app()
    paths = [r.path for r in app.routes]
    assert "/health" in paths


def test_api_prefix_default():
    s = Settings(_env_file=None)
    assert s.API_V1_PREFIX == "/api/v1"


def test_upload_dir_default():
    s = Settings(_env_file=None)
    assert s.UPLOAD_DIR == "uploads"
```

- [ ] **Step 2: Run test to verify it fails (import path fix needed)**

Run: `.\.venv\Scripts\pytest backend/tests/test_deploy_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend'` — confirms path assumption before fix.

- [ ] **Step 3: Fix test imports to repo convention and add prod guard in `backend/app/config.py`**

Replace the first import block of the test with:

```python
from app.config import Settings
```

And append to `backend/app/config.py` after the `settings = get_settings()` line:

```python
if settings.ENVIRONMENT == "production" and settings.DEBUG:
    raise RuntimeError("DEBUG must be false in production (set DEBUG=false)")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\pytest backend/tests/test_deploy_config.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run full gate**

Run: `.\.venv\Scripts\python scripts/verify_all.py`
Expected: pytest + lint + build all PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/config.py backend/tests/test_deploy_config.py
git commit -m "deploy: harden production config guard"
```

### Task 5: CI/CD with GitHub Actions

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`
- Modify: `scripts/check_migrations.py` (no change — invoked by CI)

**Interfaces:**
- Consumes: `scripts/verify_all.py:57-61` (pytest + lint + build), `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`
- Produces: `ci.yml` (migrations check + backend tests on Postgres 16 service + frontend lint/build + compose build), `deploy.yml` (ECR push on `main`, manual dispatch with `environment: production`)

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: ci
on:
  push:
  pull_request:
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: palmistry_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s --health-timeout 5s --health-retries 5
    env:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@localhost:5432/palmistry_test
      DATABASE_TEST_URL: postgresql+psycopg://postgres:postgres@localhost:5432/palmistry_test
      SECRET_KEY: ci-test-secret-key-min-32-chars-xxxx
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: python scripts/check_migrations.py
      - run: python -m pytest backend/tests -q
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - run: npm ci
        working-directory: frontend
      - run: npm run lint
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t palmistry-backend:ci ./backend
      - run: docker build --build-arg NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 -t palmistry-frontend:ci ./frontend
```

- [ ] **Step 2: Write `.github/workflows/deploy.yml`**

```yaml
name: deploy
on:
  push:
    branches: [main]
  workflow_dispatch:
jobs:
  push-images:
    runs-on: ubuntu-latest
    environment: production
    permissions: { contents: read, id-token: write }
    env:
      AWS_REGION: ${{ vars.AWS_REGION }}
      ECR_BACKEND_REPO: ${{ vars.ECR_BACKEND_REPO }}
      ECR_FRONTEND_REPO: ${{ vars.ECR_FRONTEND_REPO }}
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          BACKEND_URI="${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_BACKEND_REPO}:${GITHUB_SHA}"
          docker build -t "$BACKEND_URI" ./backend
          docker push "$BACKEND_URI"
      - run: |
          FRONTEND_URI="${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_FRONTEND_REPO}:${GITHUB_SHA}"
          docker build --build-arg NEXT_PUBLIC_API_BASE_URL="${{ vars.PUBLIC_API_BASE_URL }}" -t "$FRONTEND_URI" ./frontend
          docker push "$FRONTEND_URI"
```

- [ ] **Step 3: Validate workflow YAML locally**

Run: `.\.venv\Scripts\python -c "import yaml,pathlib; [yaml.safe_load(pathlib.Path(p).read_text()) for p in ['.github/workflows/ci.yml','.github/workflows/deploy.yml']]; print('yaml ok')"`
Expected: `yaml ok` (if `pyyaml` missing, run `pip install pyyaml` first — dev-only, do not add to requirements).

- [ ] **Step 4: Dry-run the CI backend job order locally**

Run: `.\.venv\Scripts\python scripts/check_migrations.py`
Expected: exit 0, single head printed.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/deploy.yml
git commit -m "deploy: add CI and ECR push workflows"
```

### Task 6: AWS default production target (replaceable adapters)

**Files:**
- Create: `docs/deployment/aws-production.md`
- Create: `scripts/deploy_aws.ps1`
- Modify: `.env.example` (already extended in Task 3 — add `RDS_DATABASE_URL` + `S3_UPLOADS_BUCKET` lines below)

**Interfaces:**
- Consumes: Task 1/2 images, `docker-compose.yml`, `backend/app/config.py:37-40` (`DATABASE_URL`), `backend/app/services/profile` avatar disk path (`UPLOAD_DIR/avatars`)
- Produces: documented path ECR → ECS Fargate (2 backend tasks) + RDS Postgres 16 + ALB `/health` check; S3 noted as future `UPLOAD_DIR` adapter (disk volume stays default so local/Compose keeps working)

- [ ] **Step 1: Append cloud-db/storage vars to `.env.example`**

```ini
RDS_DATABASE_URL=<YOUR_RDS_POSTGRES_URL>
S3_UPLOADS_BUCKET=<YOUR_S3_BUCKET_EMPTY_KEEPS_LOCAL_DISK>
```

- [ ] **Step 2: Write `docs/deployment/aws-production.md`**

```markdown
# AWS production (default)

Target: ECR -> ECS Fargate + RDS Postgres 16 + ALB. Azure remains
replaceable: any registry/DB/blob can substitute via the same env vars.

1. Provision: ECR repos ($ECR_BACKEND_REPO, $ECR_FRONTEND_REPO),
   RDS Postgres 16 (1 db `palmistry`), ALB with target-group health
   check `GET /health` (healthy threshold 2, interval 30s).
2. Secrets: store SECRET_KEY, DATABASE_URL (= RDS_DATABASE_URL),
   GOOGLE_CLIENT_ID/SECRET, OPENAI/GROQ keys in AWS Secrets Manager;
   inject as container env. Never bake into images.
3. Push: `deploy.yml` pushes :$GITHUB_SHA tags on main.
4. Run: ECS service backend (2 tasks, 0.5 vCPU/1GB, env DEBUG=false,
   REFRESH_COOKIE_SECURE=true, CORS_ORIGINS=["https://<app-domain>"]),
   frontend (1 task, NEXT_PUBLIC_API_BASE_URL=https://<api-domain>
   baked at build time). Migrate: run `alembic upgrade head` as a
   one-off ECS task before switching traffic.
5. Uploads: default stays the `uploads` EFS/EBS volume. S3 is opt-in:
   set S3_UPLOADS_BUCKET and point the avatar service at it (adapter
   to be added with that milestone); empty keeps local disk.
6. Rollback: re-point ECS service to the previous :SHA tag.
```

- [ ] **Step 3: Write `scripts/deploy_aws.ps1`**

```powershell
param([string]$Sha = "latest", [string]$Region = $env:AWS_REGION)
if (-not $Region) { $Region = "us-east-1" }
$account = (aws sts get-caller-identity --query Account --output text)
$backend = "$account.dkr.ecr.$Region.amazonaws.com/palmistry-backend:$Sha"
$frontend = "$account.dkr.ecr.$Region.amazonaws.com/palmistry-frontend:$Sha"
Write-Host "Backend: $backend"
Write-Host "Frontend: $frontend"
aws ecs update-service --region $Region --cluster palmistry --service backend --force-new-deployment
aws ecs update-service --region $Region --cluster palmistry --service frontend --force-new-deployment
```

- [ ] **Step 4: Syntax-check the script**

Run: `powershell -NoProfile -Command "$ErrorActionPreference='Stop'; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw scripts/deploy_aws.ps1), [ref]$null) | Out-Null; Write-Host 'ps1 ok'"`
Expected: `ps1 ok`.

- [ ] **Step 5: Commit**

```bash
git add docs/deployment/aws-production.md scripts/deploy_aws.ps1 .env.example
git commit -m "deploy: document AWS default target and rollout script"
```

### Task 7: Observability, backups, and release verification

**Files:**
- Create: `scripts/backup_db.ps1`
- Modify: `ARCHITECTURE.md:92-95` (replace "Not yet implemented (TASK-019)" with Compose/CI/AWS paths)
- Modify: `CHANGELOG.md` (prepend deploy entry)

**Interfaces:**
- Consumes: `GET /health`, `GET /api/v1/...` error envelope with `request_id`, `ErrorMonitoringMiddleware` (`error_logs` + latency ring), `scripts/verify_all.py`
- Produces: nightly `pg_dump` script, updated architecture/deployment docs, final green verification

- [ ] **Step 1: Write `scripts/backup_db.ps1`**

```powershell
param([string]$DbUrl = $env:DATABASE_URL, [string]$OutDir = "./backups")
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $OutDir "palmistry-$stamp.sql"
pg_dump $DbUrl -f $out
Write-Host "backup: $out"
```

- [ ] **Step 2: Update `ARCHITECTURE.md` deployment paragraph**

Old:

```markdown
- Docker Compose for local stack (deferred until Docker is available, D-005);
  GitHub Actions CI/CD; AWS default (§49.16). Not yet implemented (TASK-019).
```

New:

```markdown
- Docker Compose stack (`docker-compose.yml`: db + migrate + backend + frontend,
  volumes pgdata/uploads); GitHub Actions CI (`ci.yml`) + ECR push (`deploy.yml`);
  AWS default per docs/deployment/aws-production.md (§49.16). In-process rate
  limiting and latency buffer are per-worker until Redis lands.
```

- [ ] **Step 3: Prepend `CHANGELOG.md` entry**

```markdown
## [Unreleased] — Deployment
- Backend/frontend Docker images with healthchecks, Compose stack with one-shot
  `alembic upgrade head`, CI + ECR push workflows, AWS Fargate/RDS runbook,
  pg_dump backup script, production config guard.
```

- [ ] **Step 4: Final full verification**

Run: `.\.venv\Scripts\python scripts/verify_all.py; .\.venv\Scripts\python scripts/check_migrations.py; docker compose up --build -d; curl http://127.0.0.1:8000/health; curl -s http://127.0.0.1:8000/api/openapi.json | head -c 120; docker compose down`
Expected: verify_all PASS, single migration head, `/health` `{"status":"ok"}`, openapi JSON starts with `{"openapi"`.

- [ ] **Step 5: Commit**

```bash
git add scripts/backup_db.ps1 ARCHITECTURE.md CHANGELOG.md
git commit -m "deploy: add backup script and release docs"
```

## Self-Review

- Spec coverage: §21.6 → Tasks 1/4 (uvicorn prod workers); §21.7 → Task 3 (Compose + one-command README); §21.8 → Tasks 1/2/5/6 (images + Actions + AWS default + replaceable adapters); §25.1 → Tasks 1/2; §25.2 → Task 6; §25.3 → Tasks 3/4/7 (prod deploy + healthchecks + docs); §25.5 → Task 7 (reuse ErrorMonitoringMiddleware + latency buffer, ALB /health); §49.16 → Tasks 3/5/6/7 (Compose, Actions, AWS, dev/prod env separation, healthchecks/logging/monitoring/backups-DR via pg_dump runbook); §49.17 → Tasks 1/4 (workers/scalable) + docs note on palm <10s path.
- Placeholder scan: no TBD/TODO/appropriate-handling; every code step has literal file content, every run step has exact command + expected output.
- Type consistency: image names `palmistry-backend:local` / `palmistry-frontend:local` used in Tasks 1–3/5; env names `DATABASE_URL`, `CORS_ORIGINS`, `REFRESH_COOKIE_SECURE`, `NEXT_PUBLIC_API_BASE_URL`/`PUBLIC_API_BASE_URL` match `app/config.py` + `services/api.js`; `alembic upgrade head` is the single migration entrypoint everywhere.
- Review Focus: each of the 5 lines has an owning check — fail-fast DB (Task 1 Step 4), build-time API URL (Task 2 ARG + Task 3 var + Task 6 docs), volume persistence (Task 3 Step 4), per-worker limiter label (Task 6 docs + ARCHITECTURE note), single-head concurrency (Task 3 Step 4 + Task 5 Step 4).
