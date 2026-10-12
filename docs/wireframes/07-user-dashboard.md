# WF-07 — User Dashboard

Route: `/dashboard` · Role: User · Spec: FR-035, Module 10

```
┌──────────────────────────────────────────────────────────────┐
│  Welcome back, Aarav ✦                  [ New Palm ] [New Tarot]
├──────────────┬───────────────────────────────────────────────┤
│ SIDE NAV     │  Stat cards                                   │
│ ▸ Overview   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ │
│   Readings   │  │ 12     │ │ 78     │ │ 5-day  │ │ 3 new   │ │
│   History    │  │ total  │ │ avg    │ │ streak │ │ insight │ │
│   Insights   │  │reading │ │ score  │ │        │ │ updates │ │
│   Recommen-  │  └────────┘ └────────┘ └────────┘ └─────────┘ │
│   dations    │                                               │
│   Reports    │  ┌─ Insight trend (Chart.js line) ──────────┐ │
│   Profile    │  │ 80┤            ╭─╮                      │ │
│              │  │ 60┤      ╭─────╯  ╰──╮                   │ │
│  🔔 3 unread │  │ 40┤ ╭──╯             …                  │ │
│              │  │   └──┬─────┬─────┬─────┬────┬            │ │
│              │  └──────Jun───Jul────Aug────Sep──Oct──────────┘ │
│              │                                               │
│              │  ┌─ Recent readings ──────── View all → ────┐ │
│              │  │ 🃏 Career Spread · 2d ago · 78 High  →   │ │
│              │  │ 🖐 Palm · 4d ago · 71 High           →   │ │
│              │  └───────────────────────────────────────────┘ │
│              │  ┌─ Personality snapshot ────────────────────┐ │
│              │  │ radar: openness 82 · discipline 74 ·      │ │
│              │  │ empathy 68 … (top strengths/weaknesses)   │ │
│              │  └───────────────────────────────────────────┘ │
│              │  ┌─ Daily guidance ──────────────────────────┐ │
│              │  │ "Patience with ongoing projects serves    │ │
│              │  │  you this week."  [ Save ] [ Dismiss ]    │ │
└──────────────┴───────────────────────────────────────────────┘
```

## States & behavior

- LOADING: stat skeletons + chart placeholder.
- EMPTY (new user): hero onboarding card "Take your first reading" with two CTAs; zero-state charts.
- ERROR: widget-level error cards with per-widget retry (dashboard must not fail as a whole).
- Charts: Chart.js for standard charts; Plotly reserved for advanced analytics (§49.1).
- Notification bell → dropdown panel (FR-039 types), links to full notifications view.
