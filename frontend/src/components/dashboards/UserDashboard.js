// User role dashboard: readings, insights, guidance (FR-002, FR-003, FR-006).
import { useEffect, useState } from "react";
import Link from "next/link";
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
import { StatCard, ReadingTimeline, Segmented } from "@/components/dashboards/shared";
import PersonalityInsightsCard from "@/components/dashboards/PersonalityInsightsCard";
import ConsultationThread from "@/components/dashboards/ConsultationThread";
import { useAsyncData } from "@/hooks/useAsyncData";
import { fetchUserDashboard, requestConsultation } from "@/services/roles";
import { listMyRecommendations } from "@/services/recommendations";
import { useAuth } from "@/hooks/useAuth";
import {
  BrainIcon,
  CardsIcon,
  ChatIcon,
  FileTextIcon,
  HandIcon,
  SendIcon,
  SparkleIcon,
  UserIcon,
} from "@/components/icons";

// Kit badge tones per reading type.
const TYPE_TONES = { palm: "primary", tarot: "accent" };

// Starter form: a seeker's first question opens a consultation thread that a responsible role (tarot reader, spiritual.
function AskConsultantForm({ onCreated }) {
  const toast = useToast();
  const [topic, setTopic] = useState("");
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    if (!topic.trim() || !question.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      await requestConsultation({ topic: topic.trim(), message: question.trim() });
      toast.success("Question sent", "A verified reader or consultant will reply in your conversation thread.");
      setTopic("");
      setQuestion("");
      onCreated?.();
    } catch (err) {
      setError(err?.message || "Failed to send your question");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mb-5 rounded-2xl border border-slate-200 bg-white/70 p-4">
      <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        Ask a new question
      </p>
      <div className="space-y-2.5">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Topic (e.g. Career path, Relationship clarity)"
          aria-label="Question topic"
          maxLength={200}
          className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        />
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What would you like guidance on? Share as much context as you like…"
          aria-label="Your question"
          rows={3}
          className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        />
      </div>
      {error && (
        <div className="mt-2.5">
          <InlineError message={error} />
        </div>
      )}
      <div className="mt-3 flex justify-end">
        <Button
          type="submit"
          size="sm"
          variant="primary"
          icon={SendIcon}
          loading={busy}
          disabled={busy || !topic.trim() || !question.trim()}
        >
          Send question
        </Button>
      </div>
    </form>
  );
}

// One consultation with an expandable two-way conversation thread.
function ConsultationCard({ consultation, onReply }) {  const [open, setOpen] = useState(false);
  const c = consultation;
  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-800">{c.topic}</p>
        <Badge tone={c.guidance ? "emerald" : "accent"}>{c.status}</Badge>
      </div>
      <p className="mt-1 text-xs text-slate-600">{c.message}</p>
      {c.guidance && (
        <p className="mt-2.5 rounded-xl border border-emerald-200/60 bg-emerald-50 px-3.5 py-2 text-xs leading-relaxed text-emerald-800">
          <span className="font-bold">Consultant note: </span>
          {c.guidance}
        </p>
      )}
      <div className="mt-2.5">
        <Button variant="ghost" size="sm" onClick={() => setOpen((v) => !v)}>
          {open ? "Hide conversation" : "Open conversation"}
        </Button>
      </div>
      {open && (
        <ConsultationThread
          consultationId={c.id}
          composeLabel="Ask a follow-up question…"
          onMessageSent={onReply}
        />
      )}
    </li>
  );
}

// Recommendation catalog tones (mirrors RecommendationCard).
const REC_TYPE_TONES = {
  personal_growth: "primary",
  relationship: "rose",
  career: "blue",
  goal_alignment: "emerald",
  spiritual_development: "accent",
};

