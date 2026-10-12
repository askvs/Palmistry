# UI Wireframes — Palmistry & Tarot Intelligence Platform

Low-fidelity wireframes for every required user-facing area (spec §13.2, §13.3).
Format: ASCII wireframes + interaction notes + required UI states.

## Label rule

Every screen **must** implement the four canonical states (spec rule 0.1 #10):

| State | Convention in wireframes |
|---|---|
| `LOADING` | Skeleton shimmer / spinner region |
| `SUCCESS` | Populated content |
| `EMPTY` | Friendly empty-state with primary CTA |
| `ERROR` | Error banner with retry action |

## Screen index

| # | File | Route (planned) | Roles |
|---|---|---|---|
| 01 | `01-authentication.md` | `/register`, `/login` | Guest |
| 02 | `02-user-profile.md` | `/profile` | User |
| 03 | `03-palm-upload.md` | `/readings/palm` | User |
| 04 | `04-tarot-spread-and-card-draw.md` | `/readings/tarot` | User |
| 05 | `05-reading-display.md` | `/readings/[id]` | User, Tarot Reader |
| 06 | `06-history-and-recommendations.md` | `/history`, `/recommendations` | User |
| 07 | `07-user-dashboard.md` | `/dashboard` | User |
| 08 | `08-role-dashboards.md` | `/reader`, `/consultant`, `/admin` | Reader, Consultant, Admin |
| 09 | `09-reports-export.md` | `/reports` | All authenticated |

## Design tokens (Tailwind CSS baseline)

- **Mobile-first responsive** (§13.5): breakpoints `sm 640 / md 768 / lg 1024 / xl 1280`.
- **Typography:** Inter or system stack; scale `text-sm → text-5xl`; headings semibold.
- **Spacing:** 4px base grid (`p-2..p-8`); cards `rounded-2xl`; soft shadows.
- **Palette (mystical, calm):**
  - Background: deep indigo `#0F172A` (dark) / off-white `#F8FAFC` (light)
  - Surface: `#1E293B` / white
  - Primary accent: violet `#8B5CF6`
  - Secondary accent: gold `#F59E0B`
  - Success `#10B981`, Warning `#F59E0B`, Error `#EF4444`
- **Component tokens:** buttons (`primary/secondary/ghost/danger`), inputs, cards,
  badges for score labels (Low/Moderate/High/Very High per §49.9), skeleton loaders.
- **Accessibility:** WCAG AA contrast, focus rings, alt text on card/palm imagery,
  reduced-motion support for shuffle/draw animations.

## Global layout

```
┌────────────────────────────────────────────────────────────┐
│ ☰  ✦ MysticLens (logo)      Explore  History  Reports  🔔  ◉ │  ← top nav
├────────────────────────────────────────────────────────────┤
│                                                            │
│                     <page content>                         │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ footer: disclaimer · privacy · terms · contact             │
│ "Interpretive guidance for self-reflection — not advice."  │  ← §49.19
└────────────────────────────────────────────────────────────┘
```

Mobile: nav collapses to bottom tab bar (Home · Readings · History · Profile).
