// Confirmed-session meeting card for the seeker session hub (FR-BOOK-007).
import { useState } from "react";
import { Badge, Button, useToast } from "@/components/ui";
import { CalendarIcon, CheckIcon, ClockIcon, CopyIcon } from "@/components/icons";
import { countdownLabel, formatDuration, formatRange, googleCalendarUrl } from "@/lib/datetime";
import { useNow } from "@/hooks/useNow";

export default function MeetingCard({ booking }) {
  const toast = useToast();
  const now = useNow();
  // Stores the link that was copied; deriving `copied` from it means a new or
  // cleared link invalidates the confirmation without an effect.
  const [copiedLink, setCopiedLink] = useState("");

  const meetLink = booking.meet_link || "";
  const copied = meetLink !== "" && copiedLink === meetLink;
  const ended = now > new Date(booking.end_time).getTime();

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(meetLink);
      setCopiedLink(meetLink);
      toast.success("Meeting link copied", "Paste it anywhere to rejoin the session.");
    } catch {
      toast.error("Could not copy the link", "Please select and copy it manually.");
    }
  }

  return (
    <div className="mt-3 rounded-2xl border border-emerald-200/70 bg-emerald-50/50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
          Your session is confirmed
        </p>
        <Badge tone="emerald">{countdownLabel(booking, now)}</Badge>
      </div>

      <p className="mt-2 flex flex-wrap items-center gap-1.5 text-xs font-medium text-slate-700">
        <CalendarIcon className="h-3.5 w-3.5 text-slate-400" />
        {formatRange(booking.start_time, booking.end_time)}
        <span className="text-slate-300">·</span>
        <ClockIcon className="h-3.5 w-3.5 text-slate-400" />
        {formatDuration(booking.duration_minutes)}
      </p>

      {meetLink ? (
        <div className="mt-3 flex flex-col gap-2 rounded-xl border border-emerald-200/70 bg-white px-3.5 py-3 sm:flex-row sm:items-center sm:justify-between">
          <a
            href={meetLink}
            target="_blank"
            rel="noopener noreferrer"
            className="break-all text-sm font-semibold text-emerald-800 underline decoration-emerald-300 underline-offset-2 hover:text-emerald-900"
          >
            {meetLink}
          </a>
          <div className="shrink-0">
            <Button
              variant="secondary"
              size="sm"
              icon={copied ? CheckIcon : CopyIcon}
              onClick={copyLink}
            >
              {copied ? "Copied" : "Copy link"}
            </Button>
          </div>
        </div>
      ) : (
        <p className="mt-3 rounded-xl border border-emerald-200/70 bg-white px-3.5 py-2.5 text-xs leading-relaxed text-slate-600">
          {booking.consultant_name} hasn&apos;t shared the Google Meet link yet — it will appear
          here as soon as they do.
        </p>
      )}

      {!ended && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={CalendarIcon}
            href={googleCalendarUrl({
              title: `${booking.subject} — with ${booking.consultant_name}`,
              start: booking.start_time,
              end: booking.end_time,
              details: meetLink
                ? `Join on Google Meet: ${meetLink}`
                : `Live consultation with ${booking.consultant_name}`,
              location: meetLink || undefined,
            })}
            target="_blank"
            rel="noopener noreferrer"
          >
            Add to Google Calendar
          </Button>
        </div>
      )}

      {meetLink && (
        <p className="mt-2 text-xs text-emerald-800">
          The Join button up top unlocks 30 minutes before the session starts — the link above
          works any time.
        </p>
      )}
    </div>
  );
}
