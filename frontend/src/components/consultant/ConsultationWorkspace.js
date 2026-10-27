// Consultation Workspace — the consultant's main working environment.
import { useMemo, useState } from "react";
import { Button, Panel, SkeletonRow } from "@/components/ui";
import {
  ArrowLeftIcon,
  BrainIcon,
  CardsIcon,
  ChatIcon,
  FileTextIcon,
  HandIcon,
  PencilIcon,
  SparklesIcon,
  TargetIcon,
} from "@/components/icons";
import {
  ClientAvatar,
  EmptyState,
  FieldLabel,
  SectionError,
  SourceBadge,
  StatusBadge,
  TrendBadge,
} from "@/components/consultant/shared";
import { MeterBar } from "@/components/dashboards/shared";
import PalmAnalysisSummary from "@/components/consultant/PalmAnalysisSummary";
import TarotHistoryTable from "@/components/consultant/TarotHistoryTable";
import AIConsultationInsights from "@/components/consultant/AIInsightCard";
import ConsultantNotes from "@/components/consultant/ConsultantNotes";
import { READING_TYPE_LABELS } from "@/services/consultantDemoData";
import { formatDate, formatDateTime, relativeLabel } from "@/lib/format";

const TABS = [
  { value: "overview", label: "Overview", icon: TargetIcon },
  { value: "palm", label: "Palm Analysis", icon: HandIcon },
  { value: "tarot", label: "Tarot", icon: CardsIcon },
  { value: "personality", label: "Personality", icon: BrainIcon },
  { value: "insights", label: "AI Insights", icon: SparklesIcon },
  { value: "notes", label: "Notes", icon: PencilIcon },
];

