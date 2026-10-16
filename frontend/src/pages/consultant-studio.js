// Consultant Studio: operator console for profile, availability, requests, sessions, calendar.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  PageHeader,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { Segmented, StatCard } from "@/components/dashboards/shared";
import {
  CalendarIcon,
  ChatIcon,
  CheckCircleIcon,
  ClockIcon,
  CompassIcon,
  PencilIcon,
  PlusIcon,
  SettingsIcon,
  StarIcon,
  TrashIcon,
  VideoIcon,
} from "@/components/icons";
import {
  BookingStatusBadge,
  CalendarSyncBadge,
  EmptyRow,
  SessionCard,
} from "@/components/booking/shared";
import BookingChat from "@/components/booking/BookingChat";
import TimeProposalForm from "@/components/booking/TimeProposalForm";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import {
  acceptBooking,
  addSessionNote,
  blockSlot,
  completeBooking,
  connectCalendar,
  counterBookingAsConsultant,
  createAvailabilityRule,
  deleteAvailabilityRule,
  deleteSlot,
  deleteSessionNote,
  disconnectCalendar,
  fetchAvailabilityRules,
  fetchBookingNotes,
  fetchConsultantStudioOverview,
  fetchConsultantSessions,
  fetchMySlots,
  generateSlots,
  rejectBooking,
  requestCalendarAuthorization,
  toggleAcceptingBookings,
  unblockSlot,
  updateAvailabilityRule,
  updateSessionNote,
  upsertMyConsultantProfile,
} from "@/services/booking";
import {
  addDays,
  formatDateTime,
  formatDuration,
  formatRange,
  formatTime,
  todayKey,
} from "@/lib/datetime";

const TABS = [
  { value: "overview", label: "Overview" },
  { value: "availability", label: "Availability" },
  { value: "requests", label: "Requests" },
  { value: "sessions", label: "Sessions" },
  { value: "calendar", label: "Calendar" },
];

