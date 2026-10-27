// System reports surfaces for the administrator (FR-038): overview, health,
// error reports, and measured performance. Every value comes from real data.
import { useCallback } from "react";
import { Badge, EmptyState, ErrorState, Panel, SkeletonRow } from "@/components/ui";
import { MeterBar, StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  adminReportsErrors,
  adminReportsHealth,
  adminReportsOverview,
  adminReportsPerformance,
} from "@/services/roles";
import {
  ActivityIcon,
  AlertIcon,
  ChartIcon,
  CheckCircleIcon,
  ClockIcon,
  FileTextIcon,
  UsersIcon,
} from "@/components/icons";

const CATEGORY_LABELS = {
  server_error: "Server error",
  analysis_failed: "Failed analysis",
  auth_failure: "Auth failure",
  forbidden: "Forbidden",
  rate_limited: "Rate limited",
  validation_error: "Validation error",
};

const CATEGORY_TONES = {
  server_error: "rose",
  analysis_failed: "amber",
  auth_failure: "indigo",
  forbidden: "rose",
  rate_limited: "amber",
  validation_error: "slate",
};

// One service line in the health panel: dot + name + real check result.
function ServiceRow({ label, detail, state }) {
  const dotClass =
    state === "ok" ? "bg-emerald-500" : state === "warn" ? "bg-accent-500" : "bg-rose-600";
  const detailClass =
    state === "ok" ? "text-emerald-700" : state === "warn" ? "text-slate-500" : "text-rose-700";
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2.5">
      <span className="flex items-center gap-2.5 text-[13px] font-medium text-slate-700">
        <span className={`h-2 w-2 shrink-0 rounded-full ${dotClass}`} aria-hidden="true" />
        {label}
      </span>
      <span className={`text-right text-[12.5px] font-semibold tabular-nums ${detailClass}`}>
        {detail}
      </span>
    </div>
  );
}

function healthState(block) {
  if (block.status === "ok" || block.status === "configured") return "ok";
  if (block.status === "not_configured") return "warn";
  return "bad";
}

export function SystemOverviewPanel({ days }) {
  const loader = useCallback(() => adminReportsOverview(days), [days]);
  const { data, error, loading } = useAsyncData(loader);

  if (error) return <ErrorState message={error.message} />;
  if (loading || !data) return <SkeletonRow lines={4} />;

  const { users, analyses } = data;
  const totalInWindow = analyses.successful + analyses.failed;
  const types = analyses.success_by_type.map((row) => ({
    type: row.type,
    successful: row.count,
    failed: analyses.failed_by_type.find((item) => item.type === row.type)?.count ?? 0,
  }));

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Registered Users"
          value={users.total.toLocaleString()}
          tone="primary"
          icon={UsersIcon}
          hint={`+${users.new_in_period.toLocaleString()} in the last ${days} days`}
        />
        <StatCard
          label="Total Analyses"
          value={totalInWindow.toLocaleString()}
          tone="accent"
          icon={FileTextIcon}
          hint={`${analyses.total_all_time.toLocaleString()} all-time`}
        />
        <StatCard
          label="Successful Analyses"
          value={analyses.successful.toLocaleString()}
          tone="emerald"
          icon={CheckCircleIcon}
          hint={`${analyses.successful_all_time.toLocaleString()} all-time`}
        />
        <StatCard
          label="Failed Analyses"
          value={analyses.failed.toLocaleString()}
          tone={analyses.failed > 0 ? "rose" : "slate"}
          icon={AlertIcon}
          hint={
            analyses.failed_tracking_since
              ? `${analyses.failed_all_time.toLocaleString()} all-time · tracked since ${new Date(
                  analyses.failed_tracking_since
                ).toLocaleDateString()}`
              : "No failures recorded yet"
          }
        />
      </div>

      <Panel
        title="Analyses by Type"
        subtitle={`Successful and failed analyses in the last ${days} days`}
      >
        {totalInWindow === 0 ? (
          <EmptyState
            icon={FileTextIcon}
            title="No analyses in this window"
            description="No palm or tarot analyses completed or failed in the selected period."
          />
        ) : (
          <div className="space-y-3.5">
            {types.map((row) => {
              const count = row.successful + row.failed;
              return (
                <div key={row.type}>
                  <div className="mb-1.5 flex items-center justify-between text-[12.5px]">
                    <span className="font-medium capitalize text-slate-700">{row.type}</span>
                    <span className="font-bold tabular-nums text-slate-900">
                      {row.successful} ok · {row.failed} failed
                    </span>
                  </div>
                  <MeterBar
                    value={count / totalInWindow}
                    tone={row.type === "palm" ? "primary" : "accent"}
                    label={`${row.type} share of analyses`}
                  />
                </div>
              );
            })}
          </div>
        )}
      </Panel>
    </div>
  );
}

