# WF-06 — Reading History & Recommendations

Routes: `/history`, `/recommendations` · Role: User · Spec: FR-035, FR-034, §28.2

## Reading History

```
┌──────────────────────────────────────────────────────────────┐
│  Reading History                                             │
│  Filter: [ All ▼ ] [ Palm ] [ Tarot ]   Search [______] 🔍   │
├──────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐   │
│ │ 🖐 Palm · 2026-08-18 14:02        Score 71 [High]  →   │   │
│ ├────────────────────────────────────────────────────────┤   │
│ │ 🃏 Tarot · Three Card · 2026-08-20 09:15  78 [High] →  │   │
│ ├────────────────────────────────────────────────────────┤   │
│ │ ✚ Tarot · Celtic Cross · 2026-08-21 22:40 ⏳ pending   │   │
│ └────────────────────────────────────────────────────────┘   │
│              ‹ 1 2 3 ›                       (page/page_size)│
└──────────────────────────────────────────────────────────────┘
```

- LOADING: list skeleton. EMPTY: "No readings yet — start your first palm or tarot reading" + CTA.
- ERROR: failed-to-load banner with retry. Pending jobs show live status badge.
- Cursor pagination if feed volume grows (§49.14).

## Recommendations

```
┌──────────────────────────────────────────────────────────────┐
│  Your Recommendations              Based on 12 readings      │
├──────────────────────────────────────────────────────────────┤
│ ┌─ 🌱 Personal Growth ────────────────── relevance 84 ─────┐ │
│ │ Evening journaling aligned with your Head Line patterns… │ │
│ │ [ Mark helpful 👍 ] [ Not relevant 👎 ]                  │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌─ 💼 Career ─────────────────────────── relevance 77 ─────┐ │
│ ┌─ ♥ Relationships ───────────────────── relevance 72 ─────┐ │
│ ┌─ 🎯 Goal Alignment · Spiritual Development ──────────────┐ │
│  ℹ Reflective suggestions, not guarantees (§49.19)           │
└──────────────────────────────────────────────────────────────┘
```

- Grouped by FR-034 types; each item shows relevance + feedback capture (feeds guidance-relevance scoring FR-040).
- EMPTY: recommendations unlock after first completed reading.
