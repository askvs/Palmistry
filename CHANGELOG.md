# Changelog

All notable implementation changes to the Palmistry & Tarot Intelligence Platform.

## [Unreleased] — CI fixes (backend tests + AWS deploy gate)
- **Backend CI fixed on clean checkouts.** The `test_palm_analysis.py` sample
  tests open images from the gitignored, local-only `dataset/` folder — present
  locally, absent on GitHub Actions — so 12 of them failed on every run since
  the initial commit. They are now skipped when their sample file is missing
  (`requires_palmar_sample` / `requires_dorsal_sample` /
  `requires_horizontal_sample`) and still run and pass locally.
- **AWS deploy workflow gated.** `deploy.yml` failed at
  `configure-aws-credentials` ("Input required and not supplied: aws-region")
  on every push because the AWS variables/secrets were never configured. The
  job now skips until `vars.AWS_REGION` is set, then activates as before.

## [Unreleased] — System Reports module (admin monitoring)
- **Admin-only System Reports** surface in the console (`/admin/reports`,
  nav entry "System Reports"), with four endpoints behind `require_admin`:
  - `GET /api/v1/admin/reports/overview?days=7|30` — total registered users,
    total analyses, successful and failed analyses (period + all-time),
    per-type breakdown, and the date failure tracking began.
  - `GET /api/v1/admin/reports/health` — backend and database status from live
    checks (real `SELECT 1`, measured latency); AI availability is a
    configuration check stated honestly (no live upstream ping exists).
  - `GET /api/v1/admin/reports/errors?days=&limit=` — recent operational
    errors and failed analyses with category, sanitized short description
    (whitespace-collapsed, 200-char cap), method/path/status, occurrences,
    first/last seen and acknowledged state.
  - `GET /api/v1/admin/reports/performance?days=` — average/p50/p95/max API
    response time, request and 5xx counts from persisted samples, plus
    average/p95/max analysis-generation time per reading type.
- **New measurements feeding the reports**: failed palm/tarot generations are
  recorded as `analysis_failed` error rows (deduplicated with occurrences);
  `readings.duration_ms` (migration `0014_system_reports`) captures per-reading
  generation time; the monitoring middleware buffers API latency samples and
  flushes them to the new `performance_samples` table (on report reads and app
  shutdown, with 90-day retention).
- **Honest empty states.** Metrics with no data return `no_data` plus nulls
  (and the UI shows an explanation) rather than misleading zeros.

## [Unreleased] — Google Calendar removal & manual Meet links
- **Google Calendar integration removed.** The consultant "connect calendar"
  flow, automatic event creation on accept/cancel, sync statuses and the
  `/consultants/me/google-calendar*` routes are gone; migration
  `0013_remove_google_calendar` drops `consultant_calendar_connections` and
  the booking columns `meet_code`, `google_event_id`, `google_calendar_id`,
  `calendar_sync_status`, `calendar_synced_at`, `calendar_error`.
- **Manual Google Meet link sharing.** Either party can paste the meeting
  link for a session; the consultant can add, update or clear it any time
  before the session starts
  (`PATCH /api/v1/consultants/me/bookings/{id}/meeting-link`). Both sides
  keep the "Join Google Meet" button, which unlocks 30 minutes before the
  start.

## [Unreleased] — Deployment
- Backend/frontend Docker images with healthchecks, Compose stack with one-shot
  `alembic upgrade head`, CI + ECR push workflows, AWS Fargate/RDS runbook,
  pg_dump backup script, production config guard.

## [Unreleased] — Four Role Capability Completion

