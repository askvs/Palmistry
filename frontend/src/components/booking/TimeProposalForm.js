// TimeProposalForm — pick a date/time (and duration) to propose for a session.
import { useState } from "react";
import { Button, InlineError } from "@/components/ui";

const DURATIONS = [30, 45, 60, 90, 120];

function toLocalInputValue(date) {
  const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return d.toISOString().slice(0, 16);
}

export default function TimeProposalForm({
  mode = "propose",
  defaultDurationMinutes = 60,
  submitLabel,
  onSubmit,
  onCancel,
}) {
  // Default to the next round hour, at least ~1 day out so it clears lead time.
  const [when, setWhen] = useState(() => {
    const start = new Date();
    start.setDate(start.getDate() + 1);
    start.setMinutes(0, 0, 0);
    start.setHours(start.getHours() + 1);
    return toLocalInputValue(start);
  });
  const [duration, setDuration] = useState(defaultDurationMinutes || 60);
  const [subject, setSubject] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  // Pasted by the seeker for this particular request only — no default value.
  const [meetingLink, setMeetingLink] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    if (!when) {
      setError("Please choose a date and time.");
      return;
    }
    if (mode === "propose" && subject.trim().length < 3) {
      setError("Please add a short subject (at least 3 characters).");
      return;
    }
    const pastedLink = meetingLink.trim();
    if (mode === "propose" && pastedLink) {
      try {
        void new URL(pastedLink);
      } catch {
        setError("That meeting link doesn't look valid. Paste the full URL or leave it empty.");
        return;
      }
    }
    const startTime = new Date(when).toISOString();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        startTime,
        durationMinutes: Number(duration),
        subject: subject.trim(),
        notes: notes.trim() || undefined,
        message: message.trim() || undefined,
        meetingLink: pastedLink || undefined,
      });
    } catch (err) {
      setError(err?.message || "Something went wrong. Please try again.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Date &amp; time
          </span>
          <input
            type="datetime-local"
            value={when}
            onChange={(event) => setWhen(event.target.value)}
            className="mt-1.5 h-10 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-3.5 py-2 text-sm text-slate-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </label>
        <label className="block">
          <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Duration
          </span>
          <select
            value={duration}
            onChange={(event) => setDuration(event.target.value)}
            className="mt-1.5 h-10 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-3.5 py-2 text-sm text-slate-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          >
            {DURATIONS.map((value) => (
              <option key={value} value={value}>
                {value} minutes
              </option>
            ))}
          </select>
        </label>
      </div>

      {mode === "propose" ? (
        <>
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Subject
            </span>
            <input
              type="text"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              placeholder="What would you like to explore?"
              maxLength={200}
              className="mt-1.5 h-10 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-500 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Notes (optional)
            </span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
              maxLength={2000}
              className="mt-1.5 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Meeting link <span className="font-normal">(optional, for this request only)</span>
            </span>
            <input
              type="url"
              inputMode="url"
              value={meetingLink}
              onChange={(event) => setMeetingLink(event.target.value)}
              placeholder="Paste the meeting link for this session…"
              maxLength={500}
              className="mt-1.5 h-10 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-500 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </label>
        </>
      ) : (
        <label className="block">
          <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Message (optional)
          </span>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            rows={2}
            maxLength={2000}
            placeholder="Add a note about the new time…"
            className="mt-1.5 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </label>
      )}

      {error && <InlineError message={error} />}

      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" size="sm" disabled={busy}>
          {submitLabel || (mode === "propose" ? "Send request" : "Propose this time")}
        </Button>
      </div>
    </form>
  );
}
