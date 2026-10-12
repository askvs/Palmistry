# Core User Journey (spec §28.1)

```text
Open Platform
   ↓
Register / Login ──────────── WF-01 · POST /api/v1/auth/*
   ↓
Authenticate (JWT access + rotating refresh; Google OAuth2)
   ↓
Create / Customize Profile ── WF-02 · PUT /api/v1/profile/me
   ↓
Choose Reading Type
   ├── Palm  → WF-03 (upload → async analysis)
   └── Tarot → WF-04 (deck → shuffle → spread → draw)
   ↓
Generate Interpretation ───── async job → WF-05 reading display
   ↓
View Personalized Insights ── FR-021 categories on WF-05 tabs
   ↓
View Recommendations ──────── WF-06 · GET /api/v1/recommendations
   ↓
Save Reading to History ───── automatic on completion
   ↓
Open Dashboard / Report ───── WF-07 · WF-09
   ↓
Export PDF / Excel ────────── FR-041/042 signed download
```

## Step contracts

| Step | Success signal | Failure mode & UX |
|---|---|---|
| Register/Login | JWT issued, redirect `/dashboard` or onboarding | 401 banner, 429 rate-limit notice, OAuth provider error retry |
| Profile | Preferences persisted (UTC timestamps) | Save keeps form state, toast + retry |
| Choose type | Workflow session created | Navigation guard resumes draft session |
| Generation | Job completes → reading persisted | Retry preserves inputs; partial results flagged |
| Export | Signed URL downloads file | Regenerate action; expired-link message |

## First-run vs returning user

- **First-run:** register → onboarding wizard (interests/goals/preferences) → dashboard empty-states guide to first reading.
- **Returning:** login → dashboard with streak, pending jobs, new recommendations.

## Notification touchpoints

Reading completed · report ready · daily guidance (opt-in) — in-app first, email via SendGrid default (§49.13).
