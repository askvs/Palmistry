# D-014 — Avatars: full image upload on local disk, served via authenticated endpoint

**Date:** 2026-08-31
**Status:** Accepted

**Context:** WF-02 shows a "Change avatar" action, i.e. "profile customization"
in FR-005. The project owner explicitly chose full image upload over a preset
icon set or deferral. No object storage (S3/GCS) credentials exist, Docker is
absent (D-005), and image processing dependencies are deferred to the palm
analysis milestone (D-006).

**Decision:**
- `PUT /api/v1/profile/avatar` accepts multipart uploads (JPG/PNG/WEBP) up to
  `AVATAR_MAX_SIZE_MB` (default 5, below the §37.8 platform image cap of 10 MB).
  `python-multipart` was added to `requirements.txt` for FastAPI multipart parsing.
- The client-supplied filename and MIME type are **not trusted**: the real content
  type is derived from magic bytes (JPEG `FF D8 FF`, PNG signature, RIFF+WEBP);
  anything else is rejected with 415 `UNSUPPORTED_AVATAR_FORMAT`; oversized
  uploads get 413 `AVATAR_TOO_LARGE`; an empty body is rejected as 415.
- Files are stored on local disk under `UPLOAD_DIR/avatars/<profile_id>.<ext>`
  (default `backend/uploads`, git-ignored). One avatar per profile: uploading a
  file with a different extension deletes the old file; the DB stores only the
  key in `profiles.avatar_key`.
- Serving happens through `GET /api/v1/profile/avatar`, which requires the Bearer
  access token (avatars are not public). The frontend fetches it as a blob with
  the in-memory token and renders an object URL. The response carries
  `ETag: "<updated_at epoch>"` + `Cache-Control: private, max-age=31536000`, and
  the frontend appends `?v=<version>` so a browser cache entry is per-version;
  matching `If-None-Match` returns 304.
- No Pillow/PIL dependency was added — signature sniffing needs only byte
  comparisons. Real image processing arrives with palm analysis (D-006).
- Frontend `services/api.js` gained PATCH + FormData body handling and an
  `apiBlob` helper; `services/profile.js` wraps the profile API.

**Consequences:**
- Local disk storage is single-machine; when the Compose stack or a cloud
  deployment lands (TASK-019), the same service functions can be re-pointed at
  object storage without changing the API contract.
- Files are keyed by profile id, so uploads cannot collide across users; stale
  files with changed extensions are removed on replace and on delete.
- Because avatars are Bearer-gated, they cannot be hot-linked from other origins.
