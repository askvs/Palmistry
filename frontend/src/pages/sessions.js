// Seeker session hub: upcoming, past, feedback, and cancellation.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import {
  Button,
  EmptyState,
  ErrorState,
  Panel,
  PageHeader,
  useToast,
} from "@/components/ui";
import { ConfirmDialog } from "@/components/ui";
import { Segmented } from "@/components/dashboards/shared";
import { CalendarIcon, ChatIcon, ClockIcon, TrashIcon, UsersIcon, VideoIcon } from "@/components/icons";
import {
  BookingStatusBadge,
  BookingTimeline,
  EmptyRow,
  FeedbackForm,
} from "@/components/booking/shared";
import BookingChat from "@/components/booking/BookingChat";
import TimeProposalForm from "@/components/booking/TimeProposalForm";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  cancelBooking,
  confirmBooking,
  counterBookingAsSeeker,
  fetchMyBookings,
} from "@/services/booking";
import {
  canJoinMeet,
  formatDateTime,
  formatDuration,
  formatRange,
  relativeFromNow,
} from "@/lib/datetime";
import { BOOKING_STATUS } from "@/components/booking/shared";

const SCOPES = [
  { value: "upcoming", label: "Upcoming" },
  { value: "past", label: "Past" },
  { value: "all", label: "All" },
];

const PAGE_SIZE = 20;

