# Combined Intelligence Workflow (spec §27.3, §49.9)

```text
Palm Intelligence + Tarot Intelligence
              ↓
AI Interpretation (retrieval-grounded, LLM, structured JSON)
              ↓
User Context / Profile (age group, interests, goals, preferences,
                        recent reading history, current reading type)
              ↓
Personality Intelligence (profiling · strengths · weaknesses ·
                          behavioral insights · development recs)
              ↓
Trend Analysis (life path · opportunities · challenge forecast ·
                growth potential — reflective, never guaranteed)
              ↓
Spiritual Guidance Scoring
   Overall Insight Score =
       0.30 × Palm Analysis Confidence
     + 0.25 × Tarot Interpretation Relevance
     + 0.20 × Personality Alignment
     + 0.15 × User Context Relevance
     + 0.10 × Reading Consistency        (each normalized 0–100)
   Labels: 0–39 Low · 40–69 Moderate · 70–84 High · 85–100 Very High
              ↓
Recommendation Engine (growth · relationships · career ·
                       goal alignment · spiritual development)
              ↓
Reading Synthesis (single coherent narrative across all blocks)
              ↓
Dashboard / Reports / Notifications
```

## Component sourcing

| Component | Weight | Source |
|---|---:|---|
| Palm Analysis Confidence | 30% | CV pipeline mean feature confidence |
| Tarot Interpretation Relevance | 25% | relevance scorer vs. question/context |
| Personality Alignment | 20% | profile-model agreement with reading |
| User Context Relevance | 15% | context-matching score |
| Reading Consistency | 10% | agreement with prior readings |

Single-source readings: absent components use neutral defaults and the UI
discloses reduced coverage; weights remain fixed (FR-033).

## Persistence contract

Synthesized reading stores: component scores, overall score + label, model/prompt
versions, input context hash, disclaimer copy — enabling trend reports (FR-061)
and consistency scoring over time.

## Safety rails (§49.19)

Health → non-diagnostic + professional-care pointer · Finance → not investment advice ·
Future → reflective possibilities only · tone avoids fear/absolutes. Disclaimer renders
on reading display, recommendations, and all exports.
