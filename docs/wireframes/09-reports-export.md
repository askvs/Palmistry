# WF-09 — Reports & Export

Route: `/reports` · Roles: all authenticated (scope per role) · Spec: FR-040..FR-042, Module 12

```
┌──────────────────────────────────────────────────────────────┐
│  Reports                                                     │
│  Type: [All ▼] Palmistry · Tarot · Personality · Guidance ·  │
│                Insight trend                                 │
├──────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐   │
│ │ 📄 Palmistry Report — Aug 2026        generated 08-21  │   │
│ │    12 readings · avg score 76        [PDF] [XLSX] [👁] │   │
│ ├────────────────────────────────────────────────────────┤   │
│ │ 📄 Tarot Report — Q3                    ⏳ generating   │   │
│ └────────────────────────────────────────────────────────┘   │
│  [ + Generate new report ]                                   │
│      ┌ modal ─────────────────────────────┐                  │
│      │ Type     [Personality ▼]           │                  │
│      │ Range    [Last 30 days ▼]          │                  │
│      │ Format   (•)PDF ( )Excel           │                  │
│      │           [Cancel] [ Generate ]    │                  │
│      └────────────────────────────────────┘                  │
│  ℹ Scheduled reports appear here automatically when enabled. │
└──────────────────────────────────────────────────────────────┘
```

## States & behavior

- Generation is an async background job with progress state (rule 0.1 #16); ready → in-app + email notification (§49.13).
- LOADING: row-level spinner; ERROR: failed badge + regenerate action.
- PDF via document export pipeline; Excel (.xlsx) export (FR-062/063).
- Download links expire (signed URLs when object storage enabled).
- EMPTY: no reports yet → CTA to generate from existing readings.
