// Dashboard AI Assistant — an "overall analysis" chatbot for every role.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Badge, Button, InlineError, Panel, SkeletonRow, Spinner } from "@/components/ui";
import { useAsyncData } from "@/hooks/useAsyncData";
import { roleMeta } from "@/lib/roles";
import { askAssistant, fetchAssistantContext } from "@/services/assistant";
import {
  BrainIcon,
  ChatIcon,
  CloseIcon,
  RetryIcon,
  SendIcon,
  SparkleIcon,
} from "@/components/icons";

const MAX_INPUT = 2000;

// One chat turn.
function Message({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "rounded-br-md bg-primary-600 text-white"
            : "rounded-bl-md border border-slate-200/80 bg-white text-slate-700"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

function MetricChips({ metrics = [] }) {
  if (metrics.length === 0) return null;
  return (
    <dl className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="rounded-2xl border border-slate-100 bg-slate-50/60 px-3.5 py-2.5"
        >
          <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            {metric.label}
          </dt>
          <dd className="mt-0.5 text-lg font-bold tracking-tight text-slate-900">
            {metric.value}
          </dd>
          {metric.hint && <dd className="text-[11px] text-slate-500">{metric.hint}</dd>}
        </div>
      ))}
    </dl>
  );
}

function HighlightList({ highlights = [] }) {
  if (highlights.length === 0) return null;
  return (
    <ul className="space-y-2">
      {highlights.map((item) => (
        <li key={item.label} className="flex items-start gap-2.5 text-sm">
          <SparkleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent-500" />
          <span className="text-slate-600">
            <span className="font-semibold text-slate-800">{item.label}: </span>
            {item.detail}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function DashboardAssistant({ role }) {
  const { data: context, error: contextError, loading: contextLoading, refresh } =
    useAsyncData(fetchAssistantContext);
  const roleLabel = context?.role_label || roleMeta(role).label;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatError, setChatError] = useState(null);
  const threadRef = useRef(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  const send = useCallback(
    async (text, intent = "question") => {
      const question = (text ?? "").trim();
      if (!question || busy) return;

      setMessages((prev) => [...prev, { role: "user", content: question }]);
      setInput("");
      setBusy(true);
      setChatError(null);

      try {
        const reply = await askAssistant(question, { intent, history: messages });
        setMessages(
          reply.conversation_history.map((m) => ({ role: m.role, content: m.content }))
        );
      } catch (err) {
        setChatError(err?.message || "The assistant could not answer right now.");
        // Drop the unanswered turn so the transcript stays a clean Q&A.
        setMessages((prev) => prev.filter((m) => m.content !== question));
        setInput(question);
      } finally {
        setBusy(false);
      }
    },
    [busy, messages]
  );

  const runOverview = useCallback(() => {
    send("Give me an overall analysis of my dashboard.", "overview");
  }, [send]);

  function handleSubmit(event) {
    event.preventDefault();
    send(input);
  }

  const suggested = useMemo(() => context?.suggested_questions ?? [], [context]);
  const hasMessages = messages.length > 0;

  return (
    <Panel
      title="AI Assistant · overall analysis"
      subtitle={
        context
          ? `Grounded in ${context.scope} — ask anything, or generate the full analysis.`
          : "Loading your role-scoped data snapshot…"
      }
      action={
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="primary">{roleLabel}</Badge>
          {hasMessages && (
            <Button
              variant="ghost"
              size="sm"
              icon={CloseIcon}
              onClick={() => {
                setMessages([]);
                setChatError(null);
              }}
            >
              Clear
            </Button>
          )}
          <Button
            variant="accent"
            size="sm"
            icon={SparkleIcon}
            loading={busy}
            disabled={busy || contextLoading}
            onClick={runOverview}
          >
            Overall analysis
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {contextError && (
          <div className="space-y-3">
            <InlineError message={`Could not load your data snapshot: ${contextError.message}`} />
            <Button variant="secondary" size="sm" icon={RetryIcon} onClick={refresh}>
              Retry
            </Button>
          </div>
        )}

        {contextLoading && <SkeletonRow lines={4} />}

        {/* What the assistant can see — the grounding for every answer */}
        {context && (
          <div className="space-y-4 rounded-2xl border border-primary-100 bg-primary-50/40 p-4 sm:p-5">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-600 to-fuchsia-500 text-white shadow-md shadow-primary-500/30">
                <BrainIcon className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-slate-900">{context.headline}</h3>
                <p className="mt-0.5 text-xs leading-relaxed text-slate-500">
                  Live figures from your {roleLabel.toLowerCase()} workspace. Answers are built
                  from these numbers only — nothing is invented.
                </p>
              </div>
            </div>
            <MetricChips metrics={context.metrics} />
            <HighlightList highlights={context.highlights} />
          </div>
        )}

        {/* Conversation thread */}
        <div
          ref={threadRef}
          className="max-h-96 space-y-3 overflow-y-auto rounded-2xl border border-slate-100 bg-slate-50/60 p-4"
          aria-live="polite"
        >
          {!hasMessages && !busy && (
            <div className="space-y-3">
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-slate-200/80 bg-white px-3.5 py-2.5 text-sm leading-relaxed text-slate-700">
                  I can see your whole workspace, not a single reading. Ask about patterns,
                  trends, or what deserves attention first — or run the overall analysis above.
                </div>
              </div>
              {suggested.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {suggested.map((question) => (
                    <button
                      key={question}
                      type="button"
                      disabled={busy}
                      onClick={() => send(question)}
                      className="cursor-pointer rounded-full border border-primary-200 bg-white px-3 py-1.5 text-xs font-medium text-primary-700 transition hover:border-primary-300 hover:bg-primary-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:pointer-events-none disabled:opacity-50"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((message, index) => (
            <Message key={`${message.role}-${index}`} message={message} />
          ))}

          {busy && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2.5 rounded-2xl rounded-bl-md border border-slate-200/80 bg-white px-3.5 py-2.5">
                <Spinner className="h-4 w-4" />
                <span className="text-xs text-slate-500">Analysing your workspace…</span>
              </div>
            </div>
          )}
        </div>

        {chatError && <InlineError message={chatError} />}

        <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="assistant-question">
            Ask the AI assistant about your dashboard
          </label>
          <input
            id="assistant-question"
            type="text"
            value={input}
            maxLength={MAX_INPUT}
            disabled={busy}
            onChange={(event) => setInput(event.target.value)}
            placeholder={`Ask about your ${roleLabel.toLowerCase()} data…`}
            className="h-10 flex-1 rounded-full border border-slate-200 bg-slate-50 px-4 text-sm text-slate-800 placeholder-slate-400 transition focus:border-primary-300 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-primary-600 disabled:opacity-50"
          />
          <Button
            type="submit"
            icon={SendIcon}
            loading={busy}
            disabled={busy || !input.trim()}
          >
            Ask
          </Button>
        </form>

        {context?.disclaimer && (
          <p className="flex items-start gap-2 border-t border-slate-100 pt-3 text-[11px] italic leading-relaxed text-slate-500">
            <ChatIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {context.disclaimer}
          </p>
        )}
      </div>
    </Panel>
  );
}
