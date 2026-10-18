// Two-way consultation thread between a seeker and responsible roles (FR-006).
import { useEffect, useRef, useState } from "react";
import { Button, InlineError, SkeletonRow } from "@/components/ui";
import {
  listConsultationMessages,
  postConsultationMessage,
} from "@/services/roles";
import { SendIcon } from "@/components/icons";

const ROLE_LABELS = {
  user: "Seeker",
  tarot_reader: "Tarot Reader",
  spiritual_consultant: "Spiritual Consultant",
  admin: "Administrator",
};

function MessageBubble({ message }) {
  const staff = message.is_staff;
  return (
    <div className={`flex ${staff ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed sm:max-w-[75%] ${
          staff
            ? "rounded-br-md border border-emerald-200/60 bg-emerald-50 text-emerald-900"
            : "rounded-bl-md border border-slate-200 bg-slate-50 text-slate-800"
        }`}
      >
        <p
          className={`mb-1 text-[10px] font-bold uppercase tracking-wide ${
            staff ? "text-emerald-700" : "text-slate-500"
          }`}
        >
          {message.sender_name || "Unknown"} ·{" "}
          {ROLE_LABELS[message.sender_role] || message.sender_role || "Seeker"}
        </p>
        <p className="whitespace-pre-wrap">{message.body}</p>
        <p className="mt-1 text-[10px] text-slate-500">
          {new Date(message.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}

export default function ConsultationThread({
  consultationId,
  onMessageSent,
  composeLabel = "Reply…",
}) {
  const [messages, setMessages] = useState(null);
  const [error, setError] = useState(null);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await listConsultationMessages(consultationId);
        if (!cancelled) {
          setMessages(result.items || []);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err?.message || "Failed to load conversation");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [consultationId]);

  useEffect(() => {
    if (messages?.length) {
      bottomRef.current?.scrollIntoView({ block: "nearest" });
    }
  }, [messages]);

  async function sendReply() {
    const body = reply.trim();
    if (!body) return;
    setSending(true);
    setError(null);
    try {
      await postConsultationMessage(consultationId, { body });
      setReply("");
      const result = await listConsultationMessages(consultationId);
      setMessages(result.items || []);
      onMessageSent?.();
    } catch (err) {
      setError(err?.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  }

  if (error && !messages) {
    return (
      <div className="space-y-2">
        <InlineError message={error} />
        <Button variant="ghost" size="sm" onClick={() => setMessages(null)}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-2xl border border-slate-200/80 bg-white/70 p-3.5">
      {messages === null ? (
        <SkeletonRow lines={3} />
      ) : messages.length === 0 ? (
        <p className="py-2 text-center text-xs text-slate-500">
          No messages yet — continue the conversation below.
        </p>
      ) : (
        <div className="max-h-80 space-y-2.5 overflow-y-auto pr-1">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      {error && messages && (
        <div className="mt-2">
          <InlineError message={error} />
        </div>
      )}

      <div className="mt-3 flex flex-col gap-2 sm:flex-row">
        <textarea
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendReply();
            }
          }}
          placeholder={composeLabel}
          rows={2}
          aria-label="Message"
          className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 transition placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        />
        <Button
          size="sm"
          variant="secondary"
          icon={SendIcon}
          loading={sending}
          disabled={sending || !reply.trim()}
          onClick={sendReply}
          className="shrink-0 self-end sm:self-center"
        >
          Send
        </Button>
      </div>
    </div>
  );
}
