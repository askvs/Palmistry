# WF-05 — Reading Display

Route: `/readings/[id]` · Roles: User (owner), Tarot Reader (assigned) · Spec: FR-017..FR-021, FR-032/033, §27.3

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back    Palm & Tarot Reading          2026-08-21 14:30    │
├──────────────────────────────────────────────────────────────┤
│ ┌─ Summary strip ───────────────────────────────────────────┐│
│ │ Type: Combined   Insight Score: 78 / 100  [High]          ││
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░  score breakdown ▼                    ││
│ │   Palm Confidence 30% ▓ 82 · Tarot Relevance 25% ▓ 74 ·   ││
│ │   Personality 20% ▓ 80 · Context 15% ▓ 71 · Consistency   ││
│ │   10% ▓ 76                     (weights per §49.9)        ││
│ └───────────────────────────────────────────────────────────┘│
│                                                              │
│ ┌─ Palm Analysis ────────────────┐ ┌─ Tarot ───────────────┐ │
│ │ [annotated palm image]         │ │ drawn cards w/ posn   │ │
│ │ Life Line   ● strong, long     │ │ Strength (upright)    │ │
│ │ Head Line   ● balanced         │ │ Tower (reversed)      │ │
│ │ Heart Line  ● deep             │ │ Wheel (upright)       │ │
│ │ Fate Line   ○ faint (0.61)     │ │ position meanings …   │ │
│ │ Sun Line    ○ not detected     │ │                       │ │
│ │ Shape: Earth · Fingers: long   │ │                       │ │
│ │ model: cnn-v1.2 conf 0.83      │ │ model: gpt-… prompt v3│ │
│ └────────────────────────────────┘ └───────────────────────┘ │
│                                                              │
│ ┌─ Insights (tabs) ─────────────────────────────────────────┐│
│ │ [Personality][Relationships][Career][Finance][Health]     ││
│ │ [Personal Growth][Opportunities]   ← FR-021 categories    ││
│ │                                                           ││
│ │ Personality: reflective introvert with disciplined …      ││
│ └───────────────────────────────────────────────────────────┘│
│ ┌─ Guidance & Recommendations ──────────────────────────────┐│
│ │ • Growth: journaling practice aligned with Head Line …    ││
│ │ • Career: creative leadership window (Q4 reflection) …    ││
│ └───────────────────────────────────────────────────────────┘│
│  [ Export PDF ] [ Export Excel ] [ Save to History ✓auto ]   │
│  ℹ Interpretive guidance for self-reflection — not fact,     │
│    diagnosis, or professional advice. (§49.19)               │
└──────────────────────────────────────────────────────────────┘
```

## States & behavior

- LOADING: skeleton sections; partial streaming for LLM text where supported.
- PENDING (async job): progress card linking from dashboard/history.
- ERROR: interpretation failed → retry button preserves inputs; partial results shown with failure badges.
- Every AI block shows model/version metadata + confidence/relevance (rule 0.1 #11).
- Score labels: 0–39 Low · 40–69 Moderate · 70–84 High · 85–100 Very High.
