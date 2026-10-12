// Shared presentational primitives for the live consultation & booking module.
import { useState } from "react";
import Link from "next/link";
import KitBadge from "@/components/ui/Badge";
import KitButton from "@/components/ui/Button";
import {
  Badge,
  Button,
  EmptyState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import {
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  StarIcon,
  VideoIcon,
} from "@/components/icons";
import {
  canJoinMeet,
  formatDateTime,
  formatDuration,
  formatRange,
  formatTime,
  relativeFromNow,
} from "@/lib/datetime";

export { Panel, Badge, Button, EmptyState, SkeletonRow, useToast, InlineError };

// Dashed empty-state row, matching `components/dashboards/shared.js`.
export function EmptyRow({ children }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

// Display label, badge tone and help text for every booking status.
export const BOOKING_STATUS = {
  pending: {
    label: "Pending",
    tone: "accent",
    hint: "Waiting for the consultant to accept your request.",
  },
  countered: {
    label: "New time proposed",
    tone: "amber",
    hint: "A new time is on the table — confirm it or suggest another.",
  },
  accepted: {
    label: "Confirmed",
    tone: "emerald",
    hint: "Confirmed. Your Google Meet link is ready below.",
  },
  rejected: {
    label: "Declined",
    tone: "rose",
    hint: "The consultant could not take this session.",
  },
  cancelled: {
    label: "Cancelled",
    tone: "slate",
    hint: "This session is no longer happening.",
  },
  completed: {
    label: "Completed",
    tone: "primary",
    hint: "This session is complete — leave feedback below.",
  },
};

export const SESSION_SCOPE_LABELS = {
  upcoming: "Upcoming",
  past: "Past",
  all: "All",
};

export function BookingStatusBadge({ status }) {
  const meta = BOOKING_STATUS[status] || { label: status, tone: "slate" };
  return <KitBadge tone={meta.tone}>{meta.label}</KitBadge>;
}

// Calendar-sync chip; explains the Google Meet state on accepted bookings.
export function CalendarSyncBadge({ booking }) {
  const status = booking?.calendar_sync_status;
  if (booking?.status !== "accepted" && status !== "created") return null;
  const config = {
    created: { tone: "emerald", label: "Meet link ready" },
    not_created: { tone: "slate", label: "No calendar connected" },
    failed: { tone: "rose", label: "Calendar sync failed" },
    disabled: { tone: "slate", label: "Calendar disabled" },
    cancelled: { tone: "slate", label: "Calendar event removed" },
  }[status] || { tone: "slate", label: status };
  return <KitBadge tone={config.tone}>{config.label}</KitBadge>;
}

// Session row used by both the seeker hub and the consultant studio.
export function SessionCard({
  booking,
  variant = "seeker",
  actions,
  onOpen,
  defaultOpen = false,
}) {
  const [open, setOpen] = useState(defaultOpen);
  const isConsultant = variant === "consultant";
  const counterpart = isConsultant
    ? booking?.seeker_name || "Seeker"
    : booking?.consultant_name || "Consultant";
  const joinable = canJoinMeet(booking);
  const meta = BOOKING_STATUS[booking?.status] || {};

  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 transition hover:border-primary-200 hover:shadow-md">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking?.subject}</h4>
            <BookingStatusBadge status={booking?.status} />
            {booking?.status === "accepted" && <CalendarSyncBadge booking={booking} />}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {isConsultant ? "Seeker: " : "Consultant: "}
            <span className="font-semibold text-slate-700">{counterpart}</span>
            {isConsultant && booking?.seeker_email ? ` · ${booking.seeker_email}` : ""}
            {!isConsultant && booking?.consultant_headline ? ` · ${booking.consultant_headline}` : ""}
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
            <CalendarIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatRange(booking?.start_time, booking?.end_time)}
            <span className="text-slate-300">·</span>
            <ClockIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatDuration(booking?.duration_minutes)}
            <span className="text-slate-300">·</span>
            {relativeFromNow(booking?.start_time)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {booking?.meet_link && joinable && (
            <KitButton
              href={booking.meet_link}
              target="_blank"
              rel="noopener noreferrer"
              size="sm"
              icon={VideoIcon}
            >
              Join Google Meet
            </KitButton>
          )}
          {actions}
        </div>
      </div>

      {booking?.notes && (
        <p className="mt-3 rounded-xl border border-slate-200/70 bg-white px-3.5 py-2 text-xs leading-relaxed text-slate-600">
          <span className="font-bold text-slate-500">Seeker notes: </span>
          {booking.notes}
        </p>
      )}

      {booking?.status === "cancelled" && booking?.cancellation_reason && (
        <p className="mt-3 rounded-xl border border-rose-200/60 bg-rose-50 px-3.5 py-2 text-xs leading-relaxed text-rose-800">
          <span className="font-bold">Cancellation reason: </span>
          {booking.cancellation_reason}
        </p>
      )}

      {onOpen && (
        <div className="mt-3">
          <KitButton variant="ghost" size="sm" onClick={() => setOpen((v) => !v)}>
            {open ? "Hide details" : "View details"}
          </KitButton>
        </div>
      )}

      {open && onOpen && (
        <div className="mt-3 rounded-xl border border-slate-200/70 bg-white p-3.5">
          {onOpen(booking)}
        </div>
      )}
    </li>
  );
}

