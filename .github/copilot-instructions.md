# GitHub Copilot Instructions — Palmistry & Tarot Intelligence Platform

## Project Overview
This repository implements the Palmistry & Tarot Intelligence Platform according to `PALMISTRY_TAROT_AI_AGENT_SPEC.md` and `AGENTS.md`.

## Coding Conventions
- **Backend (Python 3.11/3.12, FastAPI, SQLAlchemy 2, Alembic)**:
  - All versioned REST endpoints live under `/api/v1`.
  - Schema validation with Pydantic v2.
  - Return the standard error envelope `{ "code": str, "message": str, "request_id": str, "fields"?: dict }` for all errors.
  - Database timestamps are always timezone-aware UTC (`datetime.now(timezone.utc)`).
  - Use Alembic migrations (`backend/alembic`) for any database changes.
  - RBAC checks use `get_current_user` and `require_roles(...)`.
- **Frontend (Next.js 16, Pages Router, React 19, Tailwind CSS v4)**:
  - Central API calls use `src/services/api.js` which automatically attaches Bearer tokens and maps backend errors to `ApiError`.
  - Every page/feature must support 4 UI states: LOADING, SUCCESS, EMPTY, ERROR.
  - Silent token refresh is handled through `AuthProvider` (`src/hooks/useAuth.js`).
- **Testing**:
  - Run backend unit tests: `.\.venv\Scripts\pytest backend/tests`
  - Run frontend lint: `npm run lint` (inside `frontend/`)
  - Run master verification: `.\.venv\Scripts\python scripts/verify_all.py`
