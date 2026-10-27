// Consultant "Live Consultation" inbox: new requests plus every post-accept
// tool (Meet link, chat, notes, completion) on one card.
import { useCallback, useMemo, useState } from "react";
import Seo from "@/components/Seo";
import {
  Badge,
  Button,
  ConfirmDialog,
  ErrorState,
  InlineError,
  PageHeader,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import {
  CalendarIcon,
  ChatIcon,
  CheckCircleIcon,
  ClockIcon,
  CompassIcon,
  FileTextIcon,
  TrashIcon,
  VideoIcon,
} from "@/components/icons";
import {
  BookingStatusBadge,
  EmptyRow,
  MeetingLinkEditor,
} from "@/components/booking/shared";
import BookingChat from "@/components/booking/BookingChat";
import TimeProposalForm from "@/components/booking/TimeProposalForm";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import {
  acceptBooking,
  addSessionNote,
  cancelConsultantBooking,
  completeBooking,
  counterBookingAsConsultant,
  deleteSessionNote,
  fetchBookingNotes,
  fetchConsultantSessions,
  rejectBooking,
  updateSessionNote,
} from "@/services/booking";
import {
  canJoinMeet,
  formatDateTime,
  formatDuration,
  formatRange,
  relativeFromNow,
} from "@/lib/datetime";

// One incoming request: accept, decline, propose another time, chat.
function RequestCard({ booking, busyId, onAct, onCounter }) {
  const [showChat, setShowChat] = useState(false);
  const [showCounter, setShowCounter] = useState(false);
  const awaitingSeeker = booking.status === "countered";

  async function counter(payload) {
    const sent = await onCounter(booking, payload);
    if (sent) setShowCounter(false);
  }

  return (
    <li
      className={`rounded-[16px] p-4 ring-1 ${
        awaitingSeeker
          ? "bg-accent-400/[0.06] ring-accent-400/25"
          : "bg-white/[0.04] ring-white/[0.08]"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-[#ede9fe]">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-[13.5px] text-[#a79fc6]">
            <span className="font-semibold text-[#ede9fe]">{booking.seeker_name}</span>
            {booking.seeker_email ? ` · ${booking.seeker_email}` : ""}
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[12.5px] tabular-nums text-[#a79fc6]">
            <CalendarIcon className="h-3.5 w-3.5" />
            {formatRange(booking.start_time, booking.end_time)}
            <span className="text-white/25">·</span>
            {formatDuration(booking.duration_minutes)}
          </p>
          {awaitingSeeker && (
            <p className="mt-1.5 text-[12.5px] font-medium text-accent-300">
              You proposed this time — waiting for {booking.seeker_name} to confirm.
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {!awaitingSeeker && (
            <Button
              variant="accent"
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
            className="border-white/15 bg-white/5 text-violet-300 hover:border-white/25 hover:bg-white/10 active:bg-white/15"
            icon={ClockIcon}
            disabled={busyId !== null}
            onClick={() => setShowCounter((value) => !value)}
          >
            {showCounter ? "Close" : "Propose time"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-violet-300 hover:bg-white/10 hover:text-white active:bg-white/10"
            icon={ChatIcon}
            onClick={() => setShowChat((value) => !value)}
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
        <p className="mt-3 rounded-[10px] bg-white/[0.05] px-3.5 py-2.5 text-sm leading-relaxed text-[#a79fc6] ring-1 ring-white/[0.06]">
          <span className="font-bold text-[#ede9fe]">Seeker notes: </span>
          {booking.notes}
        </p>
      )}

      {booking.meet_link && (
        <p className="mt-3 rounded-[10px] bg-white/[0.05] px-3.5 py-2.5 text-sm leading-relaxed text-[#a79fc6] ring-1 ring-white/[0.06]">
          <span className="font-bold text-[#ede9fe]">Seeker&apos;s meeting link: </span>
          <a
            href={booking.meet_link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-violet-300 underline underline-offset-2 hover:text-white"
          >
            {booking.meet_link}
          </a>
        </p>
      )}

      {showCounter && (
        <div className="mt-3 rounded-[16px] bg-white/[0.05] p-3.5 ring-1 ring-white/[0.08]">
          <p className="mb-2 text-[12.5px] font-semibold text-[#a79fc6]">
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

// Private/shared notes for one confirmed session, loaded only when opened.
function SessionNotes({ bookingId }) {
  const toast = useToast();
  // Stable loader: useAsyncData re-runs whenever the loader identity changes.
  const loader = useCallback(() => fetchBookingNotes(bookingId), [bookingId]);
  const { data, error, loading, refresh } = useAsyncData(loader);
  const notes = useMemo(() => data || [], [data]);
  const [body, setBody] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState(null);
  const [editingId, setEditingId] = useState(null);

  async function submit(event) {
    event.preventDefault();
    if (!body.trim() || busy) return;
    setBusy(true);
    setFormError(null);
    try {
      if (editingId) {
        await updateSessionNote(editingId, { body: body.trim(), visibility });
      } else {
        await addSessionNote(bookingId, { body: body.trim(), visibility });
      }
      setBody("");
      setVisibility("private");
      setEditingId(null);
      toast.success("Note saved");
      refresh();
    } catch (err) {
      setFormError(err?.message || "Could not save this note");
    } finally {
      setBusy(false);
    }
  }

  async function remove(noteId) {
    setBusy(true);
    try {
      await deleteSessionNote(noteId);
      toast.success("Note removed");
      refresh();
    } catch (err) {
      toast.error("Could not remove the note", err?.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[16px] bg-white/[0.05] p-3.5 ring-1 ring-white/[0.08]">
      <p className="text-xs font-bold uppercase tracking-wide text-[#a79fc6]">Session notes</p>
      <p className="mt-1 text-[12.5px] leading-relaxed text-[#a79fc6]">
        Keep private notes for yourself, or share a note with the seeker.
      </p>

      {loading ? (
        <div className="mt-3">
          <SkeletonRow lines={2} />
        </div>
      ) : error ? (
        <div className="mt-3">
          <ErrorState message={error.message} onRetry={refresh} />
        </div>
      ) : (
        <ul className="mt-3 space-y-2">
          {notes.length === 0 ? (
            <li className="text-[12.5px] text-[#a79fc6]">No notes on this session yet.</li>
          ) : (
            notes.map((note) => (
              <li
                key={note.id}
                className="rounded-[10px] bg-white/[0.04] px-4 py-3 ring-1 ring-white/[0.06]"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="min-w-0 text-sm leading-relaxed text-[#ede9fe]">{note.body}</p>
                  <Badge tone={note.visibility === "shared" ? "emerald" : "slate"}>
                    {note.visibility === "shared" ? "Shared" : "Private"}
                  </Badge>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="text-[12.5px] tabular-nums text-[#a79fc6]">
                    {note.author_name} · {formatDateTime(note.created_at)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-violet-300 hover:bg-white/10 hover:text-white active:bg-white/10"
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
      )}

      <form onSubmit={submit} className="mt-3 space-y-2.5 border-t border-white/10 pt-3">
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          rows={3}
          maxLength={4000}
          placeholder="What did you notice in this session? Symbols, themes, follow-ups…"
          className="w-full rounded-[10px] border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-[#ede9fe] placeholder:text-[#a79fc6] focus:border-violet-400/70 focus:ring-2 focus:ring-violet-500/25 focus:outline-none"
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-[12.5px] text-[#c4b5fd]">
            <input
              type="checkbox"
              checked={visibility === "shared"}
              onChange={(event) => setVisibility(event.target.checked ? "shared" : "private")}
              className="h-4 w-4 rounded border-white/20 accent-primary-600 focus:ring-primary-500"
            />
            Share this note with the seeker
          </label>
          <Button variant="accent" type="submit" size="sm" loading={busy} disabled={busy || !body.trim()}>
            {editingId ? "Update note" : "Add note"}
          </Button>
        </div>
        {formError && <InlineError message={formError} />}
      </form>
    </div>
  );
}

// One confirmed session: everything after acceptance lives on this card.
function ConfirmedCard({ booking, onChanged }) {
  const toast = useToast();
  const [showChat, setShowChat] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [busy, setBusy] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const joinable = canJoinMeet(booking);

  async function complete() {
    setBusy(true);
    try {
      await completeBooking(booking.id, { force: true });
      toast.success("Session completed", "The seeker can now leave feedback.");
      onChanged?.();
    } catch (err) {
      toast.error("Could not complete this session", err?.message);
    } finally {
      setBusy(false);
    }
  }

  async function cancelSession() {
    setBusy(true);
    try {
      await cancelConsultantBooking(booking.id);
      toast.success("Session cancelled", "The seeker has been notified.");
      onChanged?.();
    } catch (err) {
      toast.error("Could not cancel this session", err?.message);
    } finally {
      setBusy(false);
      setCancelling(false);
    }
  }

  return (
    <li className="rounded-[16px] bg-white/[0.04] p-4 ring-1 ring-white/[0.08]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-[#ede9fe]">{booking.subject}</h4>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-[13.5px] text-[#a79fc6]">
            with <span className="font-semibold text-[#ede9fe]">{booking.seeker_name}</span>
            {booking.seeker_email ? ` · ${booking.seeker_email}` : ""}
          </p>
          <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[12.5px] tabular-nums text-[#a79fc6]">
            <CalendarIcon className="h-3.5 w-3.5" />
            {formatRange(booking.start_time, booking.end_time)}
            <span className="text-white/25">·</span>
            {formatDuration(booking.duration_minutes)}
            <span className="text-white/25">·</span>
            {relativeFromNow(booking.start_time)}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {joinable ? (
            <Button
              variant="accent"
              href={booking.meet_link}
              target="_blank"
              rel="noopener noreferrer"
              size="sm"
              icon={VideoIcon}
            >
              Join Google Meet
            </Button>
          ) : (
            booking.meet_link && (
              <span className="inline-flex items-center rounded-full bg-white/5 px-2.5 py-[3px] text-[11px] font-semibold text-[#a79fc6] ring-1 ring-white/10">
                Opens 30 min before
              </span>
            )
          )}
          <Button
            variant="ghost"
            size="sm"
            className="text-violet-300 hover:bg-white/10 hover:text-white active:bg-white/10"
            icon={ChatIcon}
            onClick={() => setShowChat((value) => !value)}
          >
            {showChat ? "Hide chat" : "Chat"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-violet-300 hover:bg-white/10 hover:text-white active:bg-white/10"
            icon={FileTextIcon}
            onClick={() => setShowNotes((value) => !value)}
          >
            {showNotes ? "Hide notes" : "Notes"}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            className="border-white/15 bg-white/5 text-violet-300 hover:border-white/25 hover:bg-white/10 active:bg-white/15"
            loading={busy}
            disabled={busy}
            onClick={complete}
          >
            Mark complete
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
        </div>
      </div>

      <div className="mt-3">
        <MeetingLinkEditor booking={booking} onSaved={onChanged} />
      </div>

      {booking.notes && (
        <p className="mt-3 rounded-[10px] bg-white/[0.05] px-3.5 py-2.5 text-sm leading-relaxed text-[#a79fc6] ring-1 ring-white/[0.06]">
          <span className="font-bold text-[#ede9fe]">Seeker notes: </span>
          {booking.notes}
        </p>
      )}

      {showChat && (
        <div className="mt-3">
          <BookingChat bookingId={booking.id} counterpartName={booking.seeker_name} compact />
        </div>
      )}

      {showNotes && (
        <div className="mt-3">
          <SessionNotes bookingId={booking.id} />
        </div>
      )}

      <ConfirmDialog
        open={cancelling}
        title="Cancel this session?"
        message={`"${booking.subject}" with ${booking.seeker_name} will be cancelled and the
          seeker notified.`}
        confirmLabel="Yes, cancel"
        tone="danger"
        loading={busy}
        onConfirm={cancelSession}
        onCancel={() => setCancelling(false)}
      />
    </li>
  );
}

// Requests board: pending/countered requests above, confirmed sessions below.
function RequestsBoard() {
  const toast = useToast();
  // Stable loader: useAsyncData re-runs whenever the loader identity changes.
  const loader = useCallback(() => fetchConsultantSessions({ limit: 100 }), []);
  const { data, error, loading, refresh } = useAsyncData(loader);
  const [busyId, setBusyId] = useState(null);

  const requests = useMemo(() => data?.requests?.items || [], [data]);
  const confirmed = useMemo(() => data?.upcoming?.items || [], [data]);

  async function act(booking, action) {
    setBusyId(booking.id);
    try {
      if (action === "accept") {
        await acceptBooking(booking.id);
        toast.success("Session confirmed", "Add your Google Meet link so the seeker can join.");
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

  // Returns whether the proposal was sent, so the form only closes on success.
  async function counter(booking, { startTime, durationMinutes, message }) {
    try {
      await counterBookingAsConsultant(booking.id, { startTime, durationMinutes, message });
      toast.success("New time proposed", "The seeker has been asked to confirm it.");
      refresh();
      return true;
    } catch (err) {
      toast.error("Could not propose a new time", err?.message);
      return false;
    }
  }

  return (
    <div>
      <div className="border-b border-white/10 pb-4">
        <h2 className="text-[15px] font-semibold tracking-tight text-[#ede9fe]">
          Live Consultation Requests
        </h2>
        <p className="mt-0.5 text-[12.5px] text-[#a79fc6]">
          Accept new requests here — once confirmed, every tool to run the session stays on the
          same card.
        </p>
      </div>

      {loading ? (
        <div className="mt-6 space-y-3 py-2">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : error ? (
        <ErrorState className="mt-6" message={error.message} onRetry={refresh} />
      ) : (
        <div className="mt-6 space-y-6">
          <section>
            <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-[#a79fc6]">
              New requests {requests.length > 0 && `(${requests.length})`}
            </p>
            {requests.length === 0 ? (
              <EmptyRow>No new requests right now — you&apos;re all caught up.</EmptyRow>
            ) : (
              <ul className="space-y-3">
                {requests.map((booking) => (
                  <RequestCard
                    key={booking.id}
                    booking={booking}
                    busyId={busyId}
                    onAct={act}
                    onCounter={counter}
                  />
                ))}
              </ul>
            )}
          </section>

          <section>
            <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-[#a79fc6]">
              Confirmed sessions {confirmed.length > 0 && `(${confirmed.length})`}
            </p>
            {confirmed.length === 0 ? (
              <EmptyRow>
                No confirmed sessions yet — accepted requests appear here with their Meet link,
                chat and notes.
              </EmptyRow>
            ) : (
              <ul className="space-y-3">
                {confirmed.map((booking) => (
                  <ConfirmedCard key={booking.id} booking={booking} onChanged={refresh} />
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default function LiveConsultationPage() {
  const { user, loading: authLoading } = useAuth();
  // Consultant-only page: everyone else is redirected to their dashboard.
  const blocked = useRoleGuard();

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
          eyebrow="Live consultation"
          title="Sign in required"
          description="Sign in with a consultant account to manage your consultation requests."
          actions={
            <Button href="/login?redirect=/live-consultation">Sign in</Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-8">
      <Seo
        title="Live consultation"
        description="Manage live session requests, meeting links, and notes in one room."
      />
      <PageHeader
        icon={CompassIcon}
        tileTone="emerald"
        eyebrow="Live consultations"
        title="Live Consultation"
        description="Your consultation inbox: accept or decline requests, then run every confirmed
          session from one card — share the Google Meet link, chat with the seeker, keep notes
          and mark it complete."
        gradient="gold"
      />

      {user && (
        <section className="rounded-[20px] bg-gradient-to-b from-[#1e1836] to-[#0f0c29] p-6 sm:p-8 ring-1 ring-white/10 text-[#ede9fe]">
          <RequestsBoard />
        </section>
      )}
    </div>
  );
}
