// Administrative audit trail (§49.3: audit logs).
import { useCallback } from "react";
import {
  Badge,
  EmptyState,
  ErrorState,
  Panel,
  SkeletonRow,
} from "@/components/ui";
import { useAsyncData } from "@/hooks/useAsyncData";
import { adminListAuditLogs } from "@/services/roles";
import { ShieldIcon } from "@/components/icons";

const ACTION_TONES = {
  "user.update": "primary",
  "report.generate": "accent",
  "error.acknowledge": "blue",
};

export default function AuditLogPanel({ limit = 100 }) {
  const loader = useCallback(() => adminListAuditLogs(limit), [limit]);
  const { data, error, loading } = useAsyncData(loader);
  const items = data?.items || [];

  return (
    <Panel
      title="Administrative Security Audit Log"
      subtitle="Chronicle of administrative overrides, role updates and system operations"
    >
      {loading ? (
        <div className="py-2">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : error ? (
        <ErrorState message={error.message} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={ShieldIcon}
          title="No security actions recorded yet"
          description="Administrative overrides, role updates and system operations appear here."
        />
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map((entry) => (
            <li key={entry.id} className="-mx-2 rounded-lg px-2 py-2.5 transition hover:bg-slate-50/60">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <Badge tone={ACTION_TONES[entry.action] || "slate"}>{entry.action}</Badge>
                <span className="min-w-0 flex-1 truncate text-[13px] text-slate-600">{entry.target}</span>
                <span className="text-[12.5px] font-medium text-slate-500">
                  {entry.actor_email || "system"}
                </span>
                <span className="shrink-0 text-[12.5px] tabular-nums text-slate-500">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
              </div>
              {entry.detail && (
                <p className="mt-1 pl-1 text-[12.5px] leading-relaxed text-slate-500">{entry.detail}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