// One booking row; onChanged refreshes the list after a mutation.
function BookingRow({ booking, onChanged }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [showCounter, setShowCounter] = useState(false);

  const joinable = canJoinMeet(booking);
  const meta = BOOKING_STATUS[booking.status] || {};
  const isNegotiating = booking.status === "pending" || booking.status === "countered";
  const awaitingSeeker = booking.status === "countered";
  const canChat = isNegotiating || booking.status === "accepted";

  async function doCancel() {
    setBusy(true);
    setError(null);
    try {
      await cancelBooking(booking.id);
      toast.success("Session cancelled", "The consultant has been notified.");
      onChanged?.();
    } catch (err) {
      setError(err?.message || "Could not cancel this session");
    } finally {
      setBusy(false);
      setCancelling(false);
    }
  }

  async function confirmTime() {
    setBusy(true);
    setError(null);
    try {
      await confirmBooking(booking.id);
      toast.success("Time confirmed", "Your session is being set up with a Meet link.");
      onChanged?.();
    } catch (err) {
      setError(err?.message || "Could not confirm this time");
    } finally {
      setBusy(false);
    }
  }

  async function counterTime({ startTime, durationMinutes, message }) {
    await counterBookingAsSeeker(booking.id, { startTime, durationMinutes, message });
    toast.success("New time suggested", "The consultant has been asked to confirm it.");
    setShowCounter(false);
    onChanged?.();
  }

  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 transition hover:border-primary-200">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-xs text-slate-600">
            with{" "}
            <Link
              href={`/consultants/${booking.consultant_id}`}
              className="font-semibold text-primary-600 hover:underline"
            >
              {booking.consultant_name}
            </Link>
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
            <CalendarIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatRange(booking.start_time, booking.end_time)}
            <span className="text-slate-300">·</span>
            <ClockIcon className="h-3.5 w-3.5 text-slate-400" />
            {formatDuration(booking.duration_minutes)}
            <span className="text-slate-300">·</span>
            {relativeFromNow(booking.start_time)}
          </p>
          {booking.cancellation_reason && booking.status === "cancelled" && (
            <p className="mt-1.5 text-xs text-rose-700">
              Reason: {booking.cancellation_reason}
            </p>
          )}
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
          {canChat && (
            <Button
              variant="ghost"
              size="sm"
              icon={ChatIcon}
              onClick={() => setShowChat((v) => !v)}
              aria-expanded={showChat}
            >
              {showChat ? "Hide chat" : "Chat"}
            </Button>
          )}
          {(isNegotiating || booking.status === "accepted") && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setOpen((v) => !v)}
                aria-expanded={open}
              >
                {open ? "Hide" : "Details"}
              </Button>
              <Button
                variant="dangerGhost"
                size="sm"
                icon={TrashIcon}
                disabled={busy}
                onClick={() => setCancelling(true)}
              >
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Negotiation banner: whose turn is it, and the time on the table. */}
      {isNegotiating && (
        <div
          className={`mt-3 rounded-2xl border px-4 py-3 ${
            awaitingSeeker
              ? "border-amber-200 bg-amber-50/70"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          {awaitingSeeker ? (
            <>
              <p className="text-xs font-semibold text-amber-800">
                {booking.consultant_name} proposed a new time:
              </p>
              <p className="mt-0.5 text-sm font-semibold text-amber-900">
                {formatRange(booking.start_time, booking.end_time)}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" loading={busy} onClick={confirmTime}>
                  Confirm this time
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowCounter((v) => !v)}
                >
                  {showCounter ? "Close" : "Suggest another time"}
                </Button>
              </div>
            </>
          ) : (
            <p className="text-xs text-slate-600">
              Waiting for {booking.consultant_name} to confirm your requested time
              {". "}
              You can suggest a different time or chat with them below.
              <span className="ml-1">
                <button
                  type="button"
                  onClick={() => setShowCounter((v) => !v)}
                  className="font-semibold text-primary-600 hover:underline"
                >
                  {showCounter ? "Close" : "Suggest another time"}
                </button>
              </span>
            </p>
          )}

          {showCounter && (
            <div className="mt-3 border-t border-slate-200/70 pt-3">
              <TimeProposalForm
                mode="counter"
                defaultDurationMinutes={booking.duration_minutes}
                submitLabel="Send new time"
                onSubmit={counterTime}
                onCancel={() => setShowCounter(false)}
              />
            </div>
          )}
        </div>
      )}

      {canChat && showChat && (
        <div className="mt-3">
          <BookingChat bookingId={booking.id} counterpartName={booking.consultant_name} compact />
        </div>
      )}

      {error && (
        <div className="mt-3">
          <p className="text-xs text-rose-700">{error}</p>
        </div>
      )}

      {open && (
        <div className="mt-4 space-y-4 border-t border-slate-100 pt-4">
          {booking.status === "accepted" && booking.meet_link && (
            <div className="rounded-2xl border border-emerald-200/60 bg-emerald-50 px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                Google Meet
              </p>
              <a
                href={booking.meet_link}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 block break-all text-sm font-semibold text-emerald-800 underline decoration-emerald-300 underline-offset-2 hover:text-emerald-900"
              >
                {booking.meet_link}
              </a>
              {!joinable && (
                <p className="mt-1.5 text-xs text-emerald-700">
                  The link opens 30 minutes before the session starts.
                </p>
              )}
            </div>
          )}

          {booking.notes && (
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                Your notes
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-600">{booking.notes}</p>
            </div>
          )}

          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
              History
            </p>
            <BookingTimeline events={booking.events || []} />
          </div>

          {booking.session_notes && booking.session_notes.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                Consultant session notes
              </p>
              <ul className="space-y-2">
                {booking.session_notes.map((note) => (
                  <li
                    key={note.id}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
                  >
                    <p className="text-xs leading-relaxed text-slate-700">{note.body}</p>
                    <p className="mt-1 text-[11px] text-slate-400">
                      {note.author_name || "Consultant"} · {formatDateTime(note.created_at)}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {booking.status === "completed" && (
            <div>
              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                Feedback
              </p>
              <FeedbackForm booking={booking} onSubmitted={() => onChanged?.()} />
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        open={cancelling}
        title="Cancel this session?"
        message={`"${booking.subject}" with ${booking.consultant_name} will be cancelled and the
          consultant notified. Sessions inside the free-cancellation window can only be cancelled by
          the consultant.`}
        confirmLabel="Yes, cancel"
        tone="danger"
        loading={busy}
        onConfirm={doCancel}
        onCancel={() => setCancelling(false)}
      />
    </li>
  );
}

export default function SessionsPage() {
  const router = useRouter();
  const [scope, setScope] = useState("upcoming");
  const [offset, setOffset] = useState(0);
  const justBooked = Array.isArray(router.query.booked)
    ? router.query.booked[0]
    : router.query.booked;

  const loader = useCallback(
    () => fetchMyBookings({ scope, limit: PAGE_SIZE, offset }),
    [scope, offset],
  );
  const { data, error, loading, refresh } = useAsyncData(loader);

  const items = useMemo(() => data?.items || [], [data]);
  const total = data?.total ?? 0;
  const hasNext = offset + PAGE_SIZE < total;

  // The just-booked booking stays highlighted while it is still in the URL.
  const highlight = justBooked ?? null;

  return (
    <div className="animate-fade-in space-y-8">
      <PageHeader
        icon={CalendarIcon}
        eyebrow="Live consultations"
        title="My sessions"
        description="Track every live session you have booked, join the Google Meet call, and
          leave feedback once a session is complete."
        actions={
          <Button href="/consultants" icon={UsersIcon}>
            Book another session
          </Button>
        }
      />

      {justBooked && highlight && (
        <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 text-sm text-emerald-900">
          <VideoIcon className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
          <p>
            Your booking request has been sent. It shows as{" "}
            <span className="font-semibold">Pending</span> until the consultant accepts — the
            Google Meet link appears here as soon as it is shared.
          </p>
        </div>
      )}

      <Panel
        title="Sessions"
        subtitle={`${total} session${total === 1 ? "" : "s"} in this view`}
        action={
          <Segmented
            label="Session scope"
            value={scope}
            onChange={(value) => {
              setScope(value);
              setOffset(0);
            }}
            options={SCOPES}
          />
        }
      >
        {loading ? (
          <div className="space-y-3 py-2">
            <div className="h-20 animate-pulse rounded-2xl bg-slate-100" />
            <div className="h-20 animate-pulse rounded-2xl bg-slate-100" />
          </div>
        ) : error ? (
          <ErrorState message={error.message} onRetry={refresh} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={CalendarIcon}
            title={scope === "upcoming" ? "No upcoming sessions" : "No sessions here yet"}
            description={
              scope === "upcoming"
                ? "Browse consultant profiles and book your first live consultation."
                : "Your past sessions will appear here once they have taken place."
            }
            action={
              <Button href="/consultants" size="sm">
                Browse consultants
              </Button>
            }
          />
        ) : (
          <>
            <ul className="space-y-3">
              {items.map((booking) => (
                <div
                  key={booking.id}
                  className={
                    booking.id === highlight
                      ? "rounded-3xl ring-2 ring-emerald-300 ring-offset-2 ring-offset-white"
                      : undefined
                  }
                >
                  <BookingRow booking={booking} onChanged={refresh} />
                </div>
              ))}
            </ul>
            {total > PAGE_SIZE && (
              <div className="mt-5 flex items-center justify-between gap-3">
                <p className="text-xs text-slate-500">
                  Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={offset === 0}
                    onClick={() => setOffset((v) => Math.max(0, v - PAGE_SIZE))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={!hasNext}
                    onClick={() => setOffset((v) => v + PAGE_SIZE)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Panel>
    </div>
  );
}
