# WF-08 — Role Dashboards (Tarot Reader / Spiritual Consultant / Admin)

Spec: FR-036, FR-037, FR-038, Module 10 · RBAC per §49.3

## Tarot Reader — `/reader`

```
┌──────────────────────────────────────────────────────────────┐
│  Reader Workspace                       [ New session log ]  │
├──────────────┬───────────────────────────────────────────────┤
│ ▸ Sessions   │ KPIs: sessions today 6 · avg rating 4.6 ·     │
│   Analytics  │ completion 92% · assigned users 24            │
│   Reports    │ ┌─ Reading analytics (Chart.js) ────────────┐ │
│   Assigned   │ │ readings/day bar · spread mix doughnut    │ │
│     users    │ └───────────────────────────────────────────┘ │
│              │ ┌─ Engagement insights ─────────────────────┐ │
│              │ │ most-drawn cards, reversal rate, repeat   │ │
│              │ └───────────────────────────────────────────┘ │
│              │ ┌─ Session tracking table ──────────────────┐ │
│              │ │ user · spread · started · status · report │ │
│              │ └───────────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────┘
```

## Spiritual Consultant — `/consultant`

```
┌──────────────────────────────────────────────────────────────┐
│  Consultant Console                                          │
├──────────────┬───────────────────────────────────────────────┤
│ ▸ User trends│ ┌─ User trend analysis ─────────────────────┐ │
│   Guidance   │ │ cohort sentiment/trend lines per user set │ │
│   effectiveness│ └──────────────────────────────────────────┘ │
│   Consults   │ ┌─ Guidance effectiveness ──────────────────┐ │
│              │ │ 👍/👎 feedback ratios per guidance theme   │ │
│              │ └───────────────────────────────────────────┘ │
│              │ ┌─ Consultation insights ───────────────────┐ │
│              │ │ recurring concerns, recommended focus     │ │
│              │ └───────────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────┘
```

## Administrator — `/admin`

```
┌──────────────────────────────────────────────────────────────┐
│  Admin Console                          env: staging ▾       │
├──────────────┬───────────────────────────────────────────────┤
│ ▸ Users      │ KPIs: DAU 1,204 · readings today 312 ·        │
│   Analytics  │ API p95 380 ms · error rate 0.4%              │
│   Readings   │ ┌─ Platform analytics (Chart.js/Plotly) ────┐ │
│   System     │ │ signups, retention, reading volume        │ │
│   Config     │ └───────────────────────────────────────────┘ │
│   Audit logs │ ┌─ User management table ───────────────────┐ │
│              │ │ search · role badge · status · [suspend]  │ │
│              │ └───────────────────────────────────────────┘ │
│              │ ┌─ System reports & health ─────────────────┐ │
│              │ │ service status grid · queue depth · jobs  │ │
│              │ └───────────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────┘
```

## States & behavior

- All three: LOADING skeletons per widget; EMPTY zero-data states; ERROR per-widget retry.
- Role gating enforced by backend; unauthorized route → 403 page with explanation (§49.18).
- Admin destructive actions require confirmation dialogs; audit-logged.
