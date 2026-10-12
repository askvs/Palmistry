// Client profile header + overview metric cards.
import { Button, Panel } from "@/components/ui";
import {
  ArrowLeftIcon,
  CalendarIcon,
  ChatIcon,
  FileTextIcon,
  TargetIcon,
  TrendingUpIcon,
} from "@/components/icons";
import {
  ClientAvatar,
  ClientStatusBadge,
  SourceBadge,
  TrendBadge,
} from "@/components/consultant/shared";
import { MeterBar } from "@/components/dashboards/shared";
import { formatDate, relativeLabel } from "@/lib/format";

const OVERVIEW_METRICS = [
  { key: "personalityAlignment", label: "Personality Alignment", hint: "Blended palm + tarot signals" },
  { key: "careerTrend", label: "Career Trend", hint: "Direction of career-themed readings" },
  { key: "growthPotential", label: "Growth Potential", hint: "Capacity implied by the signals" },
  { key: "readingConsistency", label: "Reading Consistency", hint: "How stable the signals are" },
];

export function ClientOverviewHeader({
  client,
  onStartConsultation,
  onViewReports,
  starting = false,
}) {
  return (
    <div className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs sm:p-7">
      <Button href="/consultant/clients" variant="ghost" size="sm" icon={ArrowLeftIcon}>
        Back to Clients
      </Button>

      <div className="mt-4 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-4">
          <ClientAvatar name={client.name} size="lg" />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-3xl tracking-tight text-slate-900">{client.name}</h1>
              <ClientStatusBadge status={client.status} />
              <TrendBadge trend={client.trend} />
              {client.profilePending && (
                <span className="rounded-full bg-accent-50 px-2.5 py-0.5 text-xs font-medium text-accent-800 ring-1 ring-accent-200">
                  Live thread · profile pending
                </span>
              )}
            </div>

            <dl className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
              <div>
                <dt className="text-xs text-slate-400">Age group</dt>
                <dd className="font-medium text-slate-700">{client.ageGroup || "—"}</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-400">Interests</dt>
                <dd className="font-medium text-slate-700">
                  {client.interests.join(", ") || "Not recorded"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-slate-400">Last consultation</dt>
                <dd className="font-medium text-slate-700">
                  {client.lastConsultationAt
                    ? `${formatDate(client.lastConsultationAt)} · ${relativeLabel(
                        client.lastConsultationAt
                      )}`
                    : "—"}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            icon={FileTextIcon}
            href={`/consultant/reports?client=${encodeURIComponent(client.id)}`}
          >
            Reports
          </Button>
          <Button icon={ChatIcon} loading={starting} onClick={onStartConsultation}>
            Start Consultation
          </Button>
        </div>
      </div>
    </div>
  );
}

export function ClientOverviewCards({ client }) {
  const hasMetrics = Boolean(client?.metrics);

  return (
    <Panel
      title="Client overview"
      subtitle="Signal strength across this client's readings"
      action={<SourceBadge source={hasMetrics ? client.source : "demo"} />}
    >
      {!hasMetrics ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-10 text-center">
          <TargetIcon className="mx-auto h-6 w-6 text-slate-400" />
          <h3 className="mt-3 text-sm font-semibold text-slate-900">No scores available yet</h3>
          <p className="mx-auto mt-1.5 max-w-sm text-sm leading-relaxed text-slate-500">
            Overview scores are computed from a client&rsquo;s own readings. This seeker has no
            readings shared with the consultant workspace yet.
          </p>
        </div>
      ) : (
        <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {OVERVIEW_METRICS.map((metric) => (
            <li key={metric.key} className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {metric.label}
                </p>
                <TrendingUpIcon className="h-4 w-4 shrink-0 text-primary-500" />
              </div>
              <p className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
                {client.metrics[metric.key]}%
              </p>
              <div className="mt-2.5">
                <MeterBar
                  value={client.metrics[metric.key] / 100}
                  tone="primary"
                  label={`${metric.label} score`}
                />
              </div>
              <p className="mt-2 text-[11px] text-slate-400">{metric.hint}</p>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function ClientConsultationHistory({ consultations = [], source }) {
  return (
    <Panel
      title="Consultation history"
      subtitle="Sessions delivered with this client"
      action={<SourceBadge source={source} />}
    >
      {consultations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-10 text-center">
          <CalendarIcon className="mx-auto h-6 w-6 text-slate-400" />
          <h3 className="mt-3 text-sm font-semibold text-slate-900">No sessions recorded</h3>
          <p className="mx-auto mt-1.5 max-w-sm text-sm leading-relaxed text-slate-500">
            Start a consultation to begin this client&rsquo;s session history.
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {consultations.map((session) => (
            <li
              key={session.id}
              className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-900">{session.purpose}</p>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {formatDate(session.startedAt)}
                    {session.durationMinutes ? ` · ${session.durationMinutes} min` : ""}
                    {session.followUpDate ? ` · follow-up ${formatDate(session.followUpDate)}` : ""}
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                  {session.status}
                </span>
              </div>
              {session.guidance && (
                <p className="mt-2 rounded-xl bg-emerald-50/80 px-3 py-2 text-xs leading-relaxed text-emerald-900">
                  {session.guidance}
                </p>
              )}
              {session.notes && (
                <p className="mt-2 rounded-xl bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-600">
                  <span className="font-semibold text-slate-700">Your notes: </span>
                  {session.notes}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