// Day-by-day availability picker.
export function SlotPicker({
  days,
  daySlots,
  selectedDate,
  selectedSlotId,
  onSelectDate,
  onSelectSlot,
  busy,
  disabledSlots = [],
}) {
  if (!days || days.length === 0) {
    return (
      <EmptyState
        icon={CalendarIcon}
        title="No availability published"
        description="This consultant hasn't published any open slots yet. Check back soon."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div
        className="flex gap-2 overflow-x-auto pb-2"
        role="tablist"
        aria-label="Available days"
      >
        {days.map((day) => {
          const active = day.date === selectedDate;
          const hasSlots = day.available_slots > 0;
          return (
            <button
              key={day.date}
              type="button"
              role="tab"
              aria-selected={active}
              disabled={!hasSlots}
              onClick={() => onSelectDate(day.date)}
              className={`flex w-16 shrink-0 flex-col items-center gap-0.5 rounded-2xl border px-2 py-2.5 text-xs transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-40 ${
                active
                  ? "border-primary-500 bg-primary-50 text-primary-700 shadow-xs"
                  : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              <span className="font-bold uppercase tracking-wide">{day.weekday}</span>
              <span className="text-base font-bold text-slate-900">{day.dayOfMonth}</span>
              <span
                className={`text-[10px] font-semibold ${
                  hasSlots ? "text-emerald-600" : "text-slate-400"
                }`}
              >
                {hasSlots ? `${day.available_slots} open` : "full"}
              </span>
            </button>
          );
        })}
      </div>

      {!daySlots || daySlots.length === 0 ? (
        <EmptyRow>No open slots on this day. Pick another day above.</EmptyRow>
      ) : (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
          {daySlots.map((slot) => {
            const disabled = disabledSlots.includes(slot.id);
            const active = slot.id === selectedSlotId;
            return (
              <button
                key={slot.id}
                type="button"
                aria-pressed={active}
                disabled={disabled || busy}
                onClick={() => onSelectSlot(slot)}
                className={`rounded-xl border px-2 py-2 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-40 ${
                  active
                    ? "border-primary-500 bg-primary-600 text-white shadow-sm"
                    : "border-slate-200 bg-white text-slate-700 hover:border-primary-300 hover:bg-primary-50"
                }`}
              >
                {formatTime(slot.start_time)}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Marketing-style card for one consultant in the directory grid.
export function ConsultantCard({ consultant }) {
  return (
    <Link
      href={`/consultants/${consultant.id}`}
      className="group block rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs transition-all duration-300 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-base font-semibold text-slate-900 transition group-hover:text-primary-700">
            {consultant.full_name || "Consultant"}
          </h3>
          <p className="mt-0.5 truncate text-xs text-slate-500">{consultant.headline}</p>
        </div>
        {consultant.avg_rating != null && (
          <span className="flex shrink-0 items-center gap-1 rounded-full bg-accent-50 px-2 py-0.5 text-xs font-bold text-accent-700">
            <StarIcon className="h-3.5 w-3.5" />
            {Number(consultant.avg_rating).toFixed(1)}
          </span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {(consultant.specializations || []).slice(0, 3).map((tag) => (
          <KitBadge key={tag} tone="primary">
            {tag}
          </KitBadge>
        ))}
        {(consultant.specializations || []).length > 3 && (
          <KitBadge tone="slate">+{consultant.specializations.length - 3}</KitBadge>
        )}
      </div>

      <div className="mt-4 flex items-end justify-between gap-3">
        <p className="text-xs text-slate-500">
          {consultant.years_experience}+ yrs · {consultant.session_duration_minutes} min
        </p>
        <p className="text-sm font-bold text-slate-900">
          {consultant.currency} {consultant.session_rate}
        </p>
      </div>

      <div className="mt-4">
        <KitButton
          href={`/consultants/${consultant.id}`}
          variant="secondary"
          size="sm"
          fullWidth
          iconRight={CalendarIcon}
        >
          View availability
        </KitButton>
      </div>
    </Link>
  );
}

// Star rating input (1–5) used by the feedback form.
export function RatingStars({ value, onChange, disabled = false, label = "Rating" }) {
  return (
    <div role="radiogroup" aria-label={label} className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star === 1 ? "" : "s"}`}
          disabled={disabled}
          onClick={() => onChange?.(star)}
          className={`cursor-pointer rounded-full p-1 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-50 ${
            star <= (value || 0) ? "text-accent-500" : "text-slate-300 hover:text-accent-400"
          }`}
        >
          <StarIcon className="h-6 w-6" />
        </button>
      ))}
    </div>
  );
}

// Reusable "leave feedback for this completed session" panel body.
export function FeedbackForm({ booking, onSubmitted }) {
  const toast = useToast();
  const [rating, setRating] = useState(0);
  const [review, setReview] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const existing = booking?.feedback;

  async function submit(event) {
    event.preventDefault();
    if (!rating || busy) return;
    setBusy(true);
    setError(null);
    try {
      const { submitFeedback } = await import("@/services/booking");
      await submitFeedback(booking.id, { rating, review, isPublic: true });
      toast.success("Thanks for the feedback", "Your review helps other seekers choose.");
      onSubmitted?.();
    } catch (err) {
      setError(err?.message || "Could not submit your review");
    } finally {
      setBusy(false);
    }
  }

  if (existing) {
    return (
      <div className="rounded-2xl border border-emerald-200/60 bg-emerald-50 px-4 py-3">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
          Your review
        </p>
        <div className="mt-2 flex items-center gap-2">
          <RatingStars value={existing.rating} disabled />
          <span className="text-xs text-slate-500">
            {formatDateTime(existing.created_at)}
          </span>
        </div>
        {existing.review && (
          <p className="mt-2 text-xs leading-relaxed text-emerald-900">{existing.review}</p>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <RatingStars value={rating} onChange={setRating} disabled={busy} />
      <textarea
        value={review}
        onChange={(event) => setReview(event.target.value)}
        placeholder="How was your session? (optional)"
        rows={3}
        maxLength={4000}
        aria-label="Your review"
        className="w-full rounded-2xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      />
      {error && <InlineError message={error} />}
      <div className="flex justify-end">
        <KitButton
          type="submit"
          size="sm"
          icon={CheckCircleIcon}
          loading={busy}
          disabled={busy || !rating}
        >
          Submit review
        </KitButton>
      </div>
    </form>
  );
}

// Session history timeline used on the booking detail view.
export function BookingTimeline({ events = [] }) {
  if (!events.length) {
    return <EmptyRow>No activity recorded for this session yet.</EmptyRow>;
  }
  return (
    <ol className="relative space-y-4 pl-6 before:absolute before:bottom-2 before:left-2 before:top-2 before:w-0.5 before:bg-slate-200">
      {events.map((event) => (
        <li key={event.id} className="relative">
          <span className="absolute -left-[23px] top-1.5 h-3.5 w-3.5 rounded-full border-2 border-white bg-primary-600 ring-2 ring-primary-200" />
          <p className="text-xs font-semibold text-slate-800">
            {(BOOKING_STATUS[event.to_status]?.label || event.to_status || event.event_type)}
            <span className="ml-2 font-normal text-slate-400">
              {formatDateTime(event.created_at)}
            </span>
          </p>
          <p className="mt-0.5 text-xs text-slate-600">
            {event.message || `by ${event.actor_name || "system"}`}
          </p>
        </li>
      ))}
    </ol>
  );
}
