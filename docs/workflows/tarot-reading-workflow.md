# Tarot Reading Workflow (spec §27.2, §49.6)

```text
INPUT        Reading request (question optional)
   ↓
DECK         Rider-Waite-Smith default; data-driven catalog
   ↓
SHUFFLE      cryptographically secure Fisher-Yates (server);
             deterministic seed only in test mode (FR-013)
   ↓
SPREAD       Single · Three Card · Relationship · Career ·
             Celtic Cross · Life Path — each with positions,
             labels, meanings, interpretation order (§49.6)
   ↓
DRAW         user selects N cards; upright/reversed flag
   ↓
INTERPRET    per-card meaning → position meaning → spread synthesis
             (knowledge-base retrieval precedes LLM generation)
   ↓
CONTEXT      profile context: age group, interests, goals,
             preferences, recent history (FR-018)
   ↓
OUTPUT       structured reading (Pydantic-validated JSON)
   ↓
DOWNSTREAM   scoring (25% Tarot Interpretation Relevance) →
             recommendations → synthesis → history/report
```

## Session state machine

```
created → shuffled → drawing (partial picks) → drawn → interpreting → completed
                                      └────────────────────→ abandoned (TTL)
```

- Draft sessions resumable within TTL; draw order recorded.
- Reversal policy: ~configurable probability, surfaced in UI (WF-04) and persisted.

## API surface (planned)

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/tarot/decks` | deck catalog |
| `GET /api/v1/tarot/spreads` | spread definitions incl. positions |
| `POST /api/v1/tarot/sessions` | create session (deck+spread) → shuffled order server-side |
| `POST /api/v1/tarot/sessions/{id}/draw` | commit card selection |
| `POST /api/v1/tarot/sessions/{id}/interpret` | start interpretation job |
| `GET /api/v1/readings/{id}` | completed reading |

## Fairness & integrity

- Shuffle executes server-side; client never learns deck order before draw commits.
- Test mode seed recorded for reproducibility; production draws are not reproducible by design.
