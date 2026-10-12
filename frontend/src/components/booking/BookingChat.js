// BookingChat — a direct message thread between a seeker and the consultant for one booking.
import { useCallback, useEffect, useRef, useState } from "react";
import { Button, InlineError, Spinner } from "@/components/ui";
import { SendIcon } from "@/components/icons";
import { fetchBookingMessages, sendBookingMessage } from "@/services/booking";
import { formatDateTime } from "@/lib/datetime";

const POLL_MS = 15000;

export default function BookingChat({ bookingId, counterpartName = "the other participant", compact = false }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  const reload = useCallback(() => {
    if (!bookingId) return Promise.resolve();
    return fetchBookingMessages(bookingId)
      .then((data) => {
        setMessages(data?.items || []);
        setError(null);
      })
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
  }, [bookingId]);

  useEffect(() => {
    if (!bookingId) return undefined;
    // setState runs only in promise callbacks, matching useAsyncData.
    let cancelled = false;
    const run = () =>
      fetchBookingMessages(bookingId)
        .then((data) => {
          if (!cancelled) {
            setMessages(data?.items || []);
            setError(null);
          }
        })
        .catch((err) => {
          if (!cancelled) setError(err);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    run();
    const handle = setInterval(run, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(handle);
    };
  }, [bookingId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function submit(event) {
    event.preventDefault();
    const body = draft.trim();
    if (!body || sending) return;
    setSending(true);
    try {
      await sendBookingMessage(bookingId, body);
      setDraft("");
      await reload();
    } catch (err) {
      setError(err);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white">
      <div
        ref={scrollRef}
        className={`flex-1 space-y-3 overflow-y-auto p-4 ${compact ? "max-h-64" : "max-h-96"}`}
        aria-live="polite"
      >
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner label="Loading messages…" />
          </div>
        ) : error ? (
          <InlineError message="Could not load the conversation." />
        ) : messages.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-500">
            No messages yet. Say hello to {counterpartName}.
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex flex-col ${message.is_me ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm ${
                  message.is_me
                    ? "bg-primary-600 text-white"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                {message.body}
              </div>
              <span className="mt-1 text-[11px] text-slate-400">
                {message.is_me ? "You" : message.sender_name || "—"} ·{" "}
                {formatDateTime(message.created_at)}
              </span>
            </div>
          ))
        )}
      </div>

      <form onSubmit={submit} className="flex items-center gap-2 border-t border-slate-100 p-3">
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Write a message…"
          maxLength={4000}
          className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
        />
        <Button type="submit" size="sm" icon={SendIcon} disabled={sending || !draft.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