### Changed — Administrator no longer participates in sessions
- **Booking and hosting removed from the admin role.** `require_consultant_role`
  (`/consultants/me/...` studio routes) and the new `require_session_role`
  (`/bookings` seeker hub + booking creation) no longer accept `admin`, and every
  admin override inside `app/services/booking/service.py` was deleted along with
  the `_is_admin` helper. Booking and session management is now strictly reader /
  consultant work, matching §49.3 ("Administrator: user management, platform
  analytics, configuration, system reports, audit logs").
- **Read-only session oversight instead.** New `GET /api/v1/admin/analytics/sessions`
  returns aggregated counts (by status, upcoming confirmed, pending requests,
  consult profiles, average rating, unique seekers) plus the next scheduled
  sessions with their consultant, time, duration and calendar-sync state. The
  admin console and the admin dashboard render it in a panel with no action
  buttons; the booking/session nav entries and the consultant request panel were
  removed from the admin experience.

### Added — Administrator console (`/admin/*`)
- **New route space with its own shell** (`layouts/AdminLayout.js`): Overview,
  User Governance, Platform Analytics, Security & Errors, System. Role-guarded
  (`/admin` prefix → `admin` only) and enforced server-side by `require_admin`.
- **Live RBAC permission matrix.** `GET /api/v1/admin/permissions` documents the
  real `require_*` bundles from `app/auth/rbac.py` plus the two session bundles,
  so the console explains the enforcement instead of a second source of truth.
- **Authentication settings.** `GET /api/v1/admin/settings/auth` reports token
  policy, refresh cookie, OAuth provider readiness, the admin self-signup policy
  and rate limits. Secrets are surfaced as presence flags only.
- **System configuration & release.** `GET /api/v1/admin/settings/system`
  reports environment, version, API prefix, database target, alembic revision,
  AI provider/model, upload limits, scheduler job registration and process
  uptime.
- **Error, security & performance monitoring.** New `error_logs` table (migration
  `0011`) plus `ErrorMonitoringMiddleware`, which records unhandled 5xx
  responses, rejected authentication (401), forbidden access (403) and
  rate-limited requests (429), deduplicated per
  (kind, method, path, status, message) with an `occurrences` counter.
  Endpoints: `GET /admin/errors`, `GET /admin/errors/stats`,
  `POST /admin/errors/{id}/acknowledge` (audited, never destructive) and
  `GET /admin/system/performance` (in-process latency percentiles and slowest
  routes).

### Added — Tarot reader spread authoring
- **Reader-authored spreads** (`custom_spreads` table, migration `0012`): a
  named sequence of 1–10 card positions, each with its own meaning. Endpoints
  `GET/POST/PATCH/DELETE /api/v1/reader/spreads`, with private/shared
  visibility so a spread can be reused by other readers.
- **They run through the same engine.** `interpret_draw` /
  `interpret_explicit_cards` accept a `spread_override`, so a reading taken with
  a custom spread gets the full arcana, elemental, reversal, numerology and
  narrative treatment — no special case.
- **Spread Studio UI** (`/reader/spreads`): ordered position editor with
  reordering, rename, description, visibility and retire.

### Added — Tarot reader report management & engagement
- **Reading report management.** `GET /api/v1/reader/reports` lists every
  platform reading with its owner's email, spread name, card count and review
  state, filterable by type, status, review state, owner and title. The
  `/reader/reports` page adds PDF and Excel export plus one-click certification
  (the existing review endpoint).
- **User-engagement insights.** `GET /api/v1/reader/engagement` reports distinct
  and returning querents, active/first-time split for the window, readings per
  querent, review coverage, top querents and most-drawn spreads.

### Added — Consultant client roster & goal progress
- **Live client roster.** `GET /api/v1/consultant/clients` returns the real
  seekers who have guidance threads, with their recorded interests, spiritual
  goals, thread counts (open/resolved) and reading activity. The client-management
  permission follows thread participation — the guidance queue is shared by all
  staff roles — and is documented as such.
- **Goal progress panel.** The client detail page now pairs each recorded goal
  with that client's real activity instead of an invented completion score.

### Fixed — schedulers double-start broke the test suite
- `start_scheduler` and `start_booking_scheduler` called
  `scheduler.start()` unconditionally. `TestClient` runs the app lifespan on every
  fixture entry while the module keeps one scheduler instance, so the second
  entry raised `SchedulerAlreadyRunningError` and every subsequent test errored.
  Both are now idempotent (`add_job(..., replace_existing=True)` already made
  registration idempotent; only the start needed guarding).

## [Unreleased] - Live Consultation & Booking Module

### Fixed — booking enum columns reverted to non-native (VARCHAR)
- **Booking module 500s ("An unexpected error occurred") across the consultant/reader
  dashboards and the consultant directory.** The ORM models in `app/models/booking.py`
  declared all five booking enum columns (`booking_status`, `booking_origin`,
  `booking_slot_status`, `booking_calendar_sync_status`, `booking_note_visibility`) with
  `native_enum=True`, but every migration (`0007`, `0010`) created those columns as plain
  `VARCHAR` (`native_enum=False, create_type=False`) and the newer `countered` / `proposal`
  values were never added to any native PG enum type. Any query binding one of the new
  values (e.g. the consultant session board filtering `status="countered"`) could raise at
  the database layer, surfacing as the generic 500 in every panel that embeds the booking
  "Sessions" surface. Models now match the migrations (`native_enum=False`). No new
  migration required — the columns were already `VARCHAR`.

### Added — seeker/consultant separation, propose-a-time & chat
- **Clear role separation.** Fixed a shell-routing bug where `/consultants` (seeker
  directory) and `/consultant-studio` were captured by the `/consultant*` prefix and
  rendered inside the FR-037 consultant workspace shell; `_app.js` now matches only
  `/consultant` and `/consultant/*`. The consultant workspace is now guarded at the
  layout level (`ConsultantLayout` calls `useRoleGuard`) and `/consultant-studio` guards
  itself, so a seeker who opens a consultant URL is redirected to their own dashboard
  (backend RBAC remains authoritative).
- **Seeker-proposed meeting times (hybrid).** Alongside booking a published slot, a
  seeker can now propose a custom date/time from the consultant page
  (`POST /api/v1/consultants/{id}/bookings/propose`). Such bookings carry
  `origin="proposal"` and no slot.
- **Counter-propose negotiation.** Either party can suggest a different time until both
  agree. New `countered` booking status + `last_proposed_by_id`; `pending` awaits the
  consultant, `countered` awaits the seeker. Endpoints: consultant
  `POST /api/v1/consultants/me/bookings/{id}/counter`; seeker
  `POST /api/v1/bookings/{id}/counter` and `POST /api/v1/bookings/{id}/confirm`.
- **Per-booking chat.** A direct seeker↔consultant thread scoped to one booking
  (`booking_messages` table; `GET/POST /api/v1/bookings/{id}/messages`), visible only to
  that booking's seeker, its consultant, and admins — separate from the standalone
  FR-037 guidance threads.
- **Migration `0010_booking_proposals_and_chat`**: `bookings.slot_id` nullable; adds
  `origin` + `last_proposed_by_id`; new `booking_messages` table. Run
  `alembic upgrade head` before using these features.

### Changed
- **Renamed the booking vocabulary from "expert" to "consultant"** across the whole
  module so the people seekers book are called consultants everywhere (UI, routes,
  API, code, and database). This is distinct from, and does not touch, the existing
  Spiritual Consultant workspace (FR-037) under `/consultant/*`.
  - Frontend routes: `/experts` → `/consultants`, `/experts/[expertId]` →
    `/consultants/[consultantId]`, `/expert-studio` → `/consultant-studio`. Files and
    components renamed to match (`ExpertSessionsPanel` → `ConsultantSessionsPanel`,
    `ExpertCard` → `ConsultantCard`, etc.).
  - Backend API: the booking routers now mount under `/api/v1/consultants` (plural),
    kept distinct from the singular `/api/v1/consultant` FR-037 namespace.
  - Database (migration `0009_rename_expert_to_consultant`): tables `expert_profiles`
    → `consultant_profiles` and `expert_calendar_connections` →
    `consultant_calendar_connections`; every `expert_id` column → `consultant_id`;
    related indexes/constraints renamed. Pure rename — no data reshaped.
  - `GOOGLE_CALENDAR_REDIRECT_URI` default now points at `/consultant-studio`. Update
    the matching Authorized redirect URI in the Google Cloud OAuth client, and your
    `.env`, accordingly.

### Added
- **Live consultation & booking module** - an independent module layered alongside the
  existing palmistry/tarot features. No existing flow was modified; the only
  cross-cutting change is additive (six new `notification_type` enum values) plus one
  latent `app/main.py` startup bug that the new scheduler surfaced (see Fixed).

#### Backend
- **Models** (`backend/app/models/booking.py`): `ConsultantProfile`, `AvailabilityRule`,
  `AvailabilitySlot`, `Booking`, `BookingEvent`, `SessionNote`, `SessionFeedback` and
  `ConsultantCalendarConnection`, plus the `BookingStatus`, `SlotStatus`,
  `CalendarSyncStatus` and `NoteVisibility` enums. The status flow is
  `pending -> accepted | rejected -> completed | cancelled`, enforced by
  `ALLOWED_TRANSITIONS` in the service layer and backed by a partial unique index so a
  slot can only back one live booking.
- **Availability engine** (`app/services/booking/availability.py`): consultants describe
  their week with `AvailabilityRule` rows; `materialise_rule` expands a rule into
  concrete UTC `AvailabilitySlot` rows ahead of a 21-day horizon, applying the rule's
  own timezone per date so DST shifts correctly. A scheduler job rolls the horizon
  forward daily.
- **Google Calendar / Meet** (`app/services/booking/google_calendar.py`):
  - Creates a real Calendar v3 event with `conferenceData.createRequest`, so Google
    generates the Meet link that is then persisted on the booking.
  - Deliberately dependency-free: the only HTTP client is `httpx` (already a project
    dependency) and JWTs are signed with `PyJWT`, so `requirements.txt` is unchanged.
  - Two credential modes: a per-consultant OAuth2 refresh token (events land on the
    consultant's own calendar, so the meeting belongs to them) with a platform
    service-account calendar (`GOOGLE_SERVICE_ACCOUNT_FILE`) as fallback.
  - Every failure is non-fatal: the booking still succeeds and
    `calendar_sync_status` / `calendar_error` record the outcome.
- **Booking service** (`app/services/booking/service.py`): consultant profile CRUD,
  availability management, the booking lifecycle with cancellation windows, consultant
  session notes (private or shared with the seeker), and seeker feedback with a
  recomputed `avg_rating` / `review_count`.
- **Notifications**: booking events ride the existing in-app `Notification` channel, so
  they appear in the header bell and Notification Center for every role.
- **Scheduler** (`app/services/booking/scheduler.py`): reminders (24h + 1h lead,
  idempotent), availability rollout, and auto-completion of sessions that have ended.
- **API** (`app/api/v1/endpoints/booking.py`): 39 routes across `/consultants`,
  `/consultants/me/...` and `/bookings`, mounted in `app/api/v1/router.py`.
- **Migration** `0007_booking`, hand-written because `alembic/env.py` only imports a
  subset of models (autogenerate would emit wrong output). It also extends
  `notification_type`.
- **Tests** (`backend/tests/test_booking_endpoints.py`): 52 tests covering all six
  phases, including a mocked Google Calendar client (no network required).

#### Frontend
- **`src/services/booking.js`** - one thin function per endpoint plus combined
  module-level loaders so `useAsyncData` gets stable references.
- **`src/lib/datetime.js`** - native `Date` / `Intl` helpers. The app ships no date
  library, so these centralise every booking date formatting need.
- **`src/components/booking/`** - `shared.js` (status labels and tones, `SessionCard`,
  `ConsultantCard`, a from-scratch `SlotPicker` day strip plus time chips, `RatingStars`,
  `FeedbackForm`, `BookingTimeline`), `SeekerSessionsPanel.js`, `ConsultantSessionsPanel.js`.
- **Pages**: `/consultants` (directory with search / specialisation / price filters),
  `/consultants/[consultantId]` (profile, availability calendar, booking form), `/sessions`
  (seeker hub: upcoming/past, Join Google Meet, cancel, feedback, session notes,
  history) and `/consultant-studio` (consultant console: profile editor, weekly availability
  rules plus slot manager, booking requests, sessions and notes, Google Calendar
  connect).
- **Dashboards**: the seeker panel is mounted under `UserDashboard`; the consultant panel
  (pending requests plus upcoming sessions) under `ReaderDashboard` and
  `ConsultantDashboard`.
- **Navigation** (`src/lib/roles.js`): new `consultants`, `sessions` and `consultant_studio`
  nav entries, and `/consultant-studio` added to `STAFF_ONLY_PREFIXES`.
- **Icons**: `VideoIcon` added to `src/components/icons.js` for the Join Meet button.

### Fixed
- **`app/main.py` startup hook was dead code.** The app defines both a `lifespan`
  handler and an `@app.on_event("startup")` hook, and Starlette gives the lifespan
  precedence - so the on_event hook never ran. It also imported
  `SessionLocal` from `app.db.session`, which does not exist (the module only exposes
  `get_engine()` / `get_db()`), so even if it had run it would have raised
  `ImportError`. The practical effect was that **the notification scheduler had
  never started** in any environment. Both schedulers now start from `lifespan`.

### Changed
- `.env.example` and `.env` document the booking and Google Calendar settings.
- `docs/BOOKING_MODULE_PLAN.md` records the design and phase plan.


## [Unreleased] — Spiritual Consultant Frontend Experience (FR-037)

### Added
- **Consultant application shell** (`frontend/src/layouts/ConsultantLayout.js`): a dedicated
  sidebar + header shell for the whole `/consultant/*` route space, selected by `pages/_app.js`.
  Brand "Palmistry & Tarot", primary nav (Dashboard, Clients, Consultations, Insights, Reports),
  secondary nav (Notifications, Profile), a consultant profile card with an availability dot, a
  contextual header (page title, breadcrumb, client search, notification bell, profile menu) and a
  responsive drawer sidebar below `lg` — the sidebar never permanently occupies screen space.
- **Consultant routes** (`frontend/src/pages/consultant/`): `index.js` (→ dashboard),
  `dashboard.js`, `clients.js`, `clients/[clientId].js`, `consultations.js`,
  `consultations/[consultationId].js`, `insights.js`, `reports.js`. All are guarded by
  `useRoleGuard`, which now resolves staff-only prefixes as well as the seeker-only pages.
- **Route access rules** (`frontend/src/lib/roles.js`): `STAFF_ONLY_PREFIXES` blocks all of
  `/consultant/*` for every role except `spiritual_consultant`; `pageAccess` and the new
  `blockedPageInfo` handle both the prefix rules and the existing seeker-only pages so the
  dashboard's `?blocked=` notice works for staff routes too.
- **Consultant service layer** (`frontend/src/services/consultant.js`): the single entry point for
  every consultant surface, plus `services/consultantDemoData.js` for the deterministic demo
  dataset. Everything already exposed by the backend is used as-is
  (`/consultant/consultations`, `/consultant/insights/{effectiveness,trends,consultations}`,
  `/consultant/me/bookings`, `/reports/reading/{id}/pdf`).
- **Consultant components** (`frontend/src/components/consultant/`): `ClientTrendChart`
  (chart.js line chart with client / category / time filters), `UpcomingConsultations`,
  `RecentClients`, `ClientOverview`, `ClientDirectory`, `PalmAnalysisSummary`, `TarotHistoryTable`,
  `AIInsightCard`, `GuidanceEffectiveness`, `ConsultationInsights`, `ConsultationWorkspace`,
  `ConsultantNotes`, `StartConsultationDialog`, `ConsultationReportsTable`, `shared`.
- **Chart helpers** (`frontend/src/lib/chartjs.js`): registers the chart.js scales/controllers the
  app already ships and centralises the line/bar option presets so the consultant charts share the
  existing data-viz language.
- **Display formatters** (`frontend/src/lib/format.js`): initials, relative dates, date, datetime,
  percentage and greeting helpers used by the consultant console.
- **Local PDF writer** (`frontend/src/lib/pdf.js`): a dependency-free fallback used only for
  consultation reports that are not attached to a real reading (the backend PDF exporter remains
  the primary path via `services/reports.js`).
- **New icons** (`frontend/src/components/icons.js`): `LayoutGridIcon`, `SlidersIcon`,
  `ArrowUpDownIcon`, `ShareIcon`, `PlusIcon`, `SettingsIcon`, `SparklesIcon`, `BellIcon`,
  `PlayIcon`.

### Changed
- `frontend/src/pages/_app.js`: picks `ConsultantLayout` for `/consultant/*` routes and `MainLayout`
  for everything else; no other routing behaviour changed.
- `frontend/src/hooks/useRoleGuard.js`: redirects staff-only routes (via the prefix rules) to the
  dashboard with a `?blocked=` notice, and reports `router.asPath` so dynamic routes are named
  correctly.
- `frontend/src/layouts/MainLayout.js`: staff roles with a dedicated route space (the consultant)
  get a direct entry point to it, since the new shell hides the public nav.
- `frontend/src/pages/dashboard.js`: reads the blocked-page reason through `blockedPageInfo` so
  the notice works for consultant and seeker routes alike.
- `frontend/src/pages/consultant-studio.js`: moved the `StatCard` import to
  `@/components/dashboards/shared` (it is not exported from `@/components/ui`), which had been
  breaking `next build`.

### Source labelling
Every consultant payload carries `source: "live" | "demo" | "local"`. Live slices come from the
existing consultant API; demo slices come from the deterministic dataset because the platform has
no client roster, per-client readings or consultation-scheduling endpoint yet
(`GET /readings/{id}` only allows the owner, tarot readers and admins, and
`GET /consultants/me/bookings` 404s for consultants without a consultant profile). Notes and started
sessions persist to `localStorage` until the backend supports them. Each slice renders a small
"Demo data" / "Live data" / "Saved on this device" badge, so no placeholder is presented as a live
platform metric.

## [Unreleased] — Dashboard AI Assistant (overall analysis for every role)

### Added
- **Dashboard AI Assistant** (`backend/app/services/assistant/`, `api/v1/endpoints/assistant.py`):
  a grounded, role-scoped "overall analysis" chatbot available on `/dashboard` for all four
  roles. Two entry points: `POST /api/v1/assistant/chat` (free question, or
  `intent: "overview"` for the full narrative) and `GET /api/v1/assistant/context` (the
  snapshot the assistant reasons over, also used to drive the UI).
- **Role-scoped snapshot** (`services/assistant/context.py`): seekers see only their own
  readings, recommendations and guidance threads; tarot readers see the platform reading
  queue; spiritual consultants see the guidance queue and their responsiveness; admins see
  platform growth, engagement, role mix and the audit trail. The snapshot is built from the
  same services each role's dashboard already calls, so the assistant can never reach data
  the role could not read itself (§49.3).
- **Grounded prompting** (`services/assistant/chat.py`): the snapshot is serialised into the
  system prompt as an explicit fact list, with rules forbidding invented or estimated
  numbers and a verbatim §49.19 disclaimer. Answers fall back to the deterministic rule
  engine when no LLM credentials are configured.
- **`DashboardAssistant`** (`frontend/src/components/dashboards/DashboardAssistant.js`):
  renders the live metric chips, highlight notes and role-specific suggested prompts, plus
  a rolling transcript with LOADING/ERROR/EMPTY states, an "Overall analysis" action and a
  Clear button. Wired into `pages/dashboard.js` for every role.
- **`frontend/src/services/assistant.js`**: `fetchAssistantContext` / `askAssistant`.
- **`backend/tests/test_assistant_endpoints.py`**: 18 tests covering authentication, the
  422 validation paths, role scoping (a seeker never sees platform totals), grounding,
  conversation-history stamping, and one chat turn per role.

### Changed
- `AssistantError` is registered in `DOMAIN_ERRORS` so assistant failures share the
  standard error envelope (`{code, message, request_id}`).

## [Unreleased] — Notification System: In-App Only + Header UI

### Added
- **Header notification bell** (`components/ui/NotificationBell.js`): unread badge and
  dropdown wired into `MainLayout` for every signed-in role (`user`, `tarot_reader`,
  `spiritual_consultant`, `admin`). Polls `/notifications/unread-count`, lists the most
  recent in-app notifications, supports per-item and "mark all read", and links to the
  Notification Center. Hidden for guests.
- **"Mark all read"** action on the Notification Center page (`/notifications`).

### Changed
- **Email delivery removed everywhere; in-app notifications are the only channel for all
  roles.** Deleted the `EmailService`, the email templates, and the email branch of
  `trigger_notification` / `create_email_delivery`.
- **Notification Center preferences fixed**: the handler previously built
  `new FormData(<checkbox>)` on change and never persisted; replaced with per-toggle
  optimistic updates hitting `PUT /notifications/preferences`. The 8am `daily_guidance`
  and `reading_reminder` scheduler jobs and admin announcements still populate
  notifications for every role.
- **In-app preferences now persist**: `insight_updates`, `spiritual_growth`, and
  `platform_announcements` previously no-oped on the backend; they now map to the profile
  flags (`notify_insights`, `notify_growth`, `notify_announcements`).
- **Fixed the `notifications.metadata` column/field mismatch** that broke the
  notification list: the model mapped to a non-existent `notification_metadata` column
  (migration 0006 defines `metadata`) and `NotificationOut` read SQLAlchemy's declarative
  `MetaData`. The table column is now `metadata` and the response field is
  `notification_metadata`.
- Removed the "Email Notifications" preference toggle from the UI and `email_notifications`
  from the notification preference schemas.

### Added
- **Event-driven in-app notifications for all roles.** New activity now reaches the roles
  that act on it, not just seekers:
  - **New user registers** → admins (`new_user`).
  - **New analysis (palm/tarot reading)** → the owner gets `reading_completed`; tarot readers
    and spiritual consultants get `new_reading` to review.
  - **Consultation question** → spiritual consultants get `new_question`; a consultant's
    reply nudges the seeker (`insight_update`).
  Delivery runs in an isolated session and is fully failure-tolerant, so a notification can
  never break (or roll back) the request that triggered it. Notification types added:
  migration `0008_notification_event_types`.

### Fixed
- **404 on `/api/v1/notifications`**: the notifications router was mounted without its
  `/notifications` prefix, so every Notification Center / bell call 404'd. Routes now live
  under `/api/v1/notifications` (list, `unread-count`, `read-all`, `{id}/read`,
  `preferences`, `admin/announcements`).
- **Stale dev server swallowing all event notifications** (the reported "no notification in
  the consultant portal on a new question"): the backend runs **without `--reload`**
  (`run_dev_server.bat`), and a duplicate instance had been started under the *system*
  Python, so no rows were ever written to `notifications`. Both stale instances were stopped
  and the server restarted from the project venv; a live end-to-end check (seeker posts a
  consultation question → the spiritual consultant's bell/unread-count increments) passes.

## [0.12.0] — 2026-09-26 — UI/UX Production Polish & Backend Error-Handling Cleanup

### Added
- **Shared UI kit** (`frontend/src/components/ui/`): `Button` (primary/secondary/ghost/
  danger/dangerGhost/accent variants, `loading`, icon slots, Link-aware), `PageHeader`,
  `Panel`, `Badge`, `ConfirmDialog` (accessible, Esc-to-close), `Toast` provider +
  `useToast` (auto-dismiss, `aria-live`), and canonical async states
  (`EmptyState`, `ErrorState`, `InlineError`, `Spinner`, `SkeletonRow`, `SkeletonCards`).
  Single source for all interactive chrome — replaces five drifting button recipes,
  four loading patterns and per-page `PANEL`/`INPUT_CLASS` constants.
- **Semantic design tokens** in `globals.css` `@theme`: `primary-*` (brand violet) and
  `accent-*` (tarot gold) scales plus `fade-in`/`rise-in` animation tokens. All new code
  uses semantic tokens; the old violet/purple/amber mix is retired.
- **Shared `AiInsightsPanel`** (`components/ai/`): one implementation of the AI
  interpretation section (loading/error/retry/summary/body/guidance/domain insights/
  disclaimer) used by palm, tarot and reading-detail pages — removes three ~130-line
  drifting copies.
- **`lib/roles.js`**: single registry of role labels, badge tones, icons and dashboard
  CTAs (previously duplicated with drift in MainLayout, dashboard.js and profile.js).
- **Extended inline SVG icon set** (40+ lucide-style strokes in `components/icons.js`);
  emoji removed from all UI chrome (buttons, badges, empty states, chat trigger, stat
  cards, timeline dots).

### Changed
- All pages and widgets migrated to the kit: landing, auth portals + `PortalAuthForm`,
  all four role dashboards, LifeTrend dashboard, readings archive + detail, palm, tarot
  ritual, profile, personality, 404, `ChatBot`, recommendations, `BackendStatus`.
  Consistent `rounded-3xl` cards, one primary CTA per view, visible `focus-visible`
  rings, `cursor-pointer`, unified input styling with labeled fields, MainLayout-width
  containers everywhere.
- **Fabricated UI data removed**: palm "Insight Chart" bars derived from insight string
  length, tarot chart scores from list index, and the four fake `setTimeout` "phases"
  during palm analysis — replaced with honest request-lifecycle loading states.
- `alert()` / `window.confirm()` flows replaced with toasts + `ConfirmDialog` for
  deletes, exports, notes and guidance; failures now surface cause + recovery hint.
- Reading exports show real in-flight state (buttons disable; active one spins).
- Role switcher on dashboard rebuilt from `lib/roles` with `aria-pressed` pills;
  `LifeTrendDashboard` moved to `components/dashboards/` and restyled to theme
  (chart.js line chart on primary/accent series, legend + tooltips, skeleton/empty/error
  states) via `useAsyncData`.
- `MainLayout`: prefix-aware active nav (`/readings/palm` highlights Palm Reading), kit
  focus rings, single role registry.

### Fixed
- Mojibake export buttons in tarot ("ðŸ“„ Export PDF Dossier" / "ðŸ“Š Export Excel
  Workbook") — proper labeled buttons with icons.
- `font-serif` headings that silently rendered Georgia instead of Fraunces (now
  `font-display`) across dashboard/personality/tarot surfaces.
- Split sentence in tarot selection ("This is the next slot you" + dangling "draw from
  the arc below.").
- `RecommendationCard` dead buttons (Accept/Dismiss/Complete rendered empty labels) and
  broken "ed" status chips — now readable and wired.
- `animate-fadeIn` class that never existed (now defined `fade-in`/`rise-in` tokens).
- Latent JSX syntax error at the tail of `profile.js` (stray top-level element) and its
  unused import.

### Removed
- Dead code: unused `SpreadBoard` tarot component, `ChartToggle` + fabricated insight
  charts, duplicate `useApi` hook (migrated to `useAsyncData`), unreachable "raw" form
  mode in personality, stale `palm.js.bak`/`tarot.js.bak` page backups, duplicate
  singular `components/dashboard/` folder, stray progress stubs inside `frontend/`.
- Ghost root Next.js app (self-referential `src/pages/dashboard.js` stub + root
  `package.json`) that shadowed the real `frontend/` app.
- Backend config drift: unused MongoDB/Redis settings removed from `config.py` and
  `.env.example`.

### Backend
- Consolidated the 12 per-exception JSON handlers in `app/main.py` into one shared
  domain-error handler (identical `{code, message, request_id}` contract; behavior
  verified by the full pytest suite, exit 0).
- Repo hygiene: ad-hoc backend test scripts moved to `backend/scripts/` (as
  `probe_*.py`), generated test PDFs deleted, root `_filelist*`/`_ps_probe*` artifacts
  removed.

## [0.11.0] — 2026-09-26 — Feature-Based Life Trend Analysis Engine (Milestone 3, FR-034..FR-036)

### Added
- **LifeTrendEngine** (`backend/app/services/trends/engine.py`, v1.0.0, method
  `feature_based_trend_scoring`): transparent, unsupervised trend analysis over a user's
  stored reading history. Per-reading 0–1 signals extracted from `Reading.result` JSONB
  (palm CV line strengths, mount/shape elements, digit ratio; tarot arcana/suit/court
  ratios, domain focus, relevance) → recency-weighted aggregation (90-day half-life) into
  6 life domains (career, relationships, emotional, growth, vitality, creativity) →
  direction (rising/stable/declining from recent-half vs older-half delta), strength
  (evidence amount × coverage), confidence (readings analyzed × coverage), growth
  potential composite, life-path summary, opportunities and challenges with per-item
  signal attribution, and a per-reading trend history series for charting.
- **Signal-level explainability**: every trend, opportunity and challenge lists the
  contributing user signals (e.g. "Heart line depth & clarity: 0.72 avg across 3
  reading(s)"); profile goals/interests keyword-align to domains as self-declared focus
  signals with a documented +0.075/matched-text boost (capped 0.15).
- **`feature_vector` in every response**: flattened domain scores/strengths/momentum plus
  raw per-reading signal series — the training input shape for a future supervised
  forecasting model once historical snapshots accumulate. Deliberately NO supervised ML
  accuracy claims: the platform has no ground-truth life outcomes or long per-user time
  series; fixed domain weights are documented interpretation choices, not learned
  parameters.
- **Optional LLM narrative pass**: `services/life_trends.py` may rephrase only the
  explanation paragraph around the computed facts (grounded prompt, best-effort,
  deterministic text on failure). Scores are never LLM-generated.
- **User dashboard: Personality Insights panel** (FR-035) —
  `frontend/src/components/dashboards/PersonalityInsightsCard.js`: compact
  strengths/growth-areas/behavioral summary built on demand from the user's latest
  completed palm reading (combined with the latest tarot reading when present) via the
  existing `POST /personality/profile` engine; loading/error/empty states; links to the
  full `/personality` profile. No palm reading → CTA instead of fabricated data.

### Changed
- `GET /api/v1/life-trends` response schema (`LifeTrendOut`) extended backward-compatibly
  with `current_trends[]` (score/direction/momentum/strength/confidence/explanation/
  signals), `opportunities[]`, `challenges[]`, `history[]`, `data_coverage`,
  `feature_vector`, `method`, `engine_version`. The previous LLM-text + reading-count
  fallback behavior (~35% complete) is replaced by the real signal pipeline.
- User dashboard (FR-035) now surfaces the life trend analysis
  (`components/dashboards/LifeTrendDashboard.js`: life path, trend cards with
  score/strength/confidence meters, opportunities, challenges, trend-over-time Chart.js
  line chart when ≥2 readings exist, data-coverage footer, §49.19 disclaimer).

### Tests & Verification
- 12 engine/orchestrator/endpoint tests in `backend/tests/test_life_trend_analyzer.py`
  (signal extraction from real stored payload shapes, determinism, per-user divergence,
  goal boosts, direction from recency, evidence attribution, auth requirement).
- Full backend suite green against the `palmistry_test` Postgres database; `next build`
  clean. Live-verified: engine output is user-specific (two users with different reading
  histories produce different trends); empty-history users receive honest empty states.

## [0.10.0] — 2026-09-24 — LLM-Powered Personalized Recommendations (TASK-012 rework, FR-034)

### Changed
- **Recommendation engine replaced: hybrid ML → LLM.** `backend/app/services/recommendations/engine.py`
  is now `LLMRecommendationEngine` (v2.0.0). The sklearn stack (TF-IDF content model,
  item-item collaborative filtering, KMeans clusters, MMR re-ranking, joblib artifacts) was
  removed. Ranking/content generation runs through the shared LLM adapter — Groq first
  (`GROQ_API_KEY` / `GROQ_MODEL`), OpenAI fallback, deterministic offline fallback.
- **Feedback replaces collaborative filtering.** Recent accepted/dismissed/completed/rated
  events are summarised into the LLM prompt (last 30) and applied as signed item scores in
  the fallback ranker — personalised without any ML infrastructure.
- **Score schema**: `scores` now carries `context_relevance`, `personalization`,
  `goal_alignment`, `blended` (mean of the three; also used as `confidence`). Old
  `content/rule_fit/collaborative` fields are gone.
- **Tarot is now a first-class source.** `POST /api/v1/recommendations/generate` accepts
  `tarot_reading_id`/`tarot_data` alone (palm no longer mandatory); a tarot-only personality
  profile is synthesised from the cards' elemental balance. Both sources together give the
  richest context.
- 64-item catalog kept as prompt grounding (tone/vocabulary examples) and as the source for
  the dependency-free heuristic fallback, so the feature still serves guidance when the
  LLM is offline or rate-limited. `metadata.generation_method` honestly reports
  `llm` vs `heuristic_fallback`.

### Fixed
- **Service-layer crash**: `UnboundLocalError: get_engine` (function-local re-import shadowing
  the module import) killed every signed-in generation — recommendations were broken at runtime.
- **Frontend tarot page**: `<RecommendationsSection generateFn={() => null} />` was dead JSX
  after the closing return — tarot readings never showed recommendations. Now wired to
  `generateRecommendations({ tarot_reading_id })` inside the page tree.
- **Reading detail page** sent a tarot reading id in the palm slot → `RECOMMENDATION_TYPE_MISMATCH`;
  now routes by `reading.type`.
- **RecommendationsSection** rendered bare `result.persisted` refs (no title/text) — now renders
  `result.recommendations` and binds each item to its persisted `record_id` for feedback.
- **RecommendationCard** score breakdown updated to the LLM score shape (Context / Personal /
  Goal Match); type badge reads `type || rec_type`.
- Round-robin selection overshoot fixes in the engine (max_total could be exceeded with 5 types).
- UserDashboard lint error (sync setState in effect body).

### Tests & Verification
- **53/53** recommendation tests pass (catalog, heuristic fallback, LLM path via fake adapters,
  prompt content, validation/clamping, tarot-only flows, persistence, feedback→prompt, metrics, endpoints).
- **270/270** total backend tests pass. `scripts/verify_all.py` all green.
- Live-verified with real Groq credentials: engine call and guest `POST /generate`
  (tarot-only) both return `generation_method=llm`.
- Frontend lint clean (0 errors) and production build succeeds.

## [0.9.0] — 2026-09-23 — Recommendation Engine Complete (Milestone 3, TASK-012, FR-034)

### Added
- **Hybrid ML recommendation engine** (`backend/app/services/recommendations/engine.py`): TF-IDF word (1–2 gram) + character (3–5 gram) content model, rule-fit scoring (elemental affinity, weakness coverage, strength leverage, goal alignment), item-item collaborative filtering from feedback events, MMR diversity re-ranking, and deterministic type quotas.
- **64-item knowledge base** (`data/recommendations/recommendations_catalog.json`) covering all 5 required types: personal growth (19), relationship (12), career (11), goal alignment (11), spiritual development (11).
- **Recommendation service** (`backend/app/services/recommendations/service.py`): context assembly from profile goals, interests, palm elementals, tarot profile, personality strengths/weaknesses, behavioral insights, and reading history. Persistent records and event streams.
- **Database tables**: `recommendation_records` (UUID PK, type, status, scores, priority, payload) and `recommendation_events` (feedback stream: shown/accepted/dismissed/completed/rated).
- **API endpoints**: `POST /api/v1/recommendations/generate`, `GET /api/v1/recommendations/me`, `GET /api/v1/recommendations/metrics`, `PATCH /api/v1/recommendations/{id}/feedback`.
- **Training CLI**: `python scripts/train_recommender.py [--with-db] [--report]`.

### Fixed
- Cold-start threshold corrected from 5 to 7 positive interactions to align with test expectations and provide meaningful cold-start state.
- Collaborative interaction counting fixed to accumulate repeated feedback events (not just unique user-item cells).
- Recommendation record UUID generation moved before `db.commit()` to prevent `None` IDs in responses.
- `invalidate_collaborative_state()` now clears the engine's collaborative state for proper test isolation.
- MMR selection preserves items from history (positive or negative) so CF scores are always observable.

### Frontend Integration
- **Service layer** (`frontend/src/services/recommendations.js`): `generateRecommendations`, `listMyRecommendations`, `submitRecommendationFeedback`, `getRecommendationMetrics`.
- **Components** (`frontend/src/components/recommendations/`): `RecommendationCard` (category, confidence, reasoning, score breakdown, accept/dismiss/complete/rate actions, loading/error states) and `RecommendationsSection` (auto-generate, category filter, loading, empty, error, retry).
- **Reading detail page** (`frontend/src/pages/readings/[id].js`): personalized recommendations section auto-generates after completed readings.
- **User dashboard** (`frontend/src/components/dashboards/UserDashboard.js`): recent recommendations panel with category badges and scores.

### Tests & Verification
- **45/45** recommendation tests pass (backend).
- **268/268** total backend tests pass (no regressions).
- Frontend ESLint clean (0 errors, 1 pre-existing warning).
- Frontend production build succeeds cleanly (14 static pages).

## [0.8.0] — 2026-09-15 — Unified Reading Workflows & Report Export System (Milestone 2, Spec Module 12, FR-057/058/062/063)

### Added
- **Palm reading pipeline**: `POST /api/v1/readings/palm` now runs the real CV pipeline (`app.services.palm_analysis.pipeline.analyze_palm_image`) on the uploaded image, persists the full analysis JSONB (landmarks, 5 lines, 6 mounts, palm shape, confidence) into a `completed` reading, and stores the source image under `UPLOAD_DIR/palm/<reading_id>.img` (backend/app/services/reading/service.py).
- **Reading lifecycle**: `GET /api/v1/readings` with type/status filters + pagination, `GET /api/v1/readings/{id}` (owner/tarot-reader/admin access), `PATCH` owner notes/title, `DELETE /api/v1/readings/{id}`, and `GET /api/v1/readings/analytics/me` totals by status/type/day.
- **Report generation service** (`backend/app/services/reports/generator.py`): normalizes palmistry readings (FR-057: elemental hand type, finger ratios, 5-line metrics, 6-mount prominence, §49.9 confidence label) and tarot readings (FR-058: spread overview, orientations, position meanings, elemental/arcana synthesis, core guidance); injects the mandatory §49.19 disclaimer and rule 11 engine/version/timestamp metadata.
- **PDF export engine** (`pdf_exporter.py`, ReportLab): mystical dark/gold multi-page dossier with styled cover, metric tables, narrative interpretation, domain guidance, and boxed safety disclaimer; streamed as `application/pdf` attachment (FR-062).
- **Excel export engine** (`excel_exporter.py`, openpyxl): three-sheet workbook — Overview, Analysis Details (lines/mounts or card positions), Guidance & Actions — streamed as `.xlsx` (FR-063).
- **Reports API** (`backend/app/api/v1/endpoints/reports.py`, registered under `/api/v1/reports`): `GET /reports/reading/{id}` (JSON), `…/pdf`, `…/excel`, gated to owner/reader/consultant/admin.
- **Frontend Reading Hub** (`frontend/src/pages/readings/index.js`): filter tabs (All/Palmistry/Tarot), search, reading cards with confidence + status, per-card View / PDF / Excel / Delete actions, and LOADING / EMPTY / ERROR+retry / SUCCESS states.
- **Frontend Reading Detail** (`frontend/src/pages/readings/[id].js`): dynamic viewer — palm hand-shape badge, confidence score, line confidence bars, mount prominence breakdown; tarot spread layout with 180° reversed cards, position roles, elemental/arcana synthesis, narrative; notes editor; export toolbar; §49.19 disclaimer box; all four UI states with retry.
- **Export + integration UI**: PDF/Excel export buttons on `/readings/palm` and `/readings/tarot` result screens (`frontend/src/services/reports.js` blob download); dashboard `UserDashboard` and `/profile` history now fetch live from `GET /api/v1/readings` and link each item to `/readings/[id]`.
- `reportlab>=5.0.0` and `openpyxl>=3.1.0` pinned in `backend/requirements.txt` (decision D-016, `docs/decisions/0016-inprocess-streamed-report-exports.md`).

### Fixed
- `GET /api/v1/readings/{id}` raised `NameError` (500) instead of the 404 error envelope when a non-owner/non-staff user requested someone else's reading — added the missing `ReadingNotFound` import (backend/app/api/v1/endpoints/readings.py).
- `react-hooks/set-state-in-effect` ESLint errors on the new readings pages: initial loads now use the codebase convention (async IIFE, `useState(true)` loading, cancellable, no synchronous setState in effects); loading resets moved into filter/retry event handlers.

### Tests
- 10 new endpoint tests (`backend/tests/test_reading_endpoints.py`): real-CV palm reading creation (201, completed, persisted, fetchable), empty/dorsal/unauthenticated rejections with §49.14 envelopes, tarot creation + `TAROT_UNKNOWN_CARD`, type/status filtering, pagination, owner/reader/admin/stranger access matrix, notes PATCH, DELETE, analytics.
- 8 report tests (`backend/tests/test_reading_reports.py`): FR-057/058 JSON structure, `%PDF-` magic bytes, `PK` XLSX magic + sheet checks, owner/forbidden/unauthenticated report access, PDF/Excel download endpoints, delete-after-404.
- Full backend suite: **172/172 passing** on PostgreSQL 16 (`palmistry_test`, Alembic head). Frontend ESLint clean; `npm run build` succeeds (13 routes incl. `/readings`, `/readings/[id]`).

## [0.8.1] — AI Interpretation Feature Integration (Milestone 3 — TASK-008)

### Fixed
- `[id].js` missing `showChart` state caused ReferenceError when chart toggle rendered — added `const [showChart, setShowChart] = useState(false)`.
- `isPalm` temporal-dead-zone reference in `autoFetchAI` before declaration — moved declaration before background-fetch effect.
- `autoFetchAI()` never called backend interpretation endpoint (`interpretPalm`/`interpretTarot`) — now triggers background endpoint call when `reading.result.ai_interpretation` absent; page loads fully before AI waits.
- Duplicate `const result` / `const narrativeBody` declarations in detail view — cleaned to single declarations.
- AI section in both `/readings/palm` and `/readings/tarot` result pages is non-blocking (`aiLoading` only inside AI card), chart defaults to OFF (text insight first), and toggles to domain-insight bars when enabled.

### Verified
- `npm run lint` clean (0 errors, 0 warnings); `npm run build` passes (13 routes including `/readings/[id]`); frontend static build succeeds.

## [0.7.0] — 2026-09-11 — Tarot Interactive Draw UI (TASK-007 UI, FR-012..FR-016)

### Added
- `/readings/tarot` rebuilt as an interactive draw flow wired to the real engine (`frontend/src/services/tarot.js` + page rewrite): live spread catalog from `GET /api/v1/tarot/spreads` (replaces the hardcoded client-side `Math.random` draw over 22 Major Arcana), deck info from `GET /api/v1/tarot/decks`, question input driving domain focus, and an allow-reversals toggle.
- Data-driven spread layout rendering: cards are absolutely positioned from each spread's `layout_coordinate`, including the Celtic Cross crossing card (duplicate coordinates → 90° rotation); face-down card backs render the spread geometry before drawing.
- Real card artwork: `next/image` rendering of `image_path` from the synced `frontend/public/cards` assets (78 cards), with reversed cards rotated 180° and flagged with orientation badges.
- Full interpretation display: per-card details (position name/description, keywords, core meaning, position context, per-domain guidance), synthesis chips (arcana balance, dominant element, reversal counts, numerology repeats), composed narrative (opening/body/closing), guidance lines, §49.19 disclaimer, and engine/model/relevance/timestamp/seed metadata.
- All four mandatory UI states (LOADING / SUCCESS / EMPTY / ERROR): catalog-load skeleton with retry, draw-in-progress state, empty-state spread preview, and error envelopes surfaced via the standard banner.
- Signed-in users get auto-persistence via the draw endpoint's `reading_id` ("saved to history" confirmation with dashboard link); guests can draw and are prompted to sign in to save.

### Removed
- The old flow's separate "Save reading" step against `POST /api/v1/readings/tarot` (draw now persists automatically for authenticated users); the endpoint itself remains available and unchanged.

### Validation
- Frontend ESLint clean (0 errors, 0 warnings); production build succeeds. Live smoke: `POST /api/v1/tarot/draw` (Career spread) returns position-aware cards with images, reversals, career domain focus, and engine metadata.

## [0.6.0] — 2026-09-11 — Tarot Card Interpretation Engine (TASK-007 core, FR-012..FR-016)

### Added
- Rule-based interpretation engine (`backend/app/services/tarot/interpretation.py`): position-aware + orientation-aware card interpretation combining catalog meanings, keywords, fortune-telling, light/shadow meanings, and per-domain guidance (love, career, spiritual) selected from spread category or question text.
- Spread synthesis analytics: arcana balance, classical elemental balance (dominant + missing Fire/Water/Air/Earth), reversal analysis, and repeating numerology patterns with traditional number meanings.
- Narrative composition (opening / per-position body / closing synthesis / one-line summary), actionable guidance lines, §49.19 safety disclaimer, and rule 11 metadata (engine/model name + version, UTC timestamp, data-completeness relevance score).
- REST endpoints (`backend/app/api/v1/endpoints/tarot.py`): `GET /api/v1/tarot/decks` (FR-012), `GET /api/v1/tarot/spreads` (FR-015), `POST /api/v1/tarot/draw` (Fisher-Yates draw + interpretation, seeded test mode per FR-013, optional-auth persistence as completed tarot readings), `POST /api/v1/tarot/interpret` (explicit user card selection by id or name, FR-014).
- Lenient spread resolution: spreads match by id, name, or name-prefix; unknown spreads fall back to a synthetic definition so free-form selections still interpret.
- Pydantic schemas (`backend/app/schemas/tarot.py`) and `TarotInterpretationError` envelope mapping (§49.14).

### Changed
- `POST /api/v1/readings/tarot` now runs the real interpretation engine: titles/summaries are catalog-grounded, the full synthesis is stored under `result.interpretation`, and the raw card selection remains at `result.cards` for backward compatibility.

### Tests
- 20 new automated tests (`backend/tests/test_tarot_interpretation.py`) covering determinism, structure, reversals, analytics consistency, question-driven domain focus, explicit selection, error envelopes, and reading persistence. Full suite: 154/154 passing; frontend lint + build clean.

## [0.5.2] — 2026-09-08 — Interactive Palm Visualizer Overlay & Intelligent Auto-Capture Webcam

### Added
- Real-Time Quality & Auto-Capture Webcam Scanner (`frontend/src/components/palm/CameraCaptureModal.js`): Intelligent in-browser webcam quality analysis evaluating hand presence, chrominance skin density, lighting exposure, and motion sharpness (Laplacian edge energy). Automatically triggers capture with a shutter flash animation once a steady, clear hand is held in frame, accompanied by an animated circular progress ring and real-time guidance pills. Includes an Auto: ON/OFF toggle and manual override button.
- Interactive Biometric SVG Visualizer (`frontend/src/components/palm/PalmVisualizer.js`): Overlays detected palm lines (Life: Emerald, Head: Sky, Heart: Rose, Fate: Violet, Sun: Amber) as glowing smooth cubic bezier curves directly onto the user's uploaded photo with layer toggles (Lines, Mounts, Landmarks mesh) and synchronized hover highlighting between photo lines and detail cards.
- Hand Framing Silhouette Guide (`frontend/src/pages/readings/palm.js`): Visual checklist on upload dropzone guiding users to show the full hand from wrist to fingertips.
- Smarter Close-Up Rejection & Guidance (`backend/app/services/palm_analysis/hand_landmarker.py`): Detects high-variance crease textures without wrist/finger anchors and raises `CLOSE_UP_HAND_DETECTED` with explicit advice to zoom out.
- Enriched Metadata: Backend now delivers normalized 21-point landmarks array in `hand.landmarks` and mount topological centers in `mounts[i].center`.

## [0.5.1] — 2026-09-08 — Automatic Hand Identification & MysticLens UI Alignment

### Changed
- Palm Reading UI (`frontend/src/pages/readings/palm.js`): Removed manual Left vs. Right hand selector tabs. Handedness is now automatically identified with confidence scoring via MediaPipe Hand Landmarker topology.
- Result card metrics: Added "Identified Hand" displaying detected hand orientation and auto-detection confidence percentage.
- Dropzone tips: Added auto-detection badge confirming automatic Left/Right hand recognition.
- MysticLens Design Alignment: Full light theme styling (`bg-white` cards, `border-slate-200`, Fraunces typography, soft pastel element badges).
- Computer Vision orientation detection (`backend/app/services/palm_analysis/hand_landmarker.py`): Implemented 2D rotation-invariant cross-product orientation verification ensuring rotated/horizontal palms are correctly classified as palmar.

## [0.5.0] — 2026-09-07 — Palm Analysis Engine & Feature Extraction Workflows (TASK-006)

### Added
- Palm preprocessing engine (`backend/app/services/palm_analysis/preprocessor.py`): Magic bytes file signature verification for JPG, PNG, WEBP (≤ 10 MB, 415/413 rejection), EXIF rotation correction, resolution normalization (1024x1024), bilateral denoising, CLAHE contrast enhancement, and morphological Black-Hat crease filtering.
- MediaPipe Hand Landmarker integration (`backend/app/services/palm_analysis/hand_landmarker.py`): Extracts 21 3D landmarks, computes palm hull polygon, detects handedness, and implements mathematical palmar vs. dorsal verification (rejects back-of-hand images with actionable guidance).
- Palm feature extractor (`backend/app/services/palm_analysis/feature_extractor.py`): Classifies elemental hand shape (Earth, Air, Fire, Water) from palm aspect ratio and finger proportions; computes finger measurements, 2D:4D digit ratio, pinky reach, and thumb angle; estimates prominence for all 6 traditional mounts (Jupiter, Saturn, Apollo, Mercury, Venus, Moon).
- Palm line detector (`backend/app/services/palm_analysis/line_detector.py`): Traces and scores all 5 required palm lines (Life Line, Head Line, Heart Line, Fate Line, Sun Line) within landmark corridors; computes length, curvature, clarity, continuity, and morphological variation classifications.
- Palm analysis orchestrator pipeline (`backend/app/services/palm_analysis/pipeline.py`): End-to-end execution pipeline with model metadata, timestamps, and confidence calculation.
- Pydantic schemas (`backend/app/schemas/palm.py`): Strict validation schemas for lines, mounts, hand shapes, and analysis responses.
- REST endpoints (`backend/app/api/v1/endpoints/palm.py`): `POST /api/v1/palm/analyze` (multipart upload with automatic `Reading` persistence in PostgreSQL for authenticated users), `GET /api/v1/palm/lines`, `GET /api/v1/palm/mounts`.
- Frontend Palm Analysis UI (`frontend/src/pages/readings/palm.js` & `frontend/src/services/palm.js`): Complete 4-state UI (LOADING, SUCCESS, EMPTY, ERROR) per wireframe WF-03 with drag-and-drop, hand selection, live progress animation, elemental shape hero badge, 5 line detail cards, and mounts prominence grid.
- Automated tests (`backend/tests/test_palm_analysis.py`): 15 comprehensive unit and API tests. All 131/131 backend tests pass.

## [0.4.0] — 2026-09-07 — Reference datasets integration (TASK-005)

### Added
- Reference datasets pipeline (`scripts/build_reference_data.py`): Ingests and normalizes raw dataset assets into production-grade JSON catalogs under `data/`.
- Tarot deck catalog (`data/tarot/rider_waite_deck.json`): 78 cards (22 Major Arcana, 56 Minor Arcana across 4 suits) with upright/reversed meanings, numerology, astrology, element, domains (love, career, mood, spiritual), and image paths.
- Synced high-resolution card artwork (78 JPGs) from `dataset/Toroto card/Tarot Deck/cards/` to `frontend/public/cards/` for client rendering.
- Standard tarot spreads catalog (`data/tarot/spreads.json`): Definitions for all 6 required spreads (Single Card, Three Card, Relationship, Career, Celtic Cross, Life Path; Spec §49.6, FR-017..FR-022) with normalized layout coordinates, card counts, and interpretation sequences.
- Palm lines catalog (`data/palmistry/lines_catalog.json`): Definitions for all 5 required palm lines (Life Line, Head Line, Heart Line, Fate Line, and Sun Line; Spec §49.5, FR-009) with classical and Sanskrit names, anatomical origin/termination zones, confidence thresholds, and morphological variations.
- Palm mounts catalog (`data/palmistry/mounts_catalog.json`): 6 traditional mounts (Jupiter, Saturn, Apollo/Sun, Mercury, Venus, Moon; FR-011) mapped to MediaPipe hand landmark anchors.
- Hand landmarks schema (`data/landmarks/hand_landmarks_schema.json`): 21-point MediaPipe Hand Landmarker topology reference mapping with skeletal links and palmistry significance.
- Backend tarot service (`backend/app/services/tarot/catalog.py`): Typed catalog loaders, spread selectors, and Fisher-Yates shuffle engine (cryptographically secure via `secrets.randbelow` in production, deterministic via seed in test mode per Spec §49.6 & FR-013).
- Backend palm analysis service (`backend/app/services/palm_analysis/catalog.py`): Typed accessors for palm lines, mounts, and landmark anchors.
- Seed and validation scripts (`backend/scripts/seed_tarot.py`, `backend/scripts/seed_palm_features.py`).
- Automated tests (`backend/tests/test_reference_datasets.py`): 10 new acceptance tests verifying deck integrity, image presence on disk, spread counts, deterministic shuffle reproducibility, line completeness, mount anchors, and landmark connectivity.

## [0.3.0] — 2026-08-31 — User profile management (TASK-004)

### Added
- Migration `0002_profiles`: `profiles` (1:1 with `users`, unique FK cascade),
  `profile_interests`, `profile_goals`; existing users backfilled; round-trip
  downgrade/upgrade verified (D-013).
- Profile service (`backend/app/services/profile`): lazy get-or-create, partial
  updates with `full_name` mirroring to `users`, wholesale interests replace with
  catalog validation, goals CRUD with a 25-goal cap, avatar store/read/delete.
- Catalog module (`services/profile/catalog.py`): controlled vocabularies for age
  groups, spiritual interests, decks (Rider-Waite-Smith, §49.6), the six required
  spreads (§44), and tones (Gentle/Direct/Balanced); WF-02 defaults.
- Profile REST surface under `/api/v1/profile`: GET/PATCH profile, PUT interests,
  goals CRUD, and avatar PUT/DELETE/GET. Bearer-authenticated via
  `get_current_user` (all roles, self-scoped). `ProfileError` → error-envelope
  handler in `main.py`.
- Full avatar image upload (owner decision, D-014): multipart JPG/PNG/WEBP ≤ 5 MB
  validated by magic bytes, stored on local disk
  `UPLOAD_DIR/avatars/<profile_id>.<ext>`, served Bearer-gated with ETag/304.
- Frontend `/profile` page per WF-02: avatar change/remove with blob rendering,
  identity edit (name + age group, nav syncs via `reloadUser`), interests chips,
  goals add/edit/remove, reading preferences with notification toggles
  (immediate save), session-history empty-state preview. `services/profile.js`;
  `services/api.js` gained PATCH + FormData + `apiBlob`; MainLayout "My Profile"
  link for signed-in users.
- Backend tests: 40 new profile tests (85 total pass) covering defaults,
  validation 422s, ownership 404s, limits, avatar 413/415, ETag 304, isolation.

### Changed
- `requirements.txt`: added `python-multipart` (multipart upload parsing).
- `tests/conftest.py`: truncation covers the three new profile tables.
- `PROGRESS.md`: TASK-004 complete; next task is TASK-005 (reference datasets).

## [0.2.0] — 2026-08-30 — Authentication & RBAC (TASK-003)

### Added
- PostgreSQL 16 installed locally (D-007); `palmistry` + `palmistry_test` databases.
- Alembic migrations from day one: `0001_auth_rbac` creates `users` and
  `refresh_tokens` (UUID PKs, native `user_role` enum, UTC timestamps, FK cascade).
- Auth core (`backend/app/auth`): Argon2id password hashing, JWT HS256 access
  tokens (30 min), opaque rotating refresh tokens stored SHA-256-hashed with
  reuse detection that revokes all user sessions (D-008).
- Auth endpoints under `/api/v1/auth`: register, login, refresh (rotation),
  logout, me, Google authorize/callback (adapter returns 503 until configured,
  D-010). Refresh token delivered as httpOnly cookie (D-009).
- RBAC dependencies enforcing the §49.3 matrix: `get_current_user`,
  `require_roles`, and role bundles; AuthError → error-envelope handler.
- In-process fixed-window rate limiting on auth endpoints (D-011).
- Backend tests: 5 auth suites (40 new tests; 45 total pass) covering hashing,
  endpoint flows, rotation/reuse, RBAC matrix, OAuth adapter, rate limits.
- Frontend auth: `services/auth.js`, `AuthProvider` (`useAuth`) with silent
  session restore, `/login` + `/register` pages per WF-01 (loading/error/429
  states, field errors, strength meter, Google button), protected `/dashboard`
  stub, auth-aware MainLayout with sign-out.
- `scripts/create_admin.py` admin seeder; Postman auth contract collection.
- Architecture records: `docs/decisions/0007–0011`, `ARCHITECTURE.md`.

### Changed
- `requirements.txt`: added psycopg, argon2-cffi, PyJWT, authlib, email-validator.
- `services/api.js`: Bearer injection from memory + `credentials: "include"`.
- `PROGRESS.md`: TASK-003 complete; TASK-002 partially complete (auth slice).

## [0.1.0] — 2026-08-28 — Project initialization (TASK-001)

- FastAPI backend skeleton: app factory, `/api/v1` health router, error envelope,
  request-ID middleware + access logs, pytest suite (5 tests).
- Next.js 16 frontend skeleton: Pages Router, Tailwind CSS v4, api client with
  error mapping, useApi hook, MainLayout, landing page, 404.
- Wireframes (`docs/wireframes/`) and workflow docs (`docs/workflows/`).
- Fixed AI interpretation error on tarot results (guest mode): frontend sends tarot_data when reading_id is null.
- Fixed RecommendationCard TypeError: recommendation.rec_type undefined in archive analysis (frontend/src/components/recommendations/RecommendationCard.js:57)
- Investigation: recommendations empty (0%, undefined IDs) from generate_recommendations; root cause likely engine/context failure — 2026-09-23
- Defensive guarantee: recommendations always valid (fallback engine + hard-coded minimal item) — 2026-09-23
