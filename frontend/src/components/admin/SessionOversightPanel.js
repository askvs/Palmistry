// Read-only session oversight for the administrator (FR-038).
import { useCallback, useState } from "react";
import {
  Badge,
  EmptyState,
  ErrorState,
  Panel,
  SkeletonRow,
} from "@/components/ui";
import { MeterBar, Segmented, StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { adminSessionOversight } from "@/services/roles";
import {
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  UsersIcon,
  VideoIcon,
} from "@/components/icons";

const PERIOD_OPTIONS = [
  { value: "7", label: "7 days" },
  { value: "30", label: "30 days" },
  { value: "90", label: "90 days" },
];

const STATUS_TONES = {
  pending: "accent",
  countered: "accent",
  accepted: "emerald",
  completed: "blue",
  cancelled: "slate",
  rejected: "slate",
};

const STATUS_LABELS = {
  pending: "Awaiting consultant",
  countered: "Awaiting seeker",
  accepted: "Confirmed",
  completed: "Completed",
  cancelled: "Cancelled",
  rejected: "Declined",
};

export default function SessionOversightPanel() {
  const [days, setDays] = useState(30);
  const loader = useCallback(() => adminSessionOversight(days), [days]);
  const { data, error, loading, refresh } = useAsyncData(loader);

  const sessions = data;
  const total = sessions?.total ?? 0;

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Total Sessions"
          value={sessions ? sessions.total : loading ? "—" : 0}
          tone="primary"
          icon={CalendarIcon}
          hint="Every session booked on the platform"
        />
        <StatCard
          label="Confirmed Upcoming"
          value={sessions ? sessions.upcoming : loading ? "—" : 0}
          tone="emerald"
          icon={CheckCircleIcon}
          hint="Accepted sessions that have not started"
        />
        <StatCard
          label="Pending Requests"
          value={sessions ? sessions.pending_requests : loading ? "—" : 0}
          tone="accent"
          icon={ClockIcon}
          hint="Awaiting a consultant's reply"
        />
        <StatCard
          label="Unique Seekers"
          value={sessions ? sessions.unique_seekers : loading ? "—" : 0}
          tone="blue"
          icon={UsersIcon}
          hint="Accounts that booked a session"
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel
          title="Upcoming Sessions"
          subtitle="The next scheduled sessions on the platform — read-only"
        >
          {loading ? (
            <div className="space-y-3 py-2">
              <SkeletonRow lines={3} />
              <SkeletonRow lines={3} />
            </div>
          ) : error ? (
            <ErrorState message={error.message} onRetry={refresh} />
          ) : !sessions || sessions.upcoming_sessions.length === 0 ? (
            <EmptyState
              icon={CalendarIcon}
              title="No scheduled sessions"
              description="Confirmed and pending sessions appear here once seekers start booking."
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {sessions.upcoming_sessions.map((session) => (
                <li key={session.id} className="-mx-2 rounded-lg px-2 py-2.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="truncate text-[13px] font-semibold text-slate-800">
                      {session.subject}
                    </p>
                    <Badge tone={STATUS_TONES[session.status] || "slate"} dot>
                      {STATUS_LABELS[session.status] || session.status}
                    </Badge>
                  </div>
                  <p className="mt-0.5 text-[12.5px] tabular-nums text-slate-500">
                    {session.consultant_name || "Consultant"} ·{" "}
                    {new Date(session.start_time).toLocaleString()} · {session.duration_minutes} min
                  </p>
                  <p className="mt-0.5 flex flex-wrap items-center gap-2 text-[12.5px] text-slate-500">
                    {session.meet_link_booked ? (
                      <span className="inline-flex items-center gap-1">
                        <VideoIcon className="h-3 w-3" />
                        Meet link attached
                      </span>
                    ) : (
                      <span>No meeting link yet</span>
                    )}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title="Session Channel Health"
          subtitle="Who is hosting sessions and how seekers rate them"
        >
          {loading ? (
            <SkeletonRow lines={4} />
          ) : error ? (
            <ErrorState message={error.message} onRetry={refresh} />
          ) : !sessions ? (
            <EmptyState
              icon={CalendarIcon}
              title="No session data available"
              description="Session statistics appear once the first booking is made."
            />
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
                  <p className="text-[12.5px] font-medium text-slate-500">Consultant profiles</p>
                  <p className="mt-0.5 text-lg font-bold tabular-nums text-slate-900">
                    {sessions.consultants_total}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
                  <p className="text-[12.5px] font-medium text-slate-500">Accepting bookings</p>
                  <p className="mt-0.5 text-lg font-bold tabular-nums text-slate-900">
                    {sessions.consultants_accepting}
                  </p>
                </div>
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between text-[12.5px]">
                  <span className="font-medium text-slate-700">Average rating</span>
                  <span className="font-bold tabular-nums text-slate-900">
                    {sessions.avg_rating != null ? `${sessions.avg_rating} / 5` : "No reviews yet"}
                  </span>
                </div>
                <MeterBar
                  value={sessions.avg_rating != null ? sessions.avg_rating / 5 : 0}
                  tone="accent"
                  label="Average session rating out of five"
                />
                <p className="mt-1 text-[12.5px] tabular-nums text-slate-500">
                  {sessions.review_count} review{sessions.review_count === 1 ? "" : "s"} submitted
                </p>
              </div>

              <div className="space-y-2">
                {sessions.by_status.map((row) => (
                  <div key={row.status}>
                    <div className="mb-1 flex items-center justify-between text-[12.5px]">
                      <span className="font-medium text-slate-700">
                        {STATUS_LABELS[row.status] || row.status}
                      </span>
                      <span className="font-bold tabular-nums text-slate-900">
                        {row.count}
                        {total ? ` · ${Math.round((row.count / total) * 100)}%` : ""}
                      </span>
                    </div>
                    <MeterBar
                      value={total ? row.count / total : 0}
                      tone={
                        row.status === "cancelled" || row.status === "rejected" ? "rose" : "primary"
                      }
                      label={`${row.status} share of all sessions`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </Panel>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[12.5px] leading-relaxed text-slate-500">
          Session oversight is read-only: administrators govern accounts, analytics and
          configuration. Booking and hosting belong to readers and consultants.
        </p>
        <Segmented
          label="Session reporting window"
          value={String(days)}
          onChange={(value) => setDays(Number(value))}
          options={PERIOD_OPTIONS}
        />
      </div>
    </div>
  );
}
