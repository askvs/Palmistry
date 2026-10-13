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