function MetricRow({ label, value, hint }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2 text-xs">
        <span className="font-medium text-slate-600">{label}</span>
        <span className="font-bold text-slate-900 tabular-nums">{value}%</span>
      </div>
      <MeterBar value={value / 100} tone="primary" label={label} />
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

function ClientInfoRail({ client }) {
  if (!client) {
    return (
      <Panel title="Client information">
        <EmptyState
          icon={ChatIcon}
          title="Profile not available"
          description="This seeker's profile is not exposed to consultants by the API yet."
        />
      </Panel>
    );
  }

  return (
    <Panel
      title="Client information"
      subtitle={client.profilePending ? "Live guidance thread" : "Profile overview"}
    >
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <ClientAvatar name={client.name} size="lg" />
          <div className="min-w-0">
            <p className="truncate text-base font-semibold text-slate-900">{client.name}</p>
            <p className="text-xs text-slate-500">
              Age group {client.ageGroup || "—"}
              {client.location && client.location !== "—" ? ` · ${client.location}` : ""}
            </p>
          </div>
        </div>

        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Interests
            </dt>
            <dd className="mt-1 flex flex-wrap gap-1.5">
              {client.interests.length ? (
                client.interests.map((interest) => (
                  <span
                    key={interest}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
                  >
                    {interest}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-500">Not recorded</span>
              )}
            </dd>
          </div>

          {client.goals?.length > 0 && (
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Goals</dt>
              <dd className="mt-1 space-y-1 text-sm leading-relaxed text-slate-600">
                {client.goals.map((goal) => (
                  <p key={goal}>· {goal}</p>
                ))}
              </dd>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 border-t border-slate-100 pt-3">
            <div>
              <dt className="text-xs text-slate-500">Previous sessions</dt>
              <dd className="text-sm font-semibold text-slate-900 tabular-nums">
                {client.consultationCount}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Readings</dt>
              <dd className="text-sm font-semibold text-slate-900 tabular-nums">
                {client.readingCount}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Last consultation</dt>
              <dd className="text-sm font-semibold text-slate-900">
                {relativeLabel(client.lastConsultationAt)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Current trend</dt>
              <dd className="mt-0.5">
                <TrendBadge trend={client.trend} />
              </dd>
            </div>
          </div>
        </dl>

        <Button
          href={`/consultant/clients/${client.id}`}
          variant="secondary"
          size="sm"
          icon={ArrowLeftIcon}
          fullWidth
        >
          Full client profile
        </Button>
      </div>
    </Panel>
  );
}

function ConsultationSummary({
  session,
  client,
  source,
  guidance,
  onGuidanceChange,
  followUpDate,
  onFollowUpChange,
  onSave,
  onSaveDraft,
  onGenerateReport,
  saving,
  saved,
}) {
  const insights = client?.aiInsights || [];

  return (
    <Panel
      title="Consultation summary"
      subtitle="What this session is about and what comes out of it"
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-4">
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Consultation type
            </dt>
            <dd className="mt-0.5 font-semibold text-slate-900">{session?.purpose || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Current topic
            </dt>
            <dd className="mt-0.5 text-slate-700">
              {session?.liveMessage || session?.purpose || "Not set"}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</dt>
            <dd className="mt-1">
              <StatusBadge status={session?.status || "pending"} />
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Started
            </dt>
            <dd className="mt-0.5 text-slate-700">
              {session?.startedAt ? formatDateTime(session.startedAt) : "—"}
            </dd>
          </div>
        </dl>

        <div className="border-t border-slate-100 pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Key insights
          </p>
          {insights.length === 0 ? (
            <p className="mt-1.5 text-xs text-slate-500">
              Generate AI insights from the AI Insights tab to populate this summary.
            </p>
          ) : (
            <ul className="mt-2 space-y-2">
              {insights.slice(0, 3).map((insight) => (
                <li key={insight.id} className="rounded-control bg-slate-50/80 px-3 py-2">
                  <p className="text-xs font-bold uppercase tracking-wide text-primary-700">
                    {insight.category}
                  </p>
                  <p className="mt-0.5 text-sm leading-relaxed text-slate-700">{insight.insight}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="border-t border-slate-100 pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Recommendations
          </p>
          {client?.recommendations?.length ? (
            <ul className="mt-2 space-y-2">
              {client.recommendations.slice(0, 3).map((recommendation) => (
                <li key={recommendation.id} className="text-sm leading-relaxed text-slate-700">
                  <span className="font-semibold text-slate-800">{recommendation.title}</span>
                  <span className="ml-1 text-xs text-slate-500">({recommendation.priority})</span>
                  <p className="mt-0.5 text-sm text-slate-600">{recommendation.text}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1.5 text-xs text-slate-500">No recommendations recorded yet.</p>
          )}
        </div>

        <label className="block border-t border-slate-100 pt-4">
          <span className="mb-1.5 block">
            <FieldLabel hint="Optional">Follow-up date</FieldLabel>
          </span>
          <input
            type="date"
            value={followUpDate || ""}
            onChange={(event) => onFollowUpChange?.(event.target.value)}
            className="h-10 w-full cursor-pointer rounded-control border border-slate-200 bg-white px-3 text-sm text-slate-700 transition focus:border-primary-400 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </label>

        <div className="space-y-2 border-t border-slate-100 pt-4">
          <Button fullWidth loading={saving} onClick={() => onSave?.()} disabled={saving}>
            {saved ? "Saved" : "Save consultation"}
          </Button>
          <Button
            variant="secondary"
            fullWidth
            icon={FileTextIcon}
            onClick={onGenerateReport}
          >
            Generate report
          </Button>
          <Button variant="ghost" fullWidth onClick={() => onSaveDraft?.()}>
            Save draft
          </Button>
        </div>
      </div>
    </Panel>
  );
}

export default function ConsultationWorkspace({
  session,
  client,
  source,
  loading = false,
  error = null,
  onRetry,
  onSaveNotes,
  onSaveConsultation,
  onGenerateReport,
  onSendGuidance,
  saving = false,
  saved = false,
}) {
  const [tab, setTab] = useState("overview");
  const [notes, setNotes] = useState(session?.notes || "");
  const [guidance, setGuidance] = useState(session?.guidance || "");
  const [followUpDate, setFollowUpDate] = useState(session?.followUpDate || "");
  const [sendingGuidance, setSendingGuidance] = useState(false);

  const pastSessions = useMemo(() => {
    const rows = client?.consultations || [];
    return rows.filter((row) => row.id !== session?.id).slice(0, 6);
  }, [client, session]);

  async function handleSendGuidance() {
    const liveId = session?.liveConsultationId;
    if (!liveId || !guidance.trim()) return;
    setSendingGuidance(true);
    try {
      await onSendGuidance?.(liveId, { guidance: guidance.trim() });
    } finally {
      setSendingGuidance(false);
    }
  }

  if (loading) {
    return (
      <div className="grid gap-5 lg:grid-cols-[18rem_1fr] xl:grid-cols-[18rem_1fr_20rem]">
        <Panel title="Client information">
          <SkeletonRow lines={6} />
        </Panel>
        <Panel title="Workspace">
          <SkeletonRow lines={8} />
        </Panel>
        <Panel title="Summary">
          <SkeletonRow lines={6} />
        </Panel>
      </div>
    );
  }

  if (error || !session) {
    return (
      <SectionError
        title={error || "This consultation could not be found."}
        onRetry={onRetry}
      />
    );
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[18rem_1fr] xl:grid-cols-[18rem_1fr_20rem]">
      <div className="space-y-5">
        <ClientInfoRail client={client} />

        <Panel title="Previous sessions" subtitle="Earlier work with this client">
          {pastSessions.length === 0 ? (
            <p className="text-xs text-slate-500">No earlier sessions recorded.</p>
          ) : (
            <ul className="space-y-2.5">
              {pastSessions.map((row) => (
                <li key={row.id} className="rounded-control bg-slate-50/80 px-3 py-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{row.purpose}</p>
                    <StatusBadge status={row.status} />
                  </div>
                  <p className="mt-0.5 text-xs text-slate-500 tabular-nums">
                    {formatDate(row.startedAt)}
                    {row.durationMinutes ? ` · ${row.durationMinutes} min` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <div className="min-w-0 space-y-5">
        {/* Session banner */}
        <div className="surface-card flex flex-wrap items-center justify-between gap-3 p-5">
          <div className="flex items-center gap-3">
            <ClientAvatar name={session.clientName || client?.name || "Seeker"} size="md" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">
                {session.clientName || client?.name || "Seeker"}
              </p>
              <p className="truncate text-xs text-slate-500 tabular-nums">
                {session.purpose} · started {formatDate(session.startedAt)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={session.status || "pending"} />
            {session.liveConsultationId && (
              <Button
                size="sm"
                icon={ChatIcon}
                loading={sendingGuidance}
                disabled={!guidance.trim() || sendingGuidance}
                onClick={handleSendGuidance}
              >
                Send to client
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div
          role="tablist"
          aria-label="Consultation workspace sections"
          className="flex flex-wrap gap-1 rounded-panel border border-slate-200 bg-slate-100/80 p-1"
        >
          {TABS.map((item) => {
            const active = tab === item.value;
            return (
              <button
                key={item.value}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setTab(item.value)}
                className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                  active
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <item.icon className="h-3.5 w-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>

        <div key={tab} role="tabpanel" aria-label={TABS.find((item) => item.value === tab)?.label} className="animate-tab-in">
        {tab === "overview" && (
          <div className="space-y-5">
            {session.liveMessage && (
              <Panel title="Seeker's question" subtitle="What opened this thread">
                <p className="rounded-card border border-slate-100 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700">
                  &ldquo;{session.liveMessage}&rdquo;
                </p>
              </Panel>
            )}

            <Panel title="Client snapshot" subtitle="Signals across this client's readings">
              {client?.metrics ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <MetricRow label="Personality alignment" value={client.metrics.personalityAlignment} />
                  <MetricRow label="Career trend" value={client.metrics.careerTrend} />
                  <MetricRow label="Growth potential" value={client.metrics.growthPotential} />
                  <MetricRow label="Reading consistency" value={client.metrics.readingConsistency} />
                </div>
              ) : (
                <EmptyState
                  icon={TargetIcon}
                  title="No metrics available"
                  description="Scores appear once this client has readings the platform can analyse."
                />
              )}
            </Panel>

            <Panel
              title="Reading context"
              subtitle={`Latest reading: ${READING_TYPE_LABELS[client?.latestReading] || client?.latestReading || "—"}`}
            >
              <dl className="grid gap-3 sm:grid-cols-3">
                <div>
                  <dt className="text-xs text-slate-500">Latest reading</dt>
                  <dd className="text-sm font-semibold text-slate-900">
                    {client?.latestReadingAt ? formatDate(client.latestReadingAt) : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Readings on file</dt>
                  <dd className="text-sm font-semibold text-slate-900">{client?.readingCount ?? 0}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Consultations</dt>
                  <dd className="text-sm font-semibold text-slate-900">
                    {client?.consultationCount ?? 0}
                  </dd>
                </div>
              </dl>
            </Panel>
          </div>
        )}

        {tab === "palm" && (
          <PalmAnalysisSummary
            palm={client?.palm}
            source={client ? source : "demo"}
            loading={false}
          />
        )}

        {tab === "tarot" && (
          <TarotHistoryTable rows={client?.tarotHistory || []} source={client ? source : "demo"} />
        )}

        {tab === "personality" && (
          <Panel
            title="Personality"
            subtitle="Blended palm and tarot signals for this client"
            action={<SourceBadge source={client?.personality ? source : "demo"} />}
          >
            {!client?.personality ? (
              <EmptyState
                icon={BrainIcon}
                title="No personality profile yet"
                description="A blended profile appears once this client has both a palm scan and a tarot reading."
              />
            ) : (
              <div className="space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-primary-100 bg-primary-50/50 p-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-primary-700">
                      Archetype
                    </p>
                    <p className="mt-1 font-display text-lg font-semibold tracking-[-0.02em] text-slate-900">
                      {client.personality.archetype}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Alignment</p>
                    <p className="font-display text-lg font-semibold text-slate-900 tabular-nums">
                      {client.personality.alignment}%
                    </p>
                  </div>
                </div>

                <p className="text-sm leading-relaxed text-slate-700">
                  {client.personality.summary}
                </p>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                      Strengths
                    </p>
                    <ul className="mt-1.5 space-y-1 text-sm text-slate-600">
                      {client.personality.strengths.map((item) => (
                        <li key={item}>· {item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-accent-700">
                      Growth areas
                    </p>
                    <ul className="mt-1.5 space-y-1 text-sm text-slate-600">
                      {client.personality.growthAreas.map((item) => (
                        <li key={item}>· {item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </Panel>
        )}

        {tab === "insights" && (
          <AIConsultationInsights
            insights={client?.aiInsights || []}
            source={client?.aiInsights?.length ? source : "demo"}
          />
        )}

        {tab === "notes" && (
          <div className="space-y-5">
            <ConsultantNotes
              value={notes}
              onChange={setNotes}
              onSaveDraft={(text) => onSaveNotes?.(text)}
              onSaveConsultation={(text) => onSaveConsultation?.(text)}
              saving={saving}
              saved={saved}
              contextLabel={session.clientName || client?.name || "this client"}
            />

            <Panel
              title="Guidance you will share"
              subtitle="Written by you — nothing is sent automatically"
            >
              <textarea
                value={guidance}
                onChange={(event) => setGuidance(event.target.value)}
                rows={5}
                placeholder="Write the guidance you will share with this client…"
                aria-label="Guidance to the client"
                className="w-full rounded-control border border-slate-200 px-3.5 py-2.5 text-sm leading-relaxed text-slate-800 transition placeholder:text-slate-500 focus:border-primary-400 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
              />
              {!session.liveConsultationId && (
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  This session is not linked to a live guidance thread, so the text is saved with
                  the consultation only.
                </p>
              )}
            </Panel>
          </div>
        )}
        </div>
      </div>

      <ConsultationSummary
        session={session}
        client={client}
        source={source}
        guidance={guidance}
        onGuidanceChange={setGuidance}
        followUpDate={followUpDate}
        onFollowUpChange={setFollowUpDate}
        onSave={() => onSaveConsultation?.(notes, { guidance, followUpDate })}
        onSaveDraft={() => onSaveNotes?.(notes)}
        onGenerateReport={onGenerateReport}
        saving={saving}
        saved={saved}
      />
    </div>
  );
}