const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function ConsultantStudioPage() {
  const router = useRouter();
  const toast = useToast();
  const { user, loading: authLoading } = useAuth();
  // Seekers (role "user") are redirected to their dashboard; the studio is for
  // tarot readers, spiritual consultants and admins only.
  const blocked = useRoleGuard();

  const [tab, setTab] = useState("overview");
  // Bumped whenever the top requests panel resolves a booking, so the full
  // Requests tab below remounts with fresh data when it is opened.
  const [requestsTick, setRequestsTick] = useState(0);
  const googleCalendarState = Array.isArray(router.query.google_calendar)
    ? router.query.google_calendar[0]
    : router.query.google_calendar;

  if (blocked) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">
        Redirecting…
      </div>
    );
  }

  if (!authLoading && !user) {
    return (
      <div className="animate-fade-in space-y-8">
        <PageHeader
          icon={CompassIcon}
          eyebrow="Consultant studio"
          title="Sign in required"
          description="Sign in with a consultant account to manage your availability and sessions."
          actions={
            <Button href="/login?redirect=/consultant-studio">Sign in</Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-8">
      <PageHeader
        icon={CompassIcon}
        tileTone="emerald"
        eyebrow="Consultant studio"
        title="Your consultation workspace"
        description="Publish availability, accept booking requests, run live Google Meet
          sessions, and keep private notes on every conversation."
        gradient="gold"
        actions={
          <Button href="/sessions" variant="secondary" icon={CalendarIcon}>
            My sessions
          </Button>
        }
      />

      <Segmented
        label="Consultant studio section"
        value={tab}
        onChange={setTab}
        options={TABS}
      />

      {/* Live requests pinned on top for one-click accept/decline. */}
      {user && (
        <RequestsTopPanel
          onOpenRequests={() => setTab("requests")}
          onChanged={() => setRequestsTick((tick) => tick + 1)}
        />
      )}

      {googleCalendarState && (
        <div className="flex items-start gap-3 rounded-2xl border border-primary-100 bg-primary-50/70 p-4 text-sm text-primary-900">
          <SettingsIcon className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
          <p>
            {googleCalendarState === "connected"
              ? "Google Calendar connected. Future bookings will create calendar events with Meet links."
              : `Google Calendar connection status: ${googleCalendarState}.`}
          </p>
        </div>
      )}

      {tab === "overview" && <OverviewTab onNavigate={setTab} />}
      {tab === "availability" && <AvailabilityTab />}
      {tab === "requests" && <RequestsTab key={requestsTick} />}
      {tab === "sessions" && <SessionsTab />}
      {tab === "calendar" && <CalendarTab onDone={() => setTab("calendar")} />}
    </div>
  );
}

// Overview + profile editor.
function OverviewTab({ onNavigate }) {
  const { data, error, loading, refresh } = useAsyncData(fetchConsultantStudioOverview);
  const [editing, setEditing] = useState(false);

  if (loading) return <SkeletonRow lines={6} />;
  if (error) {
    if (error.code === "CONSULTANT_PROFILE_NOT_FOUND") {
      return <ProfileEditor onSaved={refresh} />;
    }
    if (error.status === 403) {
      return (
        <Panel>
          <EmptyState
            icon={CompassIcon}
            title="Consultant access only"
            description="This workspace is for tarot readers, spiritual consultants, and admins."
            action={
              <Button href="/dashboard" size="sm" variant="secondary">
                Back to dashboard
              </Button>
            }
          />
        </Panel>
      );
    }
    return <ErrorState message={error.message} onRetry={refresh} />;
  }

  const { profile, stats } = data;

  return (
    <div className="space-y-6">
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Pending requests"
          value={stats?.pending_requests ?? 0}
          tone="accent"
          icon={ClockIcon}
          hint="Waiting on you"
        />
        <StatCard
          label="Upcoming"
          value={stats?.upcoming_sessions ?? 0}
          tone="primary"
          icon={CalendarIcon}
          hint="Confirmed sessions"
        />
        <StatCard
          label="Completed"
          value={stats?.completed_sessions ?? 0}
          tone="emerald"
          icon={CheckCircleIcon}
          hint="All time"
        />
        <StatCard
          label="Open slots"
          value={stats?.open_slots ?? 0}
          tone="blue"
          icon={CalendarIcon}
          hint="Published ahead"
        />
      </div>

      {editing ? (
        <ProfileEditor profile={profile} onSaved={refresh} onCancel={() => setEditing(false)} />
      ) : (
        <Panel
          title="Public profile"
          subtitle="What seekers see in the consultant directory"
          action={
            <div className="flex items-center gap-2">
              <Badge tone={profile.is_accepting_bookings ? "emerald" : "slate"}>
                {profile.is_accepting_bookings ? "Accepting bookings" : "Paused"}
              </Badge>
              <Button variant="ghost" size="sm" icon={PencilIcon} onClick={() => setEditing(true)}>
                Edit
              </Button>
            </div>
          }
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Headline</p>
              <p className="mt-1 text-sm text-slate-800">{profile.headline}</p>
              {profile.bio && (
                <>
                  <p className="mt-4 text-xs font-bold uppercase tracking-wide text-slate-500">
                    Bio
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">{profile.bio}</p>
                </>
              )}
              <div className="mt-4 flex flex-wrap gap-1.5">
                {(profile.specializations || []).map((tag) => (
                  <Badge key={tag} tone="primary">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
            <dl className="space-y-2.5 text-sm">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Rate</dt>
                <dd className="font-bold text-slate-900">
                  {profile.currency} {profile.session_rate}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Duration</dt>
                <dd className="font-semibold text-slate-800">
                  {formatDuration(profile.session_duration_minutes)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Buffer</dt>
                <dd className="font-semibold text-slate-800">
                  {formatDuration(profile.buffer_minutes)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Timezone</dt>
                <dd className="font-semibold text-slate-800">{profile.timezone}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Experience</dt>
                <dd className="font-semibold text-slate-800">
                  {profile.years_experience} years
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Rating</dt>
                <dd className="flex items-center gap-1.5 font-semibold text-slate-800">
                  {profile.avg_rating != null ? (
                    <>
                      <StarIcon className="h-4 w-4 text-accent-500" />
                      {Number(profile.avg_rating).toFixed(1)}
                      <span className="text-xs text-slate-400">({profile.review_count})</span>
                    </>
                  ) : (
                    <span className="text-xs text-slate-400">No reviews yet</span>
                  )}
                </dd>
              </div>
            </dl>
          </div>

          <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
            <Button
              variant={profile.is_accepting_bookings ? "dangerGhost" : "primary"}
              size="sm"
              onClick={async () => {
                await toggleAcceptingBookings(!profile.is_accepting_bookings);
                toast.success(
                  profile.is_accepting_bookings ? "Bookings paused" : "Bookings reopened",
                );
                refresh();
              }}
            >
              {profile.is_accepting_bookings ? "Pause new bookings" : "Resume new bookings"}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onNavigate("availability")}>
              Manage availability
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onNavigate("calendar")}>
              Google Calendar
            </Button>
          </div>
        </Panel>
      )}
    </div>
  );
}

function ProfileEditor({ profile, onSaved, onCancel }) {
  const toast = useToast();
  const [form, setForm] = useState({
    headline: profile?.headline ?? "",
    bio: profile?.bio ?? "",
    specializations: (profile?.specializations || []).join(", "),
    modalities: (profile?.modalities || []).join(", "),
    languages: (profile?.languages || []).join(", "),
    years_experience: profile?.years_experience ?? 0,
    session_rate: profile?.session_rate ?? "0.00",
    currency: profile?.currency ?? "USD",
    session_duration_minutes: profile?.session_duration_minutes ?? 60,
    buffer_minutes: profile?.buffer_minutes ?? 15,
    timezone: profile?.timezone ?? "UTC",
    is_accepting_bookings: profile?.is_accepting_bookings ?? true,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  const tokens = (value) =>
    value
      .split(",")
      .map((token) => token.trim())
      .filter(Boolean);

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    if (form.headline.trim().length < 3) {
      setError("A headline of at least 3 characters is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await upsertMyConsultantProfile({
        headline: form.headline.trim(),
        bio: form.bio.trim() || null,
        specializations: tokens(form.specializations),
        modalities: tokens(form.modalities),
        languages: tokens(form.languages),
        years_experience: Number(form.years_experience) || 0,
        session_rate: form.session_rate,
        currency: form.currency,
        session_duration_minutes: Number(form.session_duration_minutes) || 60,
        buffer_minutes: Number(form.buffer_minutes) || 0,
        timezone: form.timezone,
        is_accepting_bookings: form.is_accepting_bookings,
      });
      toast.success("Profile saved", "Seekers can now find you in the consultant directory.");
      onSaved?.();
    } catch (err) {
      setError(err?.message || "Could not save your profile");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel
      title={profile ? "Edit profile" : "Open your consultant profile"}
      subtitle="This is what seekers see before they book"
    >
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label htmlFor="p-headline" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Headline
          </label>
          <input
            id="p-headline"
            value={form.headline}
            onChange={(event) => set("headline", event.target.value)}
            maxLength={160}
            required
            className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="p-bio" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Bio
          </label>
          <textarea
            id="p-bio"
            value={form.bio}
            onChange={(event) => set("bio", event.target.value)}
            rows={4}
            maxLength={4000}
            className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="p-spec" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Specialisations (comma separated)
            </label>
            <input
              id="p-spec"
              value={form.specializations}
              onChange={(event) => set("specializations", event.target.value)}
              placeholder="tarot, love, career"
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="p-mod" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Modalities
            </label>
            <input
              id="p-mod"
              value={form.modalities}
              onChange={(event) => set("modalities", event.target.value)}
              placeholder="tarot, palmistry"
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="p-lang" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Languages
            </label>
            <input
              id="p-lang"
              value={form.languages}
              onChange={(event) => set("languages", event.target.value)}
              placeholder="English, Hindi"
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-4">
          <div>
            <label htmlFor="p-rate" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Rate
            </label>
            <input
              id="p-rate"
              type="number"
              min="0"
              step="0.01"
              value={form.session_rate}
              onChange={(event) => set("session_rate", event.target.value)}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="p-currency" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Currency
            </label>
            <select
              id="p-currency"
              value={form.currency}
              onChange={(event) => set("currency", event.target.value)}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            >
              {["USD", "EUR", "GBP", "INR", "AUD", "CAD"].map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="p-duration" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Session (min)
            </label>
            <input
              id="p-duration"
              type="number"
              min="15"
              max="480"
              step="15"
              value={form.session_duration_minutes}
              onChange={(event) => set("session_duration_minutes", event.target.value)}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="p-buffer" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Buffer (min)
            </label>
            <input
              id="p-buffer"
              type="number"
              min="0"
              max="240"
              step="5"
              value={form.buffer_minutes}
              onChange={(event) => set("buffer_minutes", event.target.value)}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="p-years" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Years of practice
            </label>
            <input
              id="p-years"
              type="number"
              min="0"
              max="80"
              value={form.years_experience}
              onChange={(event) => set("years_experience", event.target.value)}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="p-tz" className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Timezone
            </label>
            <input
              id="p-tz"
              value={form.timezone}
              onChange={(event) => set("timezone", event.target.value)}
              maxLength={64}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.is_accepting_bookings}
                onChange={(event) => set("is_accepting_bookings", event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              Accept new bookings
            </label>
          </div>
        </div>

        {error && <InlineError message={error} />}

        <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
          {onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit" size="sm" loading={busy} disabled={busy}>
            Save profile
          </Button>
        </div>
      </form>
    </Panel>
  );
}

// Availability: weekly rules and materialised slots.
function AvailabilityTab() {
  const toast = useToast();
  const { data, error, loading, refresh } = useAsyncData(fetchAvailabilityRules);
  const [showForm, setShowForm] = useState(false);
  const [busyRuleId, setBusyRuleId] = useState(null);
  const [generating, setGenerating] = useState(false);

  const rules = data || [];

  async function remove(rule) {
    setBusyRuleId(rule.id);
    try {
      await deleteAvailabilityRule(rule.id);
      toast.success("Rule removed", "Its open slots were released.");
      refresh();
    } catch (err) {
      toast.error("Could not remove the rule", err?.message);
    } finally {
      setBusyRuleId(null);
    }
  }

  async function toggle(rule) {
    setBusyRuleId(rule.id);
    try {
      await updateAvailabilityRule(rule.id, { is_active: !rule.is_active });
      refresh();
    } catch (err) {
      toast.error("Could not update the rule", err?.message);
    } finally {
      setBusyRuleId(null);
    }
  }

  async function regenerate() {
    setGenerating(true);
    try {
      const result = await generateSlots({
        fromDate: todayKey(),
        toDate: addDays(todayKey(), 20),
      });
      toast.success(
        "Slots generated",
        `${result.slots_created} open slot${result.slots_created === 1 ? "" : "s"} published.`,
      );
      refresh();
    } catch (err) {
      toast.error("Could not generate slots", err?.message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <Panel
        title="Weekly availability"
        subtitle="Rules are expanded into concrete open slots automatically"
        action={
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" icon={CalendarIcon} loading={generating} onClick={regenerate}>
              Generate slots
            </Button>
            <Button variant="secondary" size="sm" icon={PlusIcon} onClick={() => setShowForm((v) => !v)}>
              {showForm ? "Close" : "Add window"}
            </Button>
          </div>
        }
      >
        {showForm && <RuleForm onCreated={() => { setShowForm(false); refresh(); }} />}

        {loading ? (
          <SkeletonRow lines={4} />
        ) : error ? (
          <ErrorState message={error.message} onRetry={refresh} />
        ) : rules.length === 0 ? (
          <EmptyRow>No availability rules yet — add a window to start being bookable.</EmptyRow>
        ) : (
          <ul className="divide-y divide-slate-100">
            {rules.map((rule) => (
              <li key={rule.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-900">
                    {rule.weekday_name} · {String(rule.start_time).slice(0, 5)}–
                    {String(rule.end_time).slice(0, 5)}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {rule.slot_duration_minutes} min slots · {rule.buffer_minutes} min buffer ·{" "}
                    {rule.timezone}
                    {rule.effective_until ? ` · until ${rule.effective_until}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={rule.is_active ? "emerald" : "slate"}>
                    {rule.is_active ? "Active" : "Paused"}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    loading={busyRuleId === rule.id}
                    disabled={busyRuleId !== null}
                    onClick={() => toggle(rule)}
                  >
                    {rule.is_active ? "Pause" : "Resume"}
                  </Button>
                  <Button
                    variant="dangerGhost"
                    size="sm"
                    icon={TrashIcon}
                    loading={busyRuleId === rule.id}
                    disabled={busyRuleId !== null}
                    onClick={() => remove(rule)}
                  >
                    Remove
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <SlotsPanel />
    </div>
  );
}

function RuleForm({ onCreated }) {
  const toast = useToast();
  const [form, setForm] = useState({
    weekday: (new Date().getDay() + 6) % 7,
    start_time: "10:00",
    end_time: "16:00",
    slot_duration_minutes: 60,
    buffer_minutes: 15,
    timezone: "UTC",
    effective_from: todayKey(),
    effective_until: "",
    is_active: true,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const payload = { ...form };
      if (!payload.effective_until) delete payload.effective_until;
      const result = await createAvailabilityRule(payload);
      toast.success(
        "Window added",
        `${result.slots_created} open slot${result.slots_created === 1 ? "" : "s"} published.`,
      );
      onCreated?.(result);
    } catch (err) {
      setError(err?.message || "Could not add this availability window");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="mb-6 rounded-2xl border border-slate-200 bg-slate-50/60 p-4"
    >
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <div>
          <label htmlFor="r-day" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Weekday
          </label>
          <select
            id="r-day"
            value={form.weekday}
            onChange={(event) => set("weekday", Number(event.target.value))}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          >
            {WEEKDAYS.map((name, index) => (
              <option key={name} value={index}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="r-start" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            From
          </label>
          <input
            id="r-start"
            type="time"
            value={form.start_time}
            onChange={(event) => set("start_time", event.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="r-end" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            To
          </label>
          <input
            id="r-end"
            type="time"
            value={form.end_time}
            onChange={(event) => set("end_time", event.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="r-duration" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Slot length (min)
          </label>
          <input
            id="r-duration"
            type="number"
            min="15"
            max="480"
            step="15"
            value={form.slot_duration_minutes}
            onChange={(event) => set("slot_duration_minutes", Number(event.target.value))}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="r-buffer" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Buffer (min)
          </label>
          <input
            id="r-buffer"
            type="number"
            min="0"
            max="240"
            step="5"
            value={form.buffer_minutes}
            onChange={(event) => set("buffer_minutes", Number(event.target.value))}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="r-tz" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Timezone
          </label>
          <input
            id="r-tz"
            value={form.timezone}
            onChange={(event) => set("timezone", event.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="r-from" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Starts
          </label>
          <input
            id="r-from"
            type="date"
            value={form.effective_from}
            onChange={(event) => set("effective_from", event.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="r-until" className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Ends (optional)
          </label>
          <input
            id="r-until"
            type="date"
            value={form.effective_until}
            onChange={(event) => set("effective_until", event.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
      </div>

      {error && (
        <div className="mt-3">
          <InlineError message={error} />
        </div>
      )}

      <div className="mt-3 flex justify-end">
        <Button type="submit" size="sm" loading={busy} disabled={busy}>
          Publish window
        </Button>
      </div>
    </form>
  );
}

// Slots grouped by day with block/unblock/delete.
function SlotsPanel() {
  const toast = useToast();
  const [statusFilter, setStatusFilter] = useState("available");
  const [busyId, setBusyId] = useState(null);

  const loader = useCallback(
    () =>
      fetchMySlots({
        status: statusFilter === "all" ? undefined : statusFilter,
        from_time: new Date().toISOString(),
        limit: 200,
      }),
    [statusFilter],
  );
  const { data, error, loading, refresh } = useAsyncData(loader);
  const slots = useMemo(() => data?.items || [], [data]);

  const grouped = useMemo(() => {
    const map = new Map();
    for (const slot of slots) {
      const key = slot.start_time.slice(0, 10);
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(slot);
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [slots]);

  async function act(slot, action) {
    setBusyId(slot.id);
    try {
      if (action === "block") await blockSlot(slot.id);
      if (action === "unblock") await unblockSlot(slot.id);
      if (action === "delete") await deleteSlot(slot.id);
      toast.success(
        action === "block" ? "Slot blocked" : action === "unblock" ? "Slot reopened" : "Slot removed",
      );
      refresh();
    } catch (err) {
      toast.error("Could not update the slot", err?.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Panel
      title="Open slots"
      subtitle="Block a slot to take it off the market; removing a booked slot is not allowed"
      action={
        <Segmented
          label="Slot status"
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { value: "available", label: "Open" },
            { value: "booked", label: "Booked" },
            { value: "blocked", label: "Blocked" },
            { value: "all", label: "All" },
          ]}
        />
      }
    >
      {loading ? (
        <SkeletonRow lines={5} />
      ) : error ? (
        <ErrorState message={error.message} onRetry={refresh} />
      ) : grouped.length === 0 ? (
        <EmptyRow>No slots to show for this filter.</EmptyRow>
      ) : (
        <div className="space-y-5">
          {grouped.map(([day, daySlots]) => (
            <div key={day}>
              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                {new Date(`${day}T00:00:00`).toLocaleDateString(undefined, {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                })}
              </p>
              <div className="flex flex-wrap gap-2">
                {daySlots.map((slot) => (
                  <div
                    key={slot.id}
                    className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2"
                  >
                    <span className="text-sm font-semibold text-slate-800">
                      {formatTime(slot.start_time)}
                    </span>
                    <Badge
                      tone={
                        slot.status === "available"
                          ? "emerald"
                          : slot.status === "booked"
                            ? "primary"
                            : "slate"
                      }
                    >
                      {slot.status}
                    </Badge>
                    {slot.status === "available" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        loading={busyId === slot.id}
                        disabled={busyId !== null}
                        onClick={() => act(slot, "block")}
                      >
                        Block
                      </Button>
                    )}
                    {slot.status === "blocked" && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          loading={busyId === slot.id}
                          disabled={busyId !== null}
                          onClick={() => act(slot, "unblock")}
                        >
                          Reopen
                        </Button>
                        <Button
                          variant="dangerGhost"
                          size="sm"
                          icon={TrashIcon}
                          loading={busyId === slot.id}
                          disabled={busyId !== null}
                          onClick={() => act(slot, "delete")}
                        >
                          Delete
                        </Button>
                      </>
                    )}
                    {slot.status === "booked" && (
                      <span className="text-[11px] text-slate-400">booked</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}

// Live requests banner pinned above the tabs.
// Live requests with one-click accept/decline; negotiation lives in the Requests tab.
function RequestsTopPanel({ onOpenRequests, onChanged }) {
  const toast = useToast();
  // Stable loader: useAsyncData re-runs whenever the loader identity changes,
  // so an inline arrow here would refetch on every render (infinite loop).
  const loader = useCallback(() => fetchConsultantSessions({ limit: 20 }), []);
  const { data, error, loading, refresh } = useAsyncData(loader);
  const [busyId, setBusyId] = useState(null);
  const [rowError, setRowError] = useState(null);
  const requests = useMemo(() => (data?.requests?.items || []).slice(0, 5), [data]);
  const total = data?.requests?.total ?? requests.length;

  async function act(booking, action) {
    setBusyId(booking.id);
    setRowError(null);
    try {
      if (action === "accept") {
        await acceptBooking(booking.id);
        toast.success("Session confirmed", "A Google Calendar event and Meet link were created.");
      } else {
        await rejectBooking(booking.id);
        toast.success("Request declined", "The seeker has been notified.");
      }
      refresh();
      onChanged?.();
    } catch (err) {
      setRowError(err?.message || "Could not update this request");
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <SkeletonRow lines={2} />;
  // Never block the studio on this surface — the Requests tab owns the full
  // error view with retry.
  if (error) return null;

  if (requests.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-2xl border border-emerald-200/70 bg-emerald-50/60 px-4 py-3 text-sm text-emerald-900">
        <CheckCircleIcon className="h-4 w-4 shrink-0 text-emerald-600" />
        <p>No pending consultation requests — you&apos;re all caught up.</p>
      </div>
    );
  }

  return (
    <Panel
      title={`Live Consultation Requests (${total})`}
      subtitle="Seekers are waiting — accept or decline in one click"
      action={
        <Button variant="ghost" size="sm" onClick={onOpenRequests}>
          Full requests
        </Button>
      }
    >
      <ul className="space-y-3">
        {requests.map((booking) => {
          const awaitingSeeker = booking.status === "countered";
          return (
            <li
              key={booking.id}
              className="rounded-2xl border border-accent-200/70 bg-accent-50/50 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
                    <BookingStatusBadge status={booking.status} />
                  </div>
                  <p className="mt-1 text-xs text-slate-600">
                    {booking.seeker_name}
                    {booking.seeker_email ? ` · ${booking.seeker_email}` : ""}
                  </p>
                  <p className="mt-1.5 text-xs text-slate-500">
                    {formatRange(booking.start_time, booking.end_time)} ·{" "}
                    {formatDuration(booking.duration_minutes)}
                  </p>
                  {awaitingSeeker && (
                    <p className="mt-1.5 text-xs font-medium text-amber-800">
                      You proposed this time — waiting for {booking.seeker_name} to confirm.
                    </p>
                  )}
                  {booking.meet_link && (
                    <p className="mt-1.5 text-xs text-slate-600">
                      <span className="font-bold text-slate-500">Seeker&apos;s link: </span>
                      <a
                        href={booking.meet_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:underline"
                      >
                        {booking.meet_link}
                      </a>
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {!awaitingSeeker && (
                    <Button
                      size="sm"
                      icon={CheckCircleIcon}
                      loading={busyId === booking.id}
                      disabled={busyId !== null}
                      onClick={() => act(booking, "accept")}
                    >
                      Accept
                    </Button>
                  )}
                  <Button
                    variant="dangerGhost"
                    size="sm"
                    icon={TrashIcon}
                    loading={busyId === booking.id}
                    disabled={busyId !== null}
                    onClick={() => act(booking, "reject")}
                  >
                    Decline
                  </Button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
      {rowError && (
        <div className="mt-3">
          <InlineError message={rowError} />
        </div>
      )}
      {total > requests.length && (
        <Button variant="ghost" size="sm" className="mt-3" onClick={onOpenRequests}>
          View all {total} requests
        </Button>
      )}
    </Panel>
  );
}

function RequestCard({ booking, busyId, onAct, onCounter, refresh }) {
  const [showChat, setShowChat] = useState(false);
  const [showCounter, setShowCounter] = useState(false);
  const awaitingSeeker = booking.status === "countered";

  async function counter({ startTime, durationMinutes, message }) {
    await onCounter(booking, { startTime, durationMinutes, message });
    setShowCounter(false);
  }

  return (
    <li
      className={`rounded-2xl border p-4 ${
        awaitingSeeker
          ? "border-amber-200/80 bg-amber-50/40"
          : "border-accent-200/70 bg-accent-50/50"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-xs text-slate-600">
            {booking.seeker_name}
            {booking.seeker_email ? ` · ${booking.seeker_email}` : ""}
          </p>
          <p className="mt-1.5 text-xs text-slate-500">
            {formatRange(booking.start_time, booking.end_time)} ·{" "}
            {formatDuration(booking.duration_minutes)}
          </p>
          {awaitingSeeker && (
            <p className="mt-1.5 text-xs font-medium text-amber-800">
              You proposed this time — waiting for {booking.seeker_name} to confirm.
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {!awaitingSeeker && (
            <Button
              size="sm"
              icon={CheckCircleIcon}
              loading={busyId === booking.id}
              disabled={busyId !== null}
              onClick={() => onAct(booking, "accept")}
            >
              Accept
            </Button>
          )}
          <Button
            variant="secondary"
            size="sm"
            icon={ClockIcon}
            disabled={busyId !== null}
            onClick={() => setShowCounter((v) => !v)}
          >
            {showCounter ? "Close" : "Propose time"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={ChatIcon}
            onClick={() => setShowChat((v) => !v)}
          >
            {showChat ? "Hide chat" : "Chat"}
          </Button>
          <Button
            variant="dangerGhost"
            size="sm"
            icon={TrashIcon}
            loading={busyId === booking.id}
            disabled={busyId !== null}
            onClick={() => onAct(booking, "reject")}
          >
            Decline
          </Button>
        </div>
      </div>

      {booking.notes && (
        <p className="mt-3 rounded-xl border border-slate-200/70 bg-white px-3.5 py-2 text-xs leading-relaxed text-slate-600">
          <span className="font-bold text-slate-500">Seeker notes: </span>
          {booking.notes}
        </p>
      )}

      {booking.meet_link && (
        <p className="mt-3 rounded-xl border border-slate-200/70 bg-white px-3.5 py-2 text-xs leading-relaxed text-slate-600">
          <span className="font-bold text-slate-500">Seeker&apos;s meeting link: </span>
          <a
            href={booking.meet_link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:underline"
          >
            {booking.meet_link}
          </a>
        </p>
      )}

      {showCounter && (
        <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3.5">
          <p className="mb-2 text-xs font-semibold text-slate-600">
            Suggest a different time to {booking.seeker_name}
          </p>
          <TimeProposalForm
            mode="counter"
            defaultDurationMinutes={booking.duration_minutes}
            submitLabel="Propose this time"
            onSubmit={counter}
            onCancel={() => setShowCounter(false)}
          />
        </div>
      )}

      {showChat && (
        <div className="mt-3">
          <BookingChat bookingId={booking.id} counterpartName={booking.seeker_name} compact />
        </div>
      )}
    </li>
  );
}

function RequestsTab() {
  const toast = useToast();
  // Stable loader (see RequestsTopPanel) to avoid a refetch loop.
  const loader = useCallback(() => fetchConsultantSessions({ limit: 100 }), []);
  const { data, error, loading, refresh } = useAsyncData(loader);
  const [busyId, setBusyId] = useState(null);
  const requests = data?.requests?.items || [];

  async function act(booking, action) {
    setBusyId(booking.id);
    try {
      if (action === "accept") {
        await acceptBooking(booking.id);
        toast.success("Session confirmed", "A Google Calendar event and Meet link were created.");
      } else {
        await rejectBooking(booking.id);
        toast.success("Request declined", "The seeker has been notified.");
      }
      refresh();
    } catch (err) {
      toast.error("Could not update this request", err?.message);
    } finally {
      setBusyId(null);
    }
  }

  async function counter(booking, { startTime, durationMinutes, message }) {
    await counterBookingAsConsultant(booking.id, { startTime, durationMinutes, message });
    toast.success("New time proposed", "The seeker has been asked to confirm it.");
    refresh();
  }

  return (
    <Panel
      title="Booking requests"
      subtitle="Accept, decline, or propose a different time — and chat with the seeker"
    >
      {loading ? (
        <SkeletonRow lines={4} />
      ) : error ? (
        <ErrorState message={error.message} onRetry={refresh} />
      ) : requests.length === 0 ? (
        <EmptyState
          icon={CheckCircleIcon}
          title="All caught up"
          description="No open booking requests right now."
        />
      ) : (
        <ul className="space-y-3">
          {requests.map((booking) => (
            <RequestCard
              key={booking.id}
              booking={booking}
              busyId={busyId}
              onAct={act}
              onCounter={counter}
              refresh={refresh}
            />
          ))}
        </ul>
      )}
    </Panel>
  );
}

// Sessions + notes.
function SessionsTab() {
  const toast = useToast();
  const [scope, setScope] = useState("upcoming");
  // Stable loader (see RequestsTopPanel) to avoid a refetch loop.
  const loader = useCallback(() => fetchConsultantSessions({ limit: 100 }), []);
  const { data, error, loading, refresh } = useAsyncData(loader);
  const [busyId, setBusyId] = useState(null);
  const [notesTarget, setNotesTarget] = useState(null);

  const upcoming = useMemo(() => data?.upcoming?.items || [], [data]);
  const past = useMemo(() => data?.past?.items || [], [data]);
  const all = useMemo(() => [...upcoming, ...past], [upcoming, past]);
  const rows =
    scope === "upcoming" ? upcoming : scope === "past" ? past : all;

  return (
    <div className="space-y-6">
      <Panel
        title="Sessions"
        subtitle="Join your Google Meet call and record session notes"
        action={
          <Segmented
            label="Session scope"
            value={scope}
            onChange={setScope}
            options={[
              { value: "upcoming", label: "Upcoming" },
              { value: "past", label: "Past" },
              { value: "all", label: "All" },
            ]}
          />
        }
      >
        {loading ? (
          <SkeletonRow lines={5} />
        ) : error ? (
          <ErrorState message={error.message} onRetry={refresh} />
        ) : rows.length === 0 ? (
          <EmptyRow>No sessions in this view.</EmptyRow>
        ) : (
          <ul className="space-y-3">
            {rows.map((booking) => (
              <li key={booking.id}>
                <SessionCard
                  booking={booking}
                  variant="consultant"
                  actions={
                    <>
                      {booking.status === "accepted" && (
                        <Button
                          variant="secondary"
                          size="sm"
                          loading={busyId === booking.id}
                          disabled={busyId !== null}
                          onClick={async () => {
                            setBusyId(booking.id);
                            try {
                              await completeBooking(booking.id, { force: true });
                              toast.success(
                                "Session completed",
                                "The seeker can now leave feedback.",
                              );
                              refresh();
                            } catch (err) {
                              toast.error("Could not complete this session", err?.message);
                            } finally {
                              setBusyId(null);
                            }
                          }}
                        >
                          Mark complete
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setNotesTarget(booking.id);
                          document
                            .getElementById("session-notes")
                            ?.scrollIntoView({ behavior: "smooth", block: "start" });
                        }}
                      >
        Notes
                      </Button>
                    </>
                  }
                />
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <div id="session-notes">
        <SessionNotesPanel
          bookings={all}
          target={notesTarget}
          onTargetChange={setNotesTarget}
          onChanged={refresh}
        />
      </div>
    </div>
  );
}

// Session notes: private notes stay with consultant, shared notes show to seeker.
function SessionNotesPanel({ bookings = [], target, onTargetChange, onChanged }) {
  const toast = useToast();
  const [body, setBody] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);

  const booking = useMemo(() => {
    if (!bookings.length) return null;
    return bookings.find((item) => item.id === target) || bookings[0];
  }, [bookings, target]);

  // `useAsyncData` owns the fetch + error state; the loader is stable per
  // booking so switching sessions re-fetches exactly once.
  const notesLoader = useCallback(
    () => (booking ? fetchBookingNotes(booking.id) : Promise.resolve([])),
    [booking],
  );
  const {
    data: notes,
    loading: notesLoading,
    refresh: refreshNotes,
  } = useAsyncData(notesLoader, { enabled: Boolean(booking) });

  async function submit(event) {
    event.preventDefault();
    if (!body.trim() || busy || !booking) return;
    setBusy(true);
    setError(null);
    try {
      if (editingId) {
        await updateSessionNote(editingId, { body: body.trim(), visibility });
      } else {
        await addSessionNote(booking.id, { body: body.trim(), visibility });
      }
      setBody("");
      setEditingId(null);
      setVisibility("private");
      toast.success("Note saved");
      refreshNotes();
      onChanged?.();
    } catch (err) {
      setError(err?.message || "Could not save this note");
    } finally {
      setBusy(false);
    }
  }

  async function remove(noteId) {
    setBusy(true);
    try {
      await deleteSessionNote(noteId);
      toast.success("Note removed");
      refreshNotes();
      onChanged?.();
    } catch (err) {
      toast.error("Could not remove the note", err?.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel
      title="Session notes"
      subtitle="Keep private notes for yourself, or share a note with the seeker"
    >
      {!booking ? (
        <EmptyRow>No sessions to write notes for yet.</EmptyRow>
      ) : notesLoading ? (
        <SkeletonRow lines={3} />
      ) : (
        <div className="space-y-4">
          {bookings.length > 1 && (
            <div>
              <label
                htmlFor="notes-booking"
                className="text-xs font-bold uppercase tracking-wide text-slate-500"
              >
                Session
              </label>
              <select
                id="notes-booking"
                value={booking.id}
                onChange={(event) => onTargetChange?.(event.target.value)}
                className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none sm:max-w-md"
              >
                {bookings.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.subject} — {formatDateTime(item.start_time)}
                  </option>
                ))}
              </select>
            </div>
          )}

          <ul className="space-y-2">
            {notes.length === 0 ? (
              <li className="text-xs text-slate-400">No notes on this session yet.</li>
            ) : (
              notes.map((note) => (
                <li
                  key={note.id}
                  className="rounded-2xl border border-slate-200 bg-slate-50/60 px-4 py-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="min-w-0 text-xs leading-relaxed text-slate-700">{note.body}</p>
                    <Badge tone={note.visibility === "shared" ? "emerald" : "slate"}>
                      {note.visibility === "shared" ? "Shared" : "Private"}
                    </Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="text-[11px] text-slate-400">
                      {note.author_name} · {formatDateTime(note.created_at)}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditingId(note.id);
                        setBody(note.body);
                        setVisibility(note.visibility);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="dangerGhost"
                      size="sm"
                      icon={TrashIcon}
                      disabled={busy}
                      onClick={() => remove(note.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </li>
              ))
            )}
          </ul>

          <form onSubmit={submit} className="space-y-2.5 border-t border-slate-100 pt-4">
            <textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              rows={3}
              maxLength={4000}
              placeholder="What did you notice in this session? Symbols, themes, follow-ups…"
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <label className="flex items-center gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={visibility === "shared"}
                  onChange={(event) => setVisibility(event.target.checked ? "shared" : "private")}
                  className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                />
                Share this note with the seeker
              </label>
              <Button type="submit" size="sm" loading={busy} disabled={busy || !body.trim()}>
                {editingId ? "Update note" : "Add note"}
              </Button>
            </div>
            {error && <InlineError message={error} />}
          </form>
        </div>
      )}
    </Panel>
  );
}

// Google Calendar connection.
function CalendarTab() {
  const toast = useToast();
  const router = useRouter();
  const { data, error, loading, refresh } = useAsyncData(fetchCalendarStatus);
  const [pastedCode, setPastedCode] = useState(null);
  const [busy, setBusy] = useState(null);
  const [localError, setLocalError] = useState(null);

  // Google redirects back with ?code=…; surface it for one-click save instead
  // of making the consultant paste it. Derived during render, never effect-synced.
  const urlCode = router.isReady ? router.query.code : undefined;
  const urlCodeValue = Array.isArray(urlCode) ? urlCode[0] : urlCode;
  const code = pastedCode ?? urlCodeValue ?? "";
  const hasUrlCode = Boolean(urlCodeValue);

  async function startAuthorize() {
    setBusy("authorize");
    setLocalError(null);
    try {
      const { authorization_url } = await requestCalendarAuthorization();
      window.location.href = authorization_url;
    } catch (err) {
      setLocalError(err?.message || "Could not start the Google consent flow");
    } finally {
      setBusy(null);
    }
  }

  async function submitCode(event) {
    event.preventDefault();
    if (!code.trim() || busy) return;
    setBusy("connect");
    setLocalError(null);
    try {
      await connectCalendar(code.trim());
      toast.success("Google Calendar connected");
      setPastedCode("");
      refresh();
    } catch (err) {
      setLocalError(err?.message || "Could not connect your calendar");
    } finally {
      setBusy(null);
    }
  }

  async function disconnect() {
    setBusy("disconnect");
    try {
      await disconnectCalendar();
      toast.success("Google Calendar disconnected");
      refresh();
    } catch (err) {
      toast.error("Could not disconnect", err?.message);
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <SkeletonRow lines={5} />;
  if (error) return <ErrorState message={error.message} onRetry={refresh} />;

  const status = data;
  const connection = status?.connection;

  return (
    <div className="space-y-6">
      <Panel
        title="Google Calendar"
        subtitle="Where confirmed sessions create events and Google Meet links"
        action={
          connection ? (
            <Badge tone={connection.is_active ? "emerald" : "slate"}>
              {connection.is_active ? "Connected" : "Disabled"}
            </Badge>
          ) : (
            <Badge tone="slate">Not connected</Badge>
          )
        }
      >
        <div className="space-y-4">
          <p className="text-sm leading-relaxed text-slate-600">
            When you accept a booking, MysticLens creates a calendar event with an auto-generated
            Google Meet link. Events land on the calendar you connect here, so the meeting belongs
            to you — not to a shared platform calendar.
          </p>

          {!status.calendar_enabled && (
            <div className="rounded-2xl border border-accent-200/60 bg-accent-50 px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wide text-accent-800">
                Google Calendar is disabled on this server
              </p>
              <p className="mt-1 text-xs leading-relaxed text-accent-900">
                Set <code className="font-mono">GOOGLE_CALENDAR_ENABLED=true</code> in the backend
                environment to turn the integration on. Booking still works without it; sessions
                simply will not get a Meet link.
              </p>
            </div>
          )}

          {connection ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <dl className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Google account
                  </dt>
                  <dd className="mt-1 text-slate-800">{connection.google_email || "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Calendar
                  </dt>
                  <dd className="mt-1 font-mono text-xs text-slate-800">
                    {connection.calendar_id}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Connected
                  </dt>
                  <dd className="mt-1 text-slate-800">{formatDateTime(connection.connected_at)}</dd>
                </div>
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Events created
                  </dt>
                  <dd className="mt-1 text-slate-800">{status.synced_bookings ?? 0}</dd>
                </div>
              </dl>

              {connection.last_error && (
                <p className="mt-3 rounded-xl border border-rose-200/60 bg-rose-50 px-3.5 py-2 text-xs text-rose-800">
                  {connection.last_error}
                </p>
              )}

              <div className="mt-4 flex flex-wrap gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  loading={busy === "disconnect"}
                  disabled={busy !== null}
                  onClick={disconnect}
                >
                  Disconnect
                </Button>
                {!connection.is_active && (
                  <Button size="sm" onClick={disconnect}>
                    Re-enable
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Button
                  icon={VideoIcon}
                  loading={busy === "authorize"}
                  disabled={busy !== null}
                  onClick={startAuthorize}
                >
                  Connect Google Calendar
                </Button>
                {status.service_account_configured && (
                  <span className="inline-flex items-center text-xs text-slate-500">
                    A platform calendar is configured and is used as a fallback.
                  </span>
                )}
              </div>

              <details className="rounded-2xl border border-slate-200 bg-slate-50/60 px-4 py-3">
                <summary className="cursor-pointer text-xs font-bold uppercase tracking-wide text-slate-600">
                  Or paste the authorisation code
                </summary>
                <form onSubmit={submitCode} className="mt-3 space-y-2.5">
                  <input
                    value={pastedCode ?? ""}
                    onChange={(event) => setPastedCode(event.target.value)}
                    placeholder="4/0A… from the Google consent screen"
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 font-mono text-xs text-slate-900 shadow-xs focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
                  />
                  <Button
                    type="submit"
                    size="sm"
                    loading={busy === "connect"}
                    disabled={busy !== null || !code.trim()}
                  >
                    Save code
                  </Button>
                </form>
              </details>
            </div>
          )}

          {localError && <InlineError message={localError} />}

          {!status.oauth_configured && (
            <p className="text-xs text-slate-500">
              Google OAuth is not configured on this server. Set{" "}
              <code className="font-mono">GOOGLE_CLIENT_ID</code> and{" "}
              <code className="font-mono">GOOGLE_CLIENT_SECRET</code> to let consultants connect their
              own calendars.
            </p>
          )}
        </div>
      </Panel>

      <Panel title="How it works">
        <ol className="space-y-2.5 text-sm text-slate-600">
          <li className="flex gap-2.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-100 text-[11px] font-bold text-primary-700">
              1
            </span>
            A seeker books one of your open slots. The booking starts as{" "}
            <span className="font-semibold">pending</span>.
          </li>
          <li className="flex gap-2.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-100 text-[11px] font-bold text-primary-700">
              2
            </span>
            You accept it — MysticLens creates the calendar event and asks Google for a Meet
            link.
          </li>
          <li className="flex gap-2.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-100 text-[11px] font-bold text-primary-700">
              3
            </span>
            Both of you see the link and a <span className="font-semibold">Join Google Meet</span>{" "}
            button 30 minutes before the session.
          </li>
          <li className="flex gap-2.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-100 text-[11px] font-bold text-primary-700">
              4
            </span>
            Cancelling removes the event; completing the session unlocks seeker feedback.
          </li>
        </ol>
      </Panel>
    </div>
  );
}
