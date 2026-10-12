# Live Consultation & Booking Module — Implementation Plan

> New, independent module for the Palmistry & Tarot Intelligence Platform.
> Follows existing FastAPI + React/Next.js (Pages Router) + PostgreSQL architecture
> and the existing JWT role-based authentication. No palmistry/tarot code is modified.

## Roles

| Role | Capability |
|---|---|
| `user` (Seeker) | Browse consultant profiles, view available slots, book, cancel, leave feedback |
| `tarot_reader`, `spiritual_consultant` | Full consultant capability (profile, availability, accept/reject, notes) **and** seeker capability |
| `admin` | Can act as consultant (role bundles), plus module visibility |

## Backend

### New files
| File | Purpose |
|---|---|
| `app/models/booking.py` | `ConsultantProfile`, `AvailabilityRule`, `AvailabilitySlot`, `Booking`, `BookingEvent`, `SessionNote`, `SessionFeedback`, `ConsultantCalendarConnection` + enums |
| `app/services/booking/errors.py` | `BookingError` family (class-attribute style, registered in `DOMAIN_ERRORS`) |
| `app/services/booking/availability.py` | Rule → slot materialisation, overlap/conflict resolution |
| `app/services/booking/google_calendar.py` | Dependency-free Google Calendar REST client (httpx + PyJWT): service-account & refresh-token auth, event create/patch/delete with `conferenceData` → Google Meet |
| `app/services/booking/notifications.py` | Booking-aware in-app notifications via existing `Notification` model |
| `app/services/booking/scheduler.py` | APScheduler: reminder dispatch, slot rollout, auto-complete |
| `app/services/booking/service.py` | Consultant profile CRUD, availability management, booking lifecycle, notes, feedback |
| `app/schemas/booking.py` | Pydantic v2 `*Out` / `*Create` / `*Update` |
| `app/api/v1/endpoints/booking.py` | `consultants.router` (`/consultants`), `consultants.router` consultant self-service (`/consultants/me/...`), `bookings.router` (`/bookings`) |
| `alembic/versions/0007_booking.py` | Hand-written migration (autogenerate is unusable — `env.py` imports a subset) |
| `tests/test_booking.py` | End-to-end API tests |

### Touched (additive only)
| File | Change |
|---|---|
| `app/config.py` | booking window/lead-time/horizon + Google Calendar settings |
| `app/models/notification.py` | 6 new `NotificationType` values (reuses existing bell/Notification Center) |
| `app/models/user.py` | `consultant_profile`, `consultant_bookings`, `client_bookings` relationships |
| `app/models/__init__.py` | re-export booking models |
| `app/api/v1/router.py` | register `booking` routers |
| `app/main.py` | add `BookingError` to `DOMAIN_ERRORS`; start booking scheduler |
| `tests/conftest.py` | add new tables to `TRUNCATE` list |
| `.env.example` / `.env` | document new settings |

## Booking status flow

```
                  ┌────────────► rejected ────┐
pending ── accept ─┤                          ├─► (terminal)
       └─ reject ─┘                          │
       └─ cancel ─► cancelled ◄──────────────┘
                  accepted ─ complete ► completed
                  accepted ─ cancel    ► cancelled
```
Enforced transitions live in `app/services/booking/service.py`; every transition writes a
`BookingEvent` audit row and fires a notification.

## Google Calendar / Meet

* Trigger: booking `pending → accepted` (i.e. "confirmed").
* Event created on the **consultant's connected Google Calendar** (per-consultant OAuth2 refresh
  token, scope `calendar.events`) with `conferenceData.createRequest` → Google returns the
  `hangoutLink`, which is persisted as `bookings.meet_link`.
* Fallback: platform **service account** calendar (`GOOGLE_SERVICE_ACCOUNT_FILE`).
* Failure is non-fatal: `calendar_sync_status` records `failed` + error; the booking still
  succeeds. Retry endpoint provided.
* Cancel/complete delete/patch the remote event; `meet_link` stays on the row for history.

## Frontend (Pages Router, Tailwind v4, no new deps)

| File | Purpose |
|---|---|
| `src/services/booking.js` | API client for `/consultants` + `/bookings` |
| `src/lib/datetime.js` | Native-`Intl` date helpers (no date library installed) |
| `src/components/booking/shared.js` | Status labels/tones, `ConsultantCard`, `SessionCard`, `SlotPicker`, `RatingStars` |
| `src/components/booking/SeekerSessionsPanel.js` | Upcoming/past sessions + Join Google Meet |
| `src/components/booking/ConsultantSessionsPanel.js` | Consultant requests/sessions/notes |
| `src/pages/consultants/index.js` | Browse + filter consultants |
| `src/pages/consultants/[consultantId].js` | Profile, day/slot picker, booking form |
| `src/pages/sessions.js` | Seeker session hub (history, cancel, feedback) |
| `src/pages/consultant-studio.js` | Consultant console (profile, availability, requests, notes) |
| `src/lib/roles.js` | nav entries `consultants` / `sessions` / `consultant_studio` |
| `UserDashboard`, `ReaderDashboard`, `ConsultantDashboard` | mount the new session panels |

## Phases

1. Consultant profiles + availability
2. Booking system + database
3. Google Calendar/Meet integration
4. User & consultant dashboards
5. Notifications + reminders + cancellation
6. Session history, notes and feedback

## Verification

* `.\.venv\Scripts\pytest backend/tests` (existing 106 + new booking tests)
* `cd frontend; npm run lint; npm run build`
* `alembic upgrade head` on `palmistry` and `palmistry_test`
* Update `AGENT_PROGRESS.md` + `CHANGELOG.md`
