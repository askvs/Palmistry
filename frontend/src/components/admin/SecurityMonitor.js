// Error & security monitor for the administrator (FR-038).
import { useCallback, useState } from "react";
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
import { PerDayBars, Segmented, StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";import {
  adminAcknowledgeError,
  adminErrorStats,
  adminListErrors,
} from "@/services/roles";
import {
  AlertIcon,
  CheckCircleIcon,
  ClockIcon,
  ShieldIcon,
} from "@/components/icons";
const LEVEL_FILTERS = [
  { value: "", label: "All" },
  { value: "error", label: "Server errors" },
  { value: "security", label: "Security events" },
];

const STATS_FILTERS = [
  { value: "1", label: "24 hours" },
  { value: "168", label: "7 days" },
];

export default function SecurityMonitor() {
  const [level, setLevel] = useState("");
  const [hours, setHours] = useState(24);
  const [busyId, setBusyId] = useState(null);
  const [actionError, setActionError] = useState(null);
  const toast = useToast();

  const listLoader = useCallback(
    () => adminListErrors({ level: level || undefined, limit: 100 }),
    [level],
  );
  const { data: listData, error: listError, loading, refresh } = useAsyncData(listLoader);
  const statsLoader = useCallback(() => adminErrorStats(hours), [hours]);
  const { data: stats } = useAsyncData(statsLoader);

  const items = listData?.items || [];

  async function acknowledge(error) {
    setBusyId(error.id);
    setActionError(null);
    try {
      await adminAcknowledgeError(error.id);
      toast.success("Marked as triaged", "The entry moved out of the unresolved queue.");
      await refresh();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      {actionError && <InlineError message={actionError} />}

      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Unresolved"
          value={stats ? stats.unresolved : loading ? "—" : 0}
          tone="rose"
          icon={AlertIcon}
          hint="Not yet triaged by an administrator"
        />
        <StatCard
          label="Server Errors"
          value={stats ? stats.server_errors_24h : loading ? "—" : 0}
          tone="accent"
          icon={AlertIcon}
          hint={`5xx responses in the last ${hours}h`}
        />
        <StatCard
          label="Auth Failures"
          value={stats ? stats.auth_failures_24h : loading ? "—" : 0}
          tone="blue"
          icon={ShieldIcon}
          hint={`Rejected sign-ins in the last ${hours}h`}
        />
        <StatCard
          label="Logged Events"
          value={stats ? stats.total : loading ? "—" : 0}
          tone="primary"
          icon={ClockIcon}
          hint="Deduplicated rows kept for review"
        />
      </div>

      <Panel
        title="Error & Security Log"
        subtitle="Unhandled failures, rejected authentication and rate-limited requests"
        action={
          <div className="flex flex-wrap items-center gap-2">
            <Segmented
              label="Event level"
              value={level}
              onChange={setLevel}
              options={LEVEL_FILTERS}
            />
            <Segmented
              label="Statistics window"
              value={String(hours)}
              onChange={(value) => setHours(Number(value))}
              options={STATS_FILTERS}
            />
          </div>
        }
      >
        {loading ? (
          <div className="space-y-3 py-2">
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
          </div>
        ) : listError ? (
          <ErrorState message={listError.message} onRetry={refresh} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={CheckCircleIcon}
            title="Nothing to triage"
            description="No server errors or security events have been recorded."
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((entry) => (
              <li
                key={entry.id}
                className="-mx-2 flex flex-col gap-2 rounded-lg px-2 py-3 transition hover:bg-slate-50/60 sm:flex-row sm:items-start sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={entry.level === "security" ? "blue" : "rose"}>
                      {entry.level === "security" ? "Security" : "Error"}
                    </Badge>
                    <Badge tone="slate">{entry.kind.replace(/_/g, " ")}</Badge>
                    <span className="font-mono text-xs font-semibold text-slate-700">
                      {entry.status_code}
                    </span>
                    <span className="truncate text-xs font-medium text-slate-600">
                      {entry.method} {entry.path}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">{entry.message}</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {entry.occurrences} occurrence{entry.occurrences === 1 ? "" : "s"} · last seen{" "}
                    {new Date(entry.last_seen_at).toLocaleString()}
                    {entry.actor_email ? ` · ${entry.actor_email}` : ""}
                    {entry.request_id ? ` · request ${entry.request_id.slice(0, 8)}` : ""}
                  </p>
                </div>

                <div className="shrink-0 self-start">
                  {entry.acknowledged_at ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
                      <CheckCircleIcon className="h-3.5 w-3.5" />
                      Triaged {new Date(entry.acknowledged_at).toLocaleDateString()}
                    </span>
                  ) : (
                    <Button
                      size="sm"
                      variant="secondary"
                      icon={CheckCircleIcon}
                      loading={busyId === entry.id}
                      onClick={() => acknowledge(entry)}
                    >
                      Mark triaged
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <p className="text-xs text-slate-500">
        Entries are deduplicated per (kind, method, path, status, message). The log is
        append-only: triaging records an audit entry and never deletes history.
      </p>
    </div>
  );
}