export default function UserDashboard() {
  const { user } = useAuth();
  const { data, error, loading, refresh } = useAsyncData(fetchUserDashboard);
  const [recs, setRecs] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [recsError, setRecsError] = useState(null);

  const [historyView, setHistoryView] = useState("timeline"); // 'timeline' | 'list'

  useEffect(() => {
    if (!user) {
      return undefined;
    }
    (async () => {
      setRecsLoading(true);
      try {
        const result = await listMyRecommendations({ limit: 5 });
        setRecs(result.items || []);
        setRecsError(null);
      } catch (err) {
        setRecsError(err?.message || "Failed to load recommendations");
      } finally {
        setRecsLoading(false);
      }
    })();
  }, [user]);

  const readings = data?.readings;
  const analytics = data?.analytics;
  const consultations = data?.consultations;
  const latestReading = readings?.items?.[0];

  async function retryRecommendations() {
    setRecsLoading(true);
    setRecsError(null);
    try {
      const result = await listMyRecommendations({ limit: 5 });
      setRecs(result.items || []);
    } catch (e) {
      setRecsError(e?.message || "Failed to load recommendations");
    } finally {
      setRecsLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {error && <ErrorState message={error.message} onRetry={refresh} />}

      {/* Secondary quick actions (the palm + tarot CTAs live in the. */}
      <div className="flex flex-wrap items-center gap-3">
        <Button href="/readings" variant="secondary" icon={FileTextIcon}>
          Reading archives
        </Button>
        <Button href="/personality" variant="ghost" icon={BrainIcon}>
          Personality insight
        </Button>
      </div>

      {/* Featured latest reading highlight */}
      {latestReading && (
        <Panel
          title="Latest divination insight"
          subtitle={new Date(latestReading.created_at).toLocaleDateString(undefined, {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          action={
            <Button
              href={`/readings/${latestReading.id}`}
              variant="secondary"
              size="sm"
              iconRight={SparkleIcon}
            >
              Open the full dossier
            </Button>
          }
        >
          <h3 className="font-display text-xl font-medium tracking-tight text-slate-900">
            {latestReading.title}
          </h3>
          <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-slate-600">
            {latestReading.summary}
          </p>
        </Panel>
      )}

      {/* Analytics stat cards */}
      <div className="grid gap-5 sm:grid-cols-3">
        <StatCard
          label="Total Readings"
          value={analytics ? analytics.total : loading ? "—" : 0}
          tone="primary"
          icon={SparkleIcon}
          hint="Across palmistry and tarot"
        />
        <StatCard
          label="Palm Scans"
          value={analytics ? (analytics.by_type.find((r) => r.type === "palm")?.count ?? 0) : loading ? "—" : 0}
          tone="blue"
          icon={HandIcon}
          hint="Chirognomy & dermatoglyphics"
        />
        <StatCard
          label="Tarot Readings"
          value={analytics ? (analytics.by_type.find((r) => r.type === "tarot")?.count ?? 0) : loading ? "—" : 0}
          tone="accent"
          icon={CardsIcon}
          hint="Major & minor arcana spreads"
        />
      </div>

      {/* Personality insights summary (FR-035) — computed from the. */}
      <Panel
        title="Personality Insights"
        subtitle="Strengths, growth areas, and behavioral patterns from your readings"
      >
        <PersonalityInsightsCard
          readingsLoading={loading}
          palmReadingId={
            readings?.items?.find((r) => r.type === "palm" && r.status === "completed")?.id
          }
          tarotReadingId={
            readings?.items?.find((r) => r.type === "tarot" && r.status === "completed")?.id
          }
        />
      </Panel>

      {/* Reading history with view toggle */}
      <Panel
        title="Reading History & Sacred Archives"
        subtitle="Chronological timeline of all your divinations and insights"
        action={
          <div className="flex items-center gap-3">
            <Segmented
              label="Reading history view"
              value={historyView}
              onChange={setHistoryView}
              options={[
                { value: "timeline", label: "Timeline" },
                { value: "list", label: "List" },
              ]}
            />
            {readings && readings.items.length > 0 && (
              <Button href="/readings" variant="ghost" size="sm">
                All archives
              </Button>
            )}
          </div>
        }
      >
        {loading ? (
          <div className="space-y-3 py-2">
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
          </div>
        ) : !readings || readings.items.length === 0 ? (
          <EmptyState
            icon={SparkleIcon}
            title="No readings yet"
            description="Your timeline fills in after your first tarot ritual or palm scan."
          />
        ) : historyView === "timeline" ? (
          <div className="py-2">
            <ReadingTimeline readings={readings.items.slice(0, 8)} />
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {readings.items.slice(0, 8).map((reading) => (
              <li key={reading.id}>
                <Link
                  href={`/readings/${reading.id}`}
                  className="-mx-2 flex items-center justify-between gap-4 rounded-xl px-3 py-3.5 transition group hover:bg-slate-50/80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-800 transition group-hover:text-primary-700">
                      {reading.title}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {new Date(reading.created_at).toLocaleString()} · {reading.summary}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge tone={TYPE_TONES[reading.type] || "slate"}>{reading.type}</Badge>
                    <Badge tone={reading.status === "completed" ? "emerald" : "accent"}>
                      {reading.status}
                    </Badge>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {/* Recent recommendations */}
      {recsError ? (
        <Panel title="Recent Recommendations" subtitle="Personalized guidance">
          <div className="space-y-3">
            <InlineError message={recsError} />
            <Button
              variant="secondary"
              size="sm"
              loading={recsLoading}
              onClick={retryRecommendations}
            >
              Retry
            </Button>
          </div>
        </Panel>
      ) : (
        <Panel
          title="Recent Recommendations"
          subtitle="Personalized guidance based on your readings and profile"
        >
          {recsLoading ? (
            <div className="py-2">
              <SkeletonRow lines={3} />
            </div>
          ) : !user ? (
            <EmptyState
              icon={UserIcon}
              title="Sign in required"
              description="Sign in to see personalized recommendations."
            />
          ) : recs.length === 0 ? (
            <EmptyState
              icon={SparkleIcon}
              title="No recommendations yet"
              description="Complete a palm or tarot reading to get started."
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {recs.slice(0, 4).map((rec) => (
                <div
                  key={rec.id}
                  className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4"
                >
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <Badge tone={REC_TYPE_TONES[rec.rec_type] || "primary"}>
                      {rec.rec_type.replace(/_/g, " ")}
                    </Badge>
                    <span className="text-xs font-semibold text-slate-600">
                      {Math.round((rec.score || 0) * 100)}%
                    </span>
                  </div>
                  <h4 className="mb-1 text-sm font-semibold text-slate-900">{rec.title}</h4>
                  <p className="line-clamp-2 text-xs text-slate-600">{rec.text}</p>
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}

      {/* Consultations / guidance */}
      <Panel
        title="Spiritual Guidance Received"
        subtitle="Direct counsel from verified readers and spiritual consultants"
      >
        <AskConsultantForm onCreated={refresh} />
        {loading ? (
          <div className="py-2">
            <SkeletonRow lines={3} />
          </div>
        ) : !consultations || consultations.items.length === 0 ? (
          <EmptyState
            icon={ChatIcon}
            title="No conversations yet"
            description="Ask your first question above — a reader or consultant will reply in your conversation thread."
          />
        ) : (
          <ul className="space-y-3">
            {consultations.items.slice(0, 5).map((c) => (
              <ConsultationCard key={c.id} consultation={c} onReply={refresh} />
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
