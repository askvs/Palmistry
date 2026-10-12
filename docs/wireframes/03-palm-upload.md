# WF-03 — Palm Upload Workflow

Route: `/readings/palm` · Role: User · Spec: FR-006..FR-011, §27.1, §49.4, §49.5

## Step 1 — Upload

```
┌──────────────────────────────────────────────────────────────┐
│  New Palm Reading                     step 1 of 2  ●○        │
├──────────────────────────────────────────────────────────────┤
│        ┌──────────────────────────────────────────┐          │
│        │            ⬆                             │          │
│        │     Drag & drop or [ Browse files ]      │          │
│        │   JPG · JPEG · PNG · WEBP — max 10 MB    │          │
│        │        📷 [ Use camera ]                 │          │
│        └──────────────────────────────────────────┘          │
│  Hand: (•) Left   ( ) Right        ← dominant-hand note     │
│  Tips: flat hand, fingers together, good lighting,           │
│        full palm visible in frame                            │
│  ┌ preview ┐  palm_left.jpg   3.2 MB ✓ valid   [ remove ]    │
│                        [ Start Analysis → ]                  │
└──────────────────────────────────────────────────────────────┘
```

## Step 2 — Processing (async job)

```
┌──────────────────────────────────────────────────────────────┐
│  Analyzing your palm…                    job #a1b2 · queued  │
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  52%                                   │
│  ✓ Upload validated                                          │
│  ✓ Preprocessing (orientation, denoise, contrast)            │
│  ● Feature extraction & line detection…                      │
│  ○ Interpretation                                            │
│  You can leave this page — we'll notify you. [ View history ]│
└──────────────────────────────────────────────────────────────┘
```

## States & behavior

- Client + server validation: MIME type **and** file signature (§49.4); 415 on unsupported, 413 on oversize.
- ERROR cases: invalid image → inline guidance to retake; model/inference error → retry with same upload (§23.2).
- Original preserved; normalized copy used for inference (§49.4).
- Results route to `/readings/[id]` (WF-05) with Life/Head/Heart/Fate/Sun lines,
  palm shape, finger structure + per-feature confidence (§49.5 outputs).
