// Platform analytics surfaces for the administrator (FR-007, FR-038).
import Link from "next/link";
import { useState } from "react";
import { Badge, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import { MeterBar, PerDayBars, StatCard, CONSULTATION_STATUS_LABELS } from "@/components/dashboards/shared";
import { roleMeta } from "@/lib/roles";
import {
  ActivityIcon,
  ChartIcon,
  ChatIcon,
  FileTextIcon,
  UsersIcon,
} from "@/components/icons";

const OVERSIGHT_FILTERS = [
  { value: "all", label: "All" },
  { value: "palm", label: "Palm" },
  { value: "tarot", label: "Tarot" },
];

const PERIOD_OPTIONS = [
  { value: "7", label: "7 days" },
  { value: "30", label: "30 days" },
];

export function AnalyticsWindowPicker({ days, onChange }) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <span className="text-xs font-medium text-slate-400">Analytics window</span>
      <div role="group" aria-label="Analytics window" className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100/80 p-0.5">
        {PERIOD_OPTIONS.map((option) => {
          const active = String(days) === option.value;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(Number(option.value))}
              className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                active ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function PlatformStatCards({ platform, readings, days, loading }) {
  const divinationDelta =
    platform && platform.readings_previous_period > 0
      ? Math.round(
          ((platform.readings_in_period - platform.readings_previous_period) /
            platform.readings_previous_period) *
            100
        )
      : null;

  return (
    <div className="grid gap-5 sm:grid-cols-4">
      <StatCard
        label="Registered Users"
        value={platform ? platform.users_total : loading ? "—" : 0}
        tone="primary"
        icon={UsersIcon}
        hint={platform ? `+${platform.signups_in_period} in the last ${days} days` : "Signup totals appear here"}
      />
      <StatCard
        label="Total Divinations"
        value={platform ? platform.readings_total : loading ? "—" : 0}
        tone="accent"
        icon={FileTextIcon}
        hint={platform ? `${platform.readings_in_period} in the last ${days} days` : "Palmistry & tarot readings"}
        trend={
          divinationDelta !== null
            ? {
                positive: divinationDelta >= 0,
                text: `${divinationDelta >= 0 ? "+" : ""}${divinationDelta}% vs previous ${days}d`,
              }
            : undefined
        }
      />
      <StatCard
        label="Consultations"
        value={platform ? platform.consultations_total : loading ? "—" : 0}
        tone="emerald"
        icon={ChatIcon}
        hint="Guidance inquiries"
      />
      <StatCard
        label="Active Users"
        value={platform ? platform.users_active : loading ? "—" : 0}
        tone="blue"
        icon={ActivityIcon}
        hint="Non-suspended accounts"
      />
    </div>
  );
}

export function UsersByRolePanel({ platform, loading }) {
  const usersByRole = platform?.users_by_role || [];
  const total = usersByRole.reduce((sum, row) => sum + row.count, 0);

  return (
    <Panel title="Users by Role" subtitle="Current role distribution across the platform">
      {!platform || usersByRole.length === 0 ? (
        <EmptyState
          icon={UsersIcon}
          title="No role data available"
          description="Role distribution appears once accounts are registered."
        />
      ) : (
        <div className="space-y-3.5">
          {usersByRole.map((row) => {
            const meta = roleMeta(row.role);
            return (
              <div key={row.role}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700">{meta.label}</span>
                  <span className="font-bold text-slate-900">
                    {row.count} · {total ? Math.round((row.count / total) * 100) : 0}%
                  </span>
                </div>
                <MeterBar
                  value={total ? row.count / total : 0}
                  tone={meta.badgeTone === "indigo" ? "primary" : meta.badgeTone}
                  label={`${meta.label} share of users`}
                />
              </div>
            );
          })}
        </div>
      )}
    </Panel>
  );
}

export function DivinationStatsPanel({ readings, loading }) {
  if (!readings) {
    return (
      <Panel title="Divination Statistics" subtitle="Reading type distribution and human review throughput">
        {loading ? (
          <SkeletonRow lines={4} />
        ) : (
          <EmptyState
            icon={FileTextIcon}
            title="No reading data available"
            description="Platform reading statistics appear after the first divination."
          />
        )}
      </Panel>
    );
  }

  const completed = readings.by_status?.find((row) => row.status === "completed")?.count ?? 0;

  return (
    <Panel title="Divination Statistics" subtitle="Reading type distribution and human review throughput">
      <div className="space-y-3.5">
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-2 text-sm">
          <span className="font-medium text-slate-700">Total platform readings</span>
          <span className="font-bold text-slate-900">{readings.total}</span>
        </div>
        {readings.by_type.map((row) => (
          <div key={row.type}>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium capitalize text-slate-700">{row.type} readings</span>
              <span className="font-bold text-slate-900">
                {row.count} · {readings.total ? Math.round((row.count / readings.total) * 100) : 0}%
              </span>
            </div>
            <MeterBar
              value={readings.total ? row.count / readings.total : 0}
              tone={row.type === "palm" ? "primary" : "accent"}
              label={`${row.type} readings share of all readings`}
            />
          </div>
        ))}
        <div className="flex items-center justify-between rounded-xl bg-slate-50/60 p-2 text-sm">
          <span className="text-slate-600">Reviewed by human reader</span>
          <span className="font-semibold text-emerald-700">{readings.reviewed_total}</span>
        </div>
        <div className="flex items-center justify-between rounded-xl bg-slate-50/60 p-2 text-sm">
          <span className="text-slate-600">Completed</span>
          <span className="font-semibold text-slate-700">
            {completed} of {readings.total}
          </span>
        </div>
      </div>
    </Panel>
  );
}

export function EngagementPanel({ platform, readings, loading }) {
  const engagement = platform?.engagement;
  const completed =
    readings?.by_status?.find((row) => row.status === "completed")?.count ?? 0;

  return (
    <Panel title="User Engagement" subtitle="Activation, return visits and completion — derived from real activity">
      {!platform || !readings ? (
        loading ? (
          <SkeletonRow lines={4} />
        ) : (
          <EmptyState
            icon={ActivityIcon}
            title="No engagement data yet"
            description="Engagement metrics appear once accounts and readings exist."
          />
        )
      ) : (
        <div className="space-y-3.5">
          <div>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">Activated accounts</span>
              <span className="font-bold text-slate-900">
                {engagement.users_with_readings} of {platform.users_total}
              </span>
            </div>
            <MeterBar
              value={platform.users_total ? engagement.users_with_readings / platform.users_total : 0}
              tone="primary"
              label="Share of accounts with at least one reading"
            />
            <p className="mt-1 text-xs text-slate-400">Accounts with at least one reading</p>
          </div>
          <div>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">Returning accounts</span>
              <span className="font-bold text-slate-900">
                {engagement.users_with_multiple_readings} of {platform.users_total}
              </span>
            </div>
            <MeterBar
              value={
                platform.users_total
                  ? engagement.users_with_multiple_readings / platform.users_total
                  : 0
              }
              tone="blue"
              label="Share of accounts with two or more readings"
            />
            <p className="mt-1 text-xs text-slate-400">Accounts with two or more readings</p>
          </div>
          <div>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">Reading completion</span>
              <span className="font-bold text-slate-900">
                {completed} of {readings.total}
              </span>
            </div>
            <MeterBar
              value={readings.total ? completed / readings.total : 0}
              tone="emerald"
              label="Completed readings share of all readings"
            />
            <p className="mt-1 text-xs text-slate-400">Completed vs pending divinations</p>
          </div>
        </div>
      )}
    </Panel>
  );
}

export function GrowthPanel({ platform, readings, days, loading }) {
  const hasSignups = (platform?.signups_per_day || []).length > 0;
  const hasReadings = readings && readings.total > 0;

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Panel title="Growth: Signups per Day" subtitle={`New accounts over the last ${days} days`}>
        {loading && !platform ? (
          <SkeletonRow lines={4} />
        ) : !hasSignups ? (
          <EmptyState
            icon={ChartIcon}
            title="No signups in this period"
            description="New registrations will chart here day by day."
          />
        ) : (
          <PerDayBars
            ariaLabel="Daily signups"
            days={days}
            series={[
              {
                key: "signups",
                label: "New accounts",
                barClass: "bg-gradient-to-t from-primary-600 to-primary-300",
                swatchClass: "bg-primary-600",
                data: platform.signups_per_day,
              },
            ]}
          />
        )}
      </Panel>

      <Panel title="Divination Activity" subtitle={`Readings per day across the platform — last ${days} days`}>
        {loading && !readings ? (
          <SkeletonRow lines={4} />
        ) : !hasReadings ? (
          <EmptyState
            icon={ChartIcon}
            title="No reading activity in this period"
            description="Daily palm and tarot readings will chart here."
          />
        ) : (
          <PerDayBars
            ariaLabel="Daily readings"
            days={days}
            series={[
              {
                key: "readings",
                label: "Readings",
                barClass: "bg-gradient-to-t from-accent-500 to-accent-300",
                swatchClass: "bg-accent-500",
                data: readings.per_day,
              },
            ]}
          />
        )}
      </Panel>
    </div>
  );
}

export function ConsultationOversightPanel({ consultations, loading }) {
  const items = consultations?.items || [];

  return (
    <Panel title="Consultation Oversight" subtitle="Every guidance thread on the platform, newest first">
      {loading ? (
        <SkeletonRow lines={3} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={ChatIcon}
          title="No consultations yet"
          description="Seeker guidance threads will appear here."
        />
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.slice(0, 8).map((consultation) => (
            <li
              key={consultation.id}
              className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-3 transition hover:bg-slate-50/60"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-800">{consultation.topic}</p>
                <p className="mt-0.5 truncate text-xs text-slate-500">
                  {new Date(consultation.created_at).toLocaleString()}
                  {consultation.guidance ? " · counsel dispatched" : " · awaiting counsel"}
                </p>
              </div>
              <Badge
                tone={
                  consultation.status === "resolved"
                    ? "emerald"
                    : consultation.status === "open"
                      ? "accent"
                      : "blue"
                }
              >
                {CONSULTATION_STATUS_LABELS[consultation.status] || consultation.status}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function ReadingOversightPanel({ readings, loading }) {
  const [filter, setFilter] = useState("all");
  const items = (readings?.items || []).filter((reading) =>
    filter === "all" ? true : reading.type === filter
  );

  return (
    <Panel
      title="Platform Reading Oversight"
      subtitle="Every divination across the platform, with its owner — open one to inspect it"
      action={
        <div role="group" aria-label="Oversight reading filter" className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100/80 p-0.5">
          {OVERSIGHT_FILTERS.map((option) => {
            const active = filter === option.value;
            return (
              <button
                key={option.value}
                type="button"
                aria-pressed={active}
                onClick={() => setFilter(option.value)}
                className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                  active ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      }
    >
      {loading ? (
        <div className="space-y-3 py-2">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={FileTextIcon}
          title="No readings on the platform"
          description="Reading activity across all accounts will appear here."
        />
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.slice(0, 10).map((reading) => (
            <li key={reading.id}>
              <Link
                href={`/readings/${reading.id}`}
                className="-mx-2 flex flex-col justify-between gap-2 rounded-xl px-3 py-3 transition group hover:bg-slate-50/80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:flex-row sm:items-center"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-semibold text-slate-800 transition group-hover:text-primary-700">
                      {reading.title}
                    </p>
                    <Badge tone={reading.type === "palm" ? "primary" : "accent"}>{reading.type}</Badge>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-slate-500">
                    {reading.owner_email || reading.user_id} ·{" "}
                    {new Date(reading.created_at).toLocaleString()}
                    {reading.reviewed_by ? " · reviewed" : ""}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2 self-end sm:self-auto">
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
  );
}

export function SystemStatusPanel({ health, error }) {
  return (
    <Panel title="System Status" subtitle="Live health of the platform's core services">
      {error ? (
        <p className="text-sm text-rose-700">Health check failed: {error.message}</p>
      ) : !health ? (
        <SkeletonRow lines={3} />
      ) : (
        <div className="space-y-3">
          <StatusRow
            label="API"
            detail={health.status === "ok" ? "Operational" : "Degraded"}
            ok={health.status === "ok"}
          />
          <StatusRow
            label="Database"
            detail={health.database === "ok" ? "Operational" : "Unavailable"}
            ok={health.database === "ok"}
          />
          <StatusRow
            label="AI Engine"
            detail={health.ai_provider === "configured" ? "Configured" : "Not configured"}
            ok={health.ai_provider === "configured"}
            warn={health.ai_provider !== "configured"}
          />
          <p className="pt-1 text-xs text-slate-400">
            Environment: {health.environment} · Version: {health.version}
          </p>
        </div>
      )}
    </Panel>
  );
}

function StatusRow({ label, detail, ok, warn = false }) {
  const dotClass = ok ? "bg-emerald-500" : warn ? "bg-slate-300" : "bg-rose-500";
  const detailClass = ok ? "text-emerald-700" : warn ? "text-slate-500" : "text-rose-700";
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2">
      <span className="flex items-center gap-2.5 text-sm font-medium text-slate-700">
        <span className={`h-2 w-2 rounded-full ${dotClass}`} aria-hidden="true" />
        {label}
      </span>
      <span className={`text-xs font-semibold ${detailClass}`}>{detail}</span>
    </div>
  );
}
