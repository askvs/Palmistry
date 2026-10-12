# Reference Datasets (`data/`)

> Integration specification for **TASK-005: Integrate Reference Datasets**.  
> Authoritative contract: `PALMISTRY_TAROT_AI_AGENT_SPEC.md` (§9.5, §18 TASK-005, §42).

---

## 1. Directory Structure

```text
data/
├── README.md                  # This reference dataset catalog
├── landmarks/                 # MediaPipe 21-point hand landmarks reference definitions
│   └── hand_landmarks_schema.json
├── palmistry/                 # Palm lines, mounts, and feature definitions
│   ├── lines_catalog.json     # Life, Head, Heart, Fate, Sun line descriptions & coordinates
│   └── mounts_catalog.json    # Jupiter, Saturn, Apollo, Mercury, Venus, Moon mounts
└── tarot/                     # Tarot deck schemas, card metadata, and spread geometries
    ├── rider_waite_deck.json  # 78 cards with upright/reversed meanings and arcana types
    └── spreads.json           # 6 standard spreads (Single, 3-Card, Relationship, Career, Celtic Cross, Life Path)
```

---

## 2. Mapping from Raw Datasets (`dataset/` -> `data/`)

The repository includes raw reference assets in [`dataset/`](file:///c:/Users/ASUS/Desktop/Palmistry/dataset) which are ingested or referenced into structured formats under `data/`:

| Raw Dataset Source (`dataset/`) | Purpose | Target Directory (`data/`) |
|---|---|---|
| `dataset/palmline/` (YOLOv5 formats: `Palm Line Detection.v2i`, `dataset_seimbang`) | YOLOv5 training & validation annotations for Life, Head, Heart, Fate lines | `data/palmistry/` |
| `dataset/Hands and palm images dataset/` | Varied palm morphology, lighting, skin tones, orientation tests | `data/landmarks/` & CV test fixtures |
| `dataset/Toroto card/Tarot Deck` | High-res card imagery (78 cards) | `frontend/public/cards/` & `data/tarot/` |
| `dataset/Toroto card/tarot meaning/` & `tarot_dataset_offline` | Symbolic card meanings, keywords, upright/reversed descriptions | `data/tarot/rider_waite_deck.json` |

---

## 3. Standard JSON Schemas for `data/`

### Tarot Deck Card (`rider_waite_deck.json`)
```json
{
  "id": "major-00-the-fool",
  "name": "The Fool",
  "number": 0,
  "arcana": "major",
  "suit": null,
  "keywords": ["beginnings", "innocence", "spontaneity", "free spirit"],
  "upright_meaning": "...",
  "reversed_meaning": "...",
  "image_path": "/cards/the_fool.webp"
}
```

### Palm Feature Definition (`lines_catalog.json`)
```json
{
  "id": "life_line",
  "name": "Life Line",
  "description": "Curves around the base of the thumb; represents vitality, energy, and life journey.",
  "significance": ["vitality", "stamina", "life changes", "physical wellbeing"]
}
```

---

## 4. Ingestion Workflow (TASK-005)

1. **Verify Raw Data**: Inspect card counts, line labels in `dataset/palmline`, and tarot text files.
2. **Normalize Assets**: Convert/standardize card metadata to `data/tarot/rider_waite_deck.json`.
3. **Build Seed Scripts**: Create `backend/scripts/seed_tarot.py` and `backend/scripts/seed_palm_features.py` to populate DB/vector catalogs.
4. **Automated Verification**: Test that all 78 tarot cards and 5 palm lines load cleanly without missing fields.
