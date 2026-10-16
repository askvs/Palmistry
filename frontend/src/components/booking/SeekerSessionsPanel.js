// Seeker session panel for the user dashboard (FR-BOOK-007).
import { useCallback, useMemo, useState } from "react";
import {
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { ConfirmDialog } from "@/components/ui";
import { CalendarIcon, ClockIcon, TrashIcon, VideoIcon } from "@/components/icons";
import { BookingStatusBadge, FeedbackForm } from "@/components/booking/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { cancelBooking, fetchSeekerSessions } from "@/services/booking";
import { canJoinMeet, formatRange } from "@/lib/datetime";

// Upcoming session row with join / cancel affordances.
function UpcomingSession({ booking, onCancelled }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState(null);

  const joinable = canJoinMeet(booking);

  async function cancel() {
    setBusy(true);
    setError(null);
    try {
      await cancelBooking(booking.id);
      toast.success("Session cancelled", "The consultant has been notified.");
      onCancelled?.();
    } catch (err) {
      setError(err?.message || "Could not cancel this session");
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  }

  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-xs text-slate-600">
            with <span className="font-semibold">{booking.consultant_name}</span>
            {booking.consultant_headline ? ` · ${booking.consultant_headline}` : ""}
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
            <CalendarIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatRange(booking.start_time, booking.end_time)}
            <span className="text-slate-300">·</span>
            <ClockIcon className="h-3.5 w-3.5 text-slate-400" />
            {booking.duration_minutes} min
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {joinable && (
            <Button
              href={booking.meet_link}
              target="_blank"
              rel="noopener noreferrer"
              size="sm"
              icon={VideoIcon}
            >
              Join Google Meet
            </Button>
          )}
          <Button
            variant="dangerGhost"
            size="sm"
            icon={TrashIcon}
            onClick={() => setConfirming(true)}
            disabled={busy}
          >
            Cancel
          </Button>
        </div>
      </div>

      {booking.status === "accepted" && !joinable && (
        <p className="mt-3 flex items-center gap-1.5 rounded-xl border border-slate-200/70 bg-white px-3.5 py-2 text-xs text-slate-500">
          <VideoIcon className="h-3.5 w-3.5" />
          The Google Meet link appears here before the session.
        </p>
      )}

      {booking.status === "pending" && (
        <p className="mt-3 rounded-xl border border-accent-200/60 bg-accent-50 px-3.5 py-2 text-xs leading-relaxed text-accent-800">
          Waiting for the consultant to accept your request.
        </p>
      )}

      {error && (
        <div className="mt-3">
          <InlineError message={error} />
        </div>
      )}

      <ConfirmDialog
        open={confirming}
        title="Cancel this session?"
        message={`"${booking.subject}" with ${booking.consultant_name} will be cancelled and the
          consultant will be notified.`}
        confirmLabel="Yes, cancel"
        tone="danger"
        loading={busy}
        onConfirm={cancel}
        onCancel={() => setConfirming(false)}
      />
    </li>
  );
}

// Past session row: outcome badge plus feedback for completed sessions.
function PastSession({ booking, onFeedback }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-xs text-slate-600">
            with <span className="font-semibold">{booking.consultant_name}</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">{formatRange(booking.start_time, booking.end_time)}</p>
          {booking.status === "cancelled" && booking.cancellation_reason && (
            <p className="mt-1.5 text-xs text-rose-700">Reason: {booking.cancellation_reason}</p>
          )}
        </div>
        {booking.status === "completed" && (
          <Button
            variant="ghost"
            size="sm"
            icon={CheckCircleIcon}
            onClick={() => setOpen((v) => !v)}
          >
            {booking.feedback ? "Your review" : "Leave feedback"}
          </Button>
        )}
      </div>

      {booking.status === "completed" && open && (
        <div className="mt-3 border-t border-slate-100 pt-3">
          <FeedbackForm booking={booking} onSubmitted={onFeedback} />
        </div>
      )}
    </li>
  );
}

export default function SeekerSessionsPanel({ limit = 4 }) {
  // Stable loader: useAsyncData re-runs whenever the loader identity changes,
  // so an inline arrow here would refetch on every render (infinite loop).
  const loader = useCallback(
    () => fetchSeekerSessions({ upcomingLimit: limit, pastLimit: limit }),
    [limit],
  );
  const { data, error, loading, refresh } = useAsyncData(loader);
  const upcomingItems = useMemo(() => data?.upcoming?.items || [], [data]);
  const pastItems = useMemo(() => data?.past?.items || [], [data]);

  return (
    <Panel
      title="Live Consultations"
      subtitle="Sessions with tarot readers and spiritual consultants"
      action={
        <Button href="/consultants" variant="secondary" size="sm" icon={CalendarIcon}>
          Find a consultant
        </Button>
      }
    >
      <div className="space-y-6">
        <section>
          <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-slate-500">
            Upcoming
          </p>
          {loading ? (
            <div className="space-y-3 py-2">
              <SkeletonRow lines={3} />
              <SkeletonRow lines={3} />
            </div>
          ) : error ? (
            <ErrorState message={error.message} onRetry={refresh} />
          ) : upcomingItems.length === 0 ? (
            <EmptyState
              icon={CalendarIcon}
              title="No upcoming sessions"
              description="Browse consultant profiles and book your first live consultation."
              action={
                <Button href="/consultants" size="sm">
                  Browse consultants
                </Button>
              }
            />
          ) : (
            <ul className="space-y-3">
              {upcomingItems.map((booking) => (
                <UpcomingSession
                  key={booking.id}
                  booking={booking}
                  onCancelled={refresh}
                />
              ))}
            </ul>
          )}
        </section>

        <section>
          <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-slate-500">
            Past sessions
          </p>
          {loading ? (
            <SkeletonRow lines={2} />
          ) : pastItems.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-6 text-center text-sm text-slate-500">
            Your completed and cancelled sessions will appear here.
          </div>
          ) : (
            <ul className="space-y-3">
              {pastItems.map((booking) => (
                <PastSession key={booking.id} booking={booking} onFeedback={refresh} />
              ))}
            </ul>
          )}
        </section>

        <Button href="/sessions" variant="ghost" size="sm">
          View all sessions
        </Button>
      </div>
    </Panel>
  );
}
