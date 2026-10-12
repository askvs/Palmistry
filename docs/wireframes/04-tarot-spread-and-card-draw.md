# WF-04 — Tarot Spread Selection & Card Draw

Route: `/readings/tarot` · Role: User · Spec: FR-012..FR-016, §27.2, §49.6

## Step 1 — Deck & spread selection

```
┌──────────────────────────────────────────────────────────────┐
│  New Tarot Reading                    step 1 of 2  ●○        │
├──────────────────────────────────────────────────────────────┤
│  Deck                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ RWS cardart │  │ deck art    │  │ + more soon │           │
│  │ Rider-Waite │  │ (data-driven│  │             │           │
│  │ ✓ selected  │  │  catalog)   │  │             │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                              │
│  Spread                                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐       │
│  │ 🃏 Single Card│ │ ⧗ Three Card  │ │ ♥ Relationship│       │
│  └───────────────┘ └───────────────┘ └───────────────┘       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐       │
│  │ 💼 Career     │ │ ✚ Celtic Cross│ │ 🛤 Life Path   │       │
│  └───────────────┘ └───────────────┘ └───────────────┘       │
│  Question (optional)  [__________________________]           │
│                    [ Shuffle & Continue → ]                  │
└──────────────────────────────────────────────────────────────┘
```

## Step 2 — Card draw (fan interaction)

```
┌──────────────────────────────────────────────────────────────┐
│  Three Card Reading — tap 3 cards     step 2 of 2  ●●        │
│                                                              │
│   ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐                  │
│   │🂠 ││🂠 ││🂠 ││🂠 ││🂠 ││🂠 ││🂠 ││🂠 ││🂠 ││🂠 │  ← shuffled fan   │
│   └──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘                  │
│                                                              │
│   Your cards:                                                │
│   ┌────────┐  ┌────────┐  ┌────────┐                         │
│   │ 🃜 VIII │  │ 🂡 rev. │  │ 🃝 X    │  ← flip animation      │
│   │Strength│  │Tower ⟲ │  │Wheel ▦ │                         │
│   └────────┘  └────────┘  └────────┘                         │
│   Positions: Past · Present · Future                         │
│                 [ Generate Reading ✨ ]                      │
└──────────────────────────────────────────────────────────────┘
```

## States & behavior

- Shuffle uses cryptographically secure Fisher-Yates server-side; deterministic seed only in test mode (FR-013).
- Reversed-card toggle shown on draw; reversals feed interpretation.
- Celtic Cross renders its 10-position layout diagram before draw.
- LOADING: "Interpreting…" overlay with staged progress; async job pattern like palm flow.
- ERROR: session expired / spread state lost → resume or restart options.
