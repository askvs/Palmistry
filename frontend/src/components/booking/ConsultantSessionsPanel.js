// Consultant session panel for the reader/consultant dashboards (FR-BOOK-008).
import { useCallback, useMemo, useState } from "react";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { CalendarIcon, CheckCircleIcon, ClockIcon, TrashIcon, VideoIcon } from "@/components/icons";
import {
  BookingStatusBadge,
  CalendarSyncBadge,
  EmptyRow,
} from "@/components/booking/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { acceptBooking, fetchConsultantSessions, rejectBooking } from "@/services/booking";
import { canJoinMeet, formatRange } from "@/lib/datetime";

// One pending request with accept / decline actions.
function RequestRow({ booking, onResolved }) {
  const toast = useToast();
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);

  async function act(action, label, success) {
    setBusy(action);
    setError(null);
    try {
      await (action === "accept" ? acceptBooking(booking.id) : rejectBooking(booking.id));
      toast.success(success.title, success.message);
      onResolved?.();
    } catch (err) {
      setError(err?.message || `Could not ${label} this request`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <li className="rounded-2xl border border-accent-200/70 bg-accent-50/50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-xs text-slate-600">
            from <span className="font-semibold">{booking.seeker_name}</span>
            {booking.seeker_email ? ` · ${booking.seeker_email}` : ""}
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
            <CalendarIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatRange(booking.start_time, booking.end_time)}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button
            size="sm"
            icon={CheckCircleIcon}
            loading={busy === "accept"}
            disabled={busy !== null}
            onClick={() =>
              act("accept", "accept", {
                title: "Session confirmed",
                message: "A Google Calendar event and Meet link have been created.",
              })
            }
          >
            Accept
          </Button>
          <Button
            variant="dangerGhost"
            size="sm"
            icon={TrashIcon}
            loading={busy === "reject"}
            disabled={busy !== null}
            onClick={() =>
              act("reject", "decline", {
                title: "Request declined",
                message: "The seeker has been notified.",
              })
            }
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
      {error && (
        <div className="mt-3">
          <InlineError message={error} />
        </div>
      )}
    </li>
  );
}

// One confirmed session; the Meet button unlocks 30 minutes before the start.
function ConfirmedSession({ booking }) {
  const joinable = canJoinMeet(booking);
  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
            <CalendarSyncBadge booking={booking} />
          </div>
          <p className="mt-1 text-xs text-slate-600">
            with <span className="font-semibold">{booking.seeker_name}</span>
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
            <ClockIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatRange(booking.start_time, booking.end_time)}
          </p>
        </div>
        {joinable ? (
          <Button
            href={booking.meet_link}
            target="_blank"
            rel="noopener noreferrer"
            size="sm"
            icon={VideoIcon}
          >
            Join Google Meet
          </Button>
        ) : (
          <Badge tone="slate">Opens 30 min before</Badge>
        )}
      </div>
    </li>
  );
}

export default function ConsultantSessionsPanel({ limit = 6 }) {
  // Stable loader: useAsyncData re-runs whenever the loader identity changes,
  // so an inline arrow here would refetch on every render (infinite loop).
  const loader = useCallback(
    () => fetchConsultantSessions({ limit }),
    [limit],
  );
  const { data, error, loading, refresh } = useAsyncData(loader);
  const requests = useMemo(() => data?.requests?.items || [], [data]);
  const upcoming = useMemo(() => data?.upcoming?.items || [], [data]);
  const recent = useMemo(
    () => (data?.past?.items || []).slice(0, limit),
    [data, limit],
  );

  return (
    <Panel
      title="Live Consultation Requests"
      subtitle="Accept or decline booking requests and join confirmed sessions"
      action={
        <Button href="/consultant-studio" variant="secondary" size="sm" icon={CalendarIcon}>
          Consultant Studio
        </Button>
      }
    >
      <div className="space-y-6">
        <section>
          <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-slate-500">
            Pending requests {requests.length > 0 && `(${requests.length})`}
          </p>
          {loading ? (
            <SkeletonRow lines={3} />
          ) : error ? (
            <ErrorState message={error.message} onRetry={refresh} />
          ) : requests.length === 0 ? (
            <EmptyRow>No open booking requests right now.</EmptyRow>
          ) : (
            <ul className="space-y-3">
              {requests.map((booking) => (
                <RequestRow key={booking.id} booking={booking} onResolved={refresh} />
              ))}
            </ul>
          )}
        </section>

        <section>
          <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-slate-500">
            Upcoming sessions
          </p>
          {loading ? (
            <SkeletonRow lines={3} />
          ) : upcoming.length === 0 ? (
            <EmptyState
              icon={CalendarIcon}
              title="Nothing booked"
              description="Publish availability in the Consultant Studio so seekers can book you."
              action={
                <Button href="/consultant-studio" size="sm">
                  Open Consultant Studio
                </Button>
              }
            />
          ) : (
            <ul className="space-y-3">
              {upcoming.map((booking) => (
                <ConfirmedSession key={booking.id} booking={booking} />
              ))}
            </ul>
          )}
        </section>

        {recent.length > 0 && (
          <section>
            <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-slate-500">
              Recent sessions
            </p>
            <ul className="divide-y divide-slate-100">
              {recent.map((booking) => (
                <li
                  key={booking.id}
                  className="flex items-center justify-between gap-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-800">
                      {booking.subject}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {booking.seeker_name} · {formatRange(booking.start_time, booking.end_time)}
                    </p>
                  </div>
                  <BookingStatusBadge status={booking.status} />
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </Panel>
  );
}
