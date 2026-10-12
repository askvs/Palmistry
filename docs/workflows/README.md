# Workflow Planning — Palmistry & Tarot Intelligence Platform

Planning companion to `docs/wireframes/`. Canonical flows from spec §6, §27, §28,
decomposed into implementable slices with screen ↔ API ↔ job mappings.

## Flow index

| File | Flow | Source |
|---|---|---|
| `core-user-journey.md` | Registration → profile → reading → dashboard → export | §28.1 |
| `palm-analysis-workflow.md` | Upload → preprocess → features → interpretation | §27.1 |
| `tarot-reading-workflow.md` | Deck → shuffle → spread → draw → interpretation | §27.2 |
| `combined-intelligence-workflow.md` | Palm + tarot → insights → scoring → recommendations | §27.3 |

## Screen ↔ workflow traceability

| Screen (wireframe) | Feeds flow | Primary API surface (planned `/api/v1/...`) |
|---|---|---|
| 01 auth | core journey | `auth/register`, `auth/login`, `auth/oauth/*`, `auth/refresh` |
| 02 profile | context for all personalization | `profile/me`, `profile/preferences` |
| 03 palm upload | palm analysis | `palm/uploads`, `palm/analyses/{id}` (+ job status) |
| 04 tarot draw | tarot reading | `tarot/decks`, `tarot/spreads`, `tarot/sessions` |
| 05 reading display | combined intelligence | `readings/{id}`, `readings/{id}/insights` |
| 06 history/recommendations | synthesis outputs | `readings?status=`, `recommendations` |
| 07 user dashboard | aggregation | `dashboard/user` |
| 08 role dashboards | role analytics | `dashboard/reader|consultant|admin` |
| 09 reports/export | reporting | `reports`, `reports/{id}/export?format=pdf|xlsx` |

## Cross-cutting interaction contract

1. **Async jobs:** palm analysis, interpretation, report generation run as background
   jobs with status polling (`GET .../jobs/{id}`) and notification on completion.
2. **Error envelope:** every failure returns `{code, message, request_id, fields?}` (§49.14).
3. **States:** every screen implements LOADING / SUCCESS / EMPTY / ERROR (rule 0.1 #10).
4. **Metadata:** AI outputs carry model id/version, prompt version, confidence/relevance.
5. **Safety copy:** interpretive-guidance disclaimer appears wherever generated content shows (§49.19).

## Implementation slice order (Milestone 1 → 4)

```
M1: auth slice → profile slice            (vertical, end-to-end)
M2: palm slice → tarot slice → reading record + report stub
M3: interpretation → personality → trends → scoring → recommendations
M4: dashboards → notifications → reports/exports → hardening → deploy
```

Each slice ships UI states + API + tests together (rule 0.1 #8).