export function SystemHealthPanel() {
  const { data, error, loading } = useAsyncData(adminReportsHealth);

  if (error) return <ErrorState message={error.message} />;
  if (loading || !data) return <SkeletonRow lines={4} />;

  const aiDetail =
    data.ai_service.status === "configured"
      ? `${data.ai_provider} · ${data.ai_model}`
      : data.ai_service.detail;
  const uptimeHours = (data.uptime_seconds / 3600).toFixed(1);

  return (
    <Panel
      title="System Health"
      subtitle="Live backend and database checks; AI availability is configuration-based"
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <ServiceRow
            label="Backend"
            detail={data.backend.detail}
            state={healthState(data.backend)}
          />
          <ServiceRow
            label="Database"
            detail={
              data.database.status === "ok"
                ? `ok · ${data.database.latency_ms} ms`
                : data.database.detail
            }
            state={healthState(data.database)}
          />
          <ServiceRow label="AI service" detail={aiDetail} state={healthState(data.ai_service)} />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="slate">{data.environment}</Badge>
          <Badge tone="blue">v{data.version}</Badge>
          <Badge tone="slate">up {uptimeHours} h</Badge>
          <Badge tone="slate">since {new Date(data.started_at).toLocaleString()}</Badge>
        </div>

        <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
          {data.notes.map((note) => (
            <li key={note} className="text-[12.5px] leading-relaxed text-slate-500">
              {note}
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

export function PerformanceReportPanel({ days }) {
  const loader = useCallback(() => adminReportsPerformance(days), [days]);
  const { data, error, loading } = useAsyncData(loader);

  if (error) return <ErrorState message={error.message} />;
  if (loading || !data) return <SkeletonRow lines={5} />;

  const { api, analysis_generation: analysis } = data;

  return (
    <div className="space-y-5">
      <Panel
        title="API Response Times"
        subtitle={`Measured per request over the last ${days} days`}
      >
        {api.status === "no_data" ? (
          <EmptyState
            icon={ClockIcon}
            title="No API samples yet"
            description="Response-time samples are collected as the API serves traffic; this window has none yet."
          />
        ) : (
          <div className="space-y-4">
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard
                label="Average"
                value={`${api.avg_ms} ms`}
                tone="primary"
                icon={ClockIcon}
                hint="Mean response time"
              />
              <StatCard
                label="p95"
                value={`${api.p95_ms} ms`}
                tone="accent"
                icon={ActivityIcon}
                hint={`Median ${api.p50_ms} ms · max ${api.max_ms} ms`}
              />
              <StatCard
                label="Requests"
                value={api.requests.toLocaleString()}
                tone="blue"
                icon={ChartIcon}
                hint="Recorded samples in window"
              />
              <StatCard
                label="Error Rate"
                value={`${(api.error_rate * 100).toFixed(2)}%`}
                tone={api.error_rate > 0.01 ? "rose" : "emerald"}
                icon={AlertIcon}
                hint="Share of requests that returned 5xx"
              />
            </div>
            <p className="text-[12.5px] tabular-nums text-slate-500">
              Samples from {new Date(api.first_sample_at).toLocaleString()} to{" "}
              {new Date(api.last_sample_at).toLocaleString()} · health probes and API docs are
              excluded.
            </p>
          </div>
        )}
      </Panel>

      <Panel
        title="Analysis Generation Time"
        subtitle="Measured per generated palm and tarot reading"
      >
        {analysis.status === "no_data" ? (
          <EmptyState
            icon={ActivityIcon}
            title="No generation timings yet"
            description="Timings are recorded when a reading is generated; failed generations have no measured duration."
          />
        ) : (
          <div className="space-y-4">
            <div className="grid gap-5 sm:grid-cols-3">
              <StatCard
                label="Average"
                value={`${analysis.avg_ms} ms`}
                tone="emerald"
                icon={ActivityIcon}
                hint={`${analysis.samples} measured reading${analysis.samples === 1 ? "" : "s"}`}
              />
              <StatCard
                label="p95"
                value={`${analysis.p95_ms} ms`}
                tone="accent"
                icon={ClockIcon}
                hint={`Max ${analysis.max_ms} ms`}
              />
              <StatCard
                label="Measured Readings"
                value={analysis.samples.toLocaleString()}
                tone="primary"
                icon={FileTextIcon}
                hint={`Over the last ${days} days`}
              />
            </div>

            {analysis.by_type.length > 0 && (
              <div className="space-y-3.5">
                {analysis.by_type.map((row) => (
                  <div key={row.type}>
                    <div className="mb-1.5 flex items-center justify-between text-[12.5px]">
                      <span className="font-medium capitalize text-slate-700">{row.type}</span>
                      <span className="font-bold tabular-nums text-slate-900">
                        avg {row.avg_ms} ms · {row.samples} reading
                        {row.samples === 1 ? "" : "s"}
                      </span>
                    </div>
                    <MeterBar
                      value={row.samples / analysis.samples}
                      tone={row.type === "palm" ? "primary" : "accent"}
                      label={`${row.type} share of measured readings`}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Panel>

      <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
        {data.notes.map((note) => (
          <li key={note} className="text-[12.5px] leading-relaxed text-slate-500">
            {note}
          </li>
        ))}
      </ul>
    </div>
  );
}

function MiniCount({ label, value, tone = "text-slate-900" }) {
  return (
    <div className="surface-card p-3">
      <p className="text-[12.5px] font-medium text-slate-500">{label}</p>
      <p className={`mt-0.5 text-lg font-bold tabular-nums ${tone}`}>{value.toLocaleString()}</p>
    </div>
  );
}

export function ErrorReportPanel({ days }) {
  const loader = useCallback(() => adminReportsErrors(days), [days]);
  const { data, error, loading } = useAsyncData(loader);

  if (error) return <ErrorState message={error.message} />;
  if (loading || !data) return <SkeletonRow lines={5} />;

  const { counts, items } = data;

  return (
    <Panel
      title="Error Reports"
      subtitle={`Recent system errors and failed analyses in the last ${days} days`}
    >
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <MiniCount label="Entries" value={counts.rows} />
          <MiniCount label="Total occurrences" value={counts.total} />
          <MiniCount
            label="Failed analyses"
            value={counts.failed_analyses}
            tone="text-amber-700"
          />
          <MiniCount label="Server errors" value={counts.server_errors} tone="text-rose-700" />
        </div>

        {items.length === 0 ? (
          <EmptyState
            icon={CheckCircleIcon}
            title="No errors in this window"
            description="No operational errors or failed analyses were recorded for the selected period."
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((item) => (
              <li key={item.id} className="py-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={CATEGORY_TONES[item.category] || "slate"}>
                    {CATEGORY_LABELS[item.category] || item.category}
                  </Badge>
                  <code className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[12px] text-slate-600">
                    {item.method} {item.path}
                  </code>
                  <span className="text-[12.5px] font-semibold tabular-nums text-slate-700">
                    HTTP {item.status_code}
                  </span>
                  {item.occurrences > 1 && (
                    <span className="text-[12.5px] font-medium tabular-nums text-slate-500">
                      ×{item.occurrences}
                    </span>
                  )}
                  {item.acknowledged_at ? (
                    <Badge tone="emerald">Acknowledged</Badge>
                  ) : (
                    <Badge tone="slate">Open</Badge>
                  )}
                </div>
                <p className="mt-1.5 break-words text-[13px] leading-relaxed text-slate-700">
                  {item.description || "No description recorded"}
                </p>
                <p className="mt-1 text-[12.5px] tabular-nums text-slate-500">
                  Last seen {new Date(item.last_seen_at).toLocaleString()} · first seen{" "}
                  {new Date(item.first_seen_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        )}

        <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
          {data.notes.map((note) => (
            <li key={note} className="text-[12.5px] leading-relaxed text-slate-500">
              {note}
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
