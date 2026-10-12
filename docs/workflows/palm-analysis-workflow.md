# Palm Analysis Workflow (spec §27.1, §49.4, §49.5)

```text
INPUT        Palm image (JPG/JPEG/PNG/WEBP ≤ 10 MB)
   ↓
VALIDATION   MIME + file-signature check; 413/415 rejections
   ↓
STORAGE      original preserved (audit-safe) + normalized copy
   ↓
PREPROCESS   orientation correction → resize → RGB → denoise →
             contrast normalization → segmentation → normalize
             (OpenCV + Pillow + Albumentations)
   ↓
LANDMARKS    MediaPipe hand landmarks (33-point)
   ↓
FEATURES     Life · Head · Heart · Fate · Sun lines;
             palm shape; finger structure
   ↓
MODELS       PyTorch transfer-learning CNN (line/feature);
             YOLO for region/object detection where needed
   ↓
OUTPUT       per-feature result + confidence + model version
   ↓
INTERPRET    LLM interpretation (retrieval-grounded, §49.8)
   ↓
DOWNSTREAM   personality → trends → scoring → recommendations
   ↓
PERSIST      reading record → dashboard/history/report
```

## Job lifecycle

| State | Trigger | UI (WF-03 step 2) |
|---|---|---|
| `queued` | upload accepted → `POST /api/v1/palm/uploads` | queued badge |
| `preprocessing` | worker picks up | checklist item ✓ |
| `extracting` | landmarks/features running | progress 30–70% |
| `interpreting` | LLM stage | progress 70–95% |
| `completed` | reading persisted | link to `/readings/{id}` |
| `failed` | validation/model/storage error | error card + retry |

## Confidence & metadata (rule 0.1 #11)

Every feature result carries `{feature, detected, confidence, model_id, model_version}`;
interpretation carries `{model, prompt_version, created_at}`. Palm Analysis Confidence
feeds the 30% weight of the Insight Score (§49.9).

## Error handling (§23.2, §49.18)

- Invalid format → 415 with guidance; oversize → 413.
- Inference error → job `failed`, bounded exponential retry on transient provider failures; never blind-retry non-idempotent steps.
- Storage failure → 503 controlled response, upload retained locally for retry.
