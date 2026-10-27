// Spiritual Consultant dashboard: triage, effectiveness, trends, guidance (FR-006).
import { useState } from "react";
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
import {
  CONSULTATION_STATUS_LABELS,
  MeterBar,
  PerDayBars,
  PersonalPracticeRow,
  Segmented,
  StatCard,
  formatDuration,
} from "@/components/dashboards/shared";
import ConsultationThread from "@/components/dashboards/ConsultationThread";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  consultantProvideGuidance,
  fetchConsultantDashboard,
} from "@/services/roles";
import {
  ChartIcon,
  ChatIcon,
  ClockIcon,
  SearchIcon,
  SendIcon,
  UsersIcon,
  TargetIcon,
} from "@/components/icons";

// Queue status filter values map 1:1 onto ConsultationStatus.
const STATUS_FILTERS = ["all", "open", "in_review", "resolved"];

const STATUS_LABELS = CONSULTATION_STATUS_LABELS;

export default function ConsultantDashboard() {
  const { data, error, loading, refresh } = useAsyncData(fetchConsultantDashboard);
  const toast = useToast();
  const queue = data?.queue;
  const trends = data?.trends;
  const effectiveness = data?.effectiveness;
  const insights = data?.insights;
  const [guidanceText, setGuidanceText] = useState({});
  const [openThreads, setOpenThreads] = useState({});
  const [busyId, setBusyId] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [queueFilter, setQueueFilter] = useState("all");
  const [queueSearch, setQueueSearch] = useState("");

  async function sendGuidance(consultation) {
    const guidance = guidanceText[consultation.id]?.trim();
    if (!guidance) return;
    setBusyId(consultation.id);
    setActionError(null);
    try {
      await consultantProvideGuidance(consultation.id, { guidance });
      toast.success("Counsel dispatched", `Your guidance for "${consultation.topic}" has been sent.`);
      setGuidanceText((prev) => ({ ...prev, [consultation.id]: "" }));
      await refresh();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  const queueItems = queue?.items || [];
  const statusCounts = queueItems.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1;
    return acc;
  }, {});
  const filteredQueue = queueItems.filter((c) => {
    if (queueFilter !== "all" && c.status !== queueFilter) return false;
    const q = queueSearch.trim().toLowerCase();
    if (q && !c.topic.toLowerCase().includes(q)) return false;
    return true;
  });

  const statusRows = ["open", "in_review", "resolved"].map((status) => ({
    status,
    count: statusCounts[status] || 0,
  }));
  const queueTotal = queueItems.length;

  return (
    <div className="space-y-8">
      {error && <ErrorState message={error.message} onRetry={refresh} />}
      {actionError && <InlineError message={actionError} />}

      {/* Triage stat grid */}
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Inquiry Requests"
          value={insights ? insights.total_requests : loading ? "—" : 0}
          tone="emerald"
          icon={ChatIcon}
          hint="All seeker submissions"
        />
        <StatCard
          label="Awaiting Your Reply"
          value={effectiveness ? effectiveness.awaiting_reply : loading ? "—" : 0}
          tone="accent"
          icon={ClockIcon}
          hint="Threads where the seeker spoke last"
        />
        <StatCard
          label="Resolution Rate"
          value={
            effectiveness
              ? `${Math.round(effectiveness.resolution_rate * 100)}%`
              : loading ? "—" : "0%"
          }
          tone="primary"
          icon={TargetIcon}
          hint="Requests with dispatched counsel"
        />
        <StatCard
          label="Avg First Response"
          value={
            effectiveness ? formatDuration(effectiveness.avg_first_response_minutes) : "—"
          }
          tone="blue"
          icon={SendIcon}
          hint="Question → first staff reply"
        />
      </div>

      {/* Optional self-readings — deliberately low-key, not the. */}
      <PersonalPracticeRow note="Optional self-readings, kept separate from your work with seekers." />

      {/* Effectiveness + queue health */}
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel
          title="Guidance Effectiveness"
          subtitle="How your counsel moves seeker threads forward"
        >
          {!effectiveness ? (
            <div className="py-2">
              <SkeletonRow lines={3} />
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-600">Threads with counsel</span>
                  <span className="font-bold text-slate-900">
                    {effectiveness.with_guidance} of {insights?.total_requests ?? 0}
                  </span>
                </div>
                <MeterBar value={effectiveness.resolution_rate} tone="emerald" label="Resolution rate" />
              </div>
              <ul className="space-y-2 text-sm">
                <li className="row-hover flex items-center justify-between rounded-control bg-slate-50/60 p-2.5">
                  <span className="text-slate-600">Resolved consultations</span>
                  <span className="font-semibold text-emerald-700 tabular-nums">
                    {statusCounts.resolved || 0}
                  </span>
                </li>
                <li className="row-hover flex items-center justify-between rounded-control bg-slate-50/60 p-2.5">
                  <span className="text-slate-600">Readings reviewed platform-wide</span>
                  <span className="font-semibold text-primary-700 tabular-nums">
                    {effectiveness.total_guidance}
                  </span>
                </li>
                <li className="row-hover flex items-center justify-between rounded-control bg-slate-50/60 p-2.5">
                  <span className="text-slate-600">Seeker follow-ups waiting on you</span>
                  <span className={`font-semibold tabular-nums ${effectiveness.awaiting_reply > 0 ? "text-accent-600" : "text-slate-500"}`}>
                    {effectiveness.awaiting_reply}
                  </span>
                </li>
              </ul>
              <p className="text-xs italic text-slate-500">
                First-response timing is measured from real thread messages — questions to a
                verified reader&apos;s or consultant&apos;s first reply.
              </p>
            </div>
          )}
        </Panel>

        <Panel title="Queue Health" subtitle="Where every consultation thread currently stands">
          {!insights ? (
            <div className="py-2">
              <SkeletonRow lines={3} />
            </div>
          ) : queueTotal === 0 ? (
            <EmptyState
              icon={ChatIcon}
              title="No consultations yet"
              description="Threads appear here the moment a seeker submits a question."
            />
          ) : (
            <div className="space-y-3.5">
              {statusRows.map((row) => (
                <div key={row.status}>
                  <div className="mb-1.5 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-600">
                      {STATUS_LABELS[row.status]}
                    </span>
                    <span className="font-bold text-slate-900">
                      {row.count} · {queueTotal ? Math.round((row.count / queueTotal) * 100) : 0}%
                    </span>
                  </div>
                  <MeterBar
                    value={queueTotal ? row.count / queueTotal : 0}
                    tone={row.status === "resolved" ? "emerald" : row.status === "open" ? "accent" : "blue"}
                    label={`${STATUS_LABELS[row.status]} share of queue`}
                  />
                </div>
              ))}
              <p className="text-xs italic text-slate-500">
                {statusCounts.open || 0} open · {statusCounts.in_review || 0} in review ·{" "}
                {statusCounts.resolved || 0} resolved across {queueTotal} threads.
              </p>
            </div>
          )}
        </Panel>
      </div>

      {/* Community activity: readings vs consultations */}
      <Panel
        title="Consultation & Divination Dynamics"
        subtitle="Seeker sessions and guidance requests over the last 7 days"
      >
        {trends && trends.readings_per_day.length === 0 && trends.consultations_per_day.length === 0 ? (
          <EmptyState
            icon={ChartIcon}
            title="No seeker trends recorded"
            description="No seeker sessions were recorded for this period."
          />
        ) : trends ? (
          <PerDayBars
            ariaLabel="Daily readings and consultations"
            series={[
              {
                key: "readings",
                label: "Divination sessions",
                barClass: "bg-gradient-to-t from-emerald-500 to-teal-300",
                swatchClass: "bg-emerald-500",
                data: trends.readings_per_day,
              },
              {
                key: "consultations",
                label: "Guidance requests",
                barClass: "bg-gradient-to-t from-primary-500 to-primary-300",
                swatchClass: "bg-primary-500",
                data: trends.consultations_per_day,
              },
            ]}
          />
        ) : (
          <div className="py-2">
            <SkeletonRow lines={3} />
          </div>
        )}
        {trends && (
          <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
            <UsersIcon className="h-3.5 w-3.5 text-emerald-600" />
            Community: {trends.active_users} active of {trends.total_users} registered seekers.
          </p>
        )}
      </Panel>

      {/* Top consultation focus areas */}
      <Panel
        title="Key Inquiry Themes & Dominant Archetypes"
        subtitle="Most frequent themes surfaced in seeker inquiries"
      >
        {!insights || insights.top_topics.length === 0 ? (
          <EmptyState
            icon={SearchIcon}
            title="No inquiry themes yet"
            description="Themes appear once seekers start submitting consultations."
          />
        ) : (
          <div className="flex flex-wrap gap-2.5">
            {insights.top_topics.map((t) => (
              <span
                key={t.topic}
                className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200/80 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800"
              >
                <span>{t.topic}</span>
                <span className="rounded-full bg-emerald-200/60 px-1.5 py-0.5 text-[10px] font-bold">
                  {t.count}
                </span>
              </span>
            ))}
          </div>
        )}
      </Panel>

      {/* Provide spiritual guidance queue */}
      <Panel
        title="Seeker Guidance Queue"
        subtitle="Provide personalized counsel, spiritual remedies, and interpretations"
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative w-52">
              <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={queueSearch}
                onChange={(e) => setQueueSearch(e.target.value)}
                placeholder="Search topics…"
                aria-label="Search consultations by topic"
                className="w-full rounded-control border border-slate-200 bg-slate-50 py-1.5 pl-9 pr-3 text-xs text-slate-800 transition placeholder:text-slate-500 focus:border-primary-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
              />
            </div>
            <Segmented
              label="Consultation queue filter"
              value={queueFilter}
              onChange={setQueueFilter}
              options={STATUS_FILTERS.map((value) => ({
                value,
                label:
                  value === "all"
                    ? `All (${queueTotal})`
                    : `${STATUS_LABELS[value]} (${statusCounts[value] || 0})`,
              }))}
            />
          </div>
        }
      >
        {loading ? (
          <div className="space-y-3 py-2">
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
          </div>
        ) : filteredQueue.length === 0 ? (
          <EmptyState
            icon={ChatIcon}
            title={
              queueTotal === 0
                ? "All consultations resolved"
                : "No threads match this filter"
            }
            description={
              queueTotal === 0
                ? "Every seeker inquiry has received counsel. New requests will appear here."
                : "Try a different status filter or clear the topic search."
            }
          />
        ) : (
          <ul className="space-y-4">
            {filteredQueue.slice(0, 10).map((c) => (
              <li key={c.id} className="surface-card p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{c.topic}</h3>
                    <p className="mt-0.5 text-xs text-slate-500 tabular-nums">
                      Inquiry ID: {c.id.slice(0, 8)}… · {new Date(c.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge tone={c.status === "resolved" ? "emerald" : c.status === "open" ? "accent" : "blue"}>
                    {STATUS_LABELS[c.status] || c.status}
                  </Badge>
                </div>

                <p className="mt-2 rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700">
                  &ldquo;{c.message}&rdquo;
                </p>

                {c.guidance ? (
                  <div className="mt-3 rounded-xl border border-emerald-200/60 bg-emerald-50/80 p-3.5 text-xs leading-relaxed text-emerald-900">
                    <p className="mb-0.5 font-bold text-emerald-800">Dispatched counsel:</p>
                    {c.guidance}
                  </div>
                ) : (
                  <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                    <textarea
                      value={guidanceText[c.id] || ""}
                      onChange={(e) =>
                        setGuidanceText((prev) => ({ ...prev, [c.id]: e.target.value }))
                      }
                      placeholder="Type deep, compassionate spiritual counsel for this seeker…"
                      rows={2}
                      aria-label={`Guidance for inquiry ${c.topic}`}
                      className="w-full rounded-control border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 transition placeholder:text-slate-500 focus:border-primary-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                    />
                    <Button
                      size="sm"
                      variant="secondary"
                      icon={SendIcon}
                      loading={busyId === c.id}
                      disabled={busyId === c.id || !(guidanceText[c.id] || "").trim()}
                      onClick={() => sendGuidance(c)}
                      className="shrink-0 self-end sm:self-center"
                    >
                      Send counsel
                    </Button>
                  </div>
                )}

                <div className="mt-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      setOpenThreads((prev) => ({ ...prev, [c.id]: !prev[c.id] }))
                    }
                  >
                    {openThreads[c.id] ? "Hide conversation" : "Open conversation"}
                  </Button>
                </div>
                {openThreads[c.id] && (
                  <div className="animate-tab-in">
                    <ConsultationThread
                      consultationId={c.id}
                      composeLabel="Respond to this seeker…"
                      onMessageSent={refresh}
                    />
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
