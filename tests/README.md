# Top-Level Test Suite (`tests/`)

Per **Spec §0.3** and **Architecture Decision D-002**:
- **Backend Unit & Acceptance Tests**: Live in [`backend/tests/`](file:///c:/Users/ASUS/Desktop/Palmistry/backend/tests) (managed via pytest against PostgreSQL `palmistry_test`).
- **Frontend Unit & Component Tests**: Live in [`frontend/`](file:///c:/Users/ASUS/Desktop/Palmistry/frontend) (Vitest / React Testing Library to be added in Milestone 4).
- **Top-Level `tests/`**: Reserved for cross-service, End-to-End (E2E), and system integration testing (Playwright, full-stack API contract suites).

## Directory Organization

```text
tests/
├── README.md                  # This test organization guide
├── e2e/                       # Playwright browser automation tests (Milestone 4)
└── integration/               # Multi-service contract integration tests
```

## Running Backend Tests

```powershell
.\.venv\Scripts\pytest backend/tests
```

## Running Full Verification

```powershell
.\.venv\Scripts\python scripts/verify_all.py
```
