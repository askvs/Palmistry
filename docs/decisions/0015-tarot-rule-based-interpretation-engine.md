# D-015 — Tarot card interpretation: deterministic rule engine until LLM synthesis (TASK-008)

**Date:** 2026-09-11
**Status:** Accepted

**Context:** FR-016 requires tarot card interpretation as part of TASK-007, while
TASK-008 owns the AI (LLM) interpretation engine. TASK-007 must be demonstrable
end-to-end without external LLM credentials.

**Decision:**
- `backend/app/services/tarot/interpretation.py` implements a deterministic,
  rule-based interpretation engine (`TarotInterpretationEngine` v1.0.0) layered on
  the reference catalog (`data/tarot/rider_waite_deck.json`, `data/tarot/spreads.json`).
- Per card: orientation-aware (upright/reversed) keywords, core meaning,
  position-aware context sentence, domain guidance (love / career / spiritual from
  catalog `domains`), fortune-telling, and expanded light/shadow meanings.
- Per spread: arcana balance, elemental balance (Fire/Water/Air/Earth with dominant
  and missing elements), reversal analysis, and repeating numerology patterns,
  composed into an opening/body/closing narrative, summary, and guidance lines.
- Question text or spread category selects a domain focus; unknown spreads resolve
  leniently by id/name prefix, falling back to a synthetic spread definition.
- Payloads carry §49.19 safety disclaimers and rule 11 metadata (engine name/version,
  model name/version, UTC timestamp, data-completeness relevance score).
- REST surface: `GET /api/v1/tarot/decks` (FR-012), `GET /api/v1/tarot/spreads`
  (FR-015), `POST /api/v1/tarot/draw` (FR-013/014/016), `POST /api/v1/tarot/interpret`
  (FR-014/016). Seeded draws are accepted for test-mode reproducibility (FR-013).
- `POST /api/v1/readings/tarot` now runs the engine; the raw card selection stays at
  `result.cards` for backward compatibility and the full synthesis lives under
  `result.interpretation`.

**Consequences:**
- Interpretations are honest, catalog-grounded, and fully testable without mocks or
  fabricated model outputs (rule 12); the relevance metric measures catalog data
  completeness, not claimed AI confidence.
- TASK-008 will layer LLM-based personalization on top of this structured payload;
  the engine output doubles as the retrieval/validation substrate for that step.
