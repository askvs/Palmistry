// Admin summary shown on the shared role dashboard.
import { useCallback } from "react";
import Link from "next/link";
import { Button, ErrorState, Panel, SkeletonRow } from "@/components/ui";
import { StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  adminErrorStats,
  adminSessionOversight,
  fetchSystemHealth,
} from "@/services/roles";
import { SystemStatusPanel } from "@/components/admin/AnalyticsPanels";
import SessionOversightPanel from "@/components/admin/SessionOversightPanel";
import AuditLogPanel from "@/components/admin/AuditLogPanel";
import { ActivityIcon, CalendarIcon, ChartIcon, ShieldIcon, UsersIcon } from "@/components/icons";

const CONSOLE_LINKS = [
  {
    href: "/admin/users",
    label: "User Governance",
    description: "Accounts, role assignment and suspensions",
    icon: UsersIcon,
  },
  {
    href: "/admin/analytics",
    label: "Platform Analytics",
    description: "Usage, engagement, reading statistics and sessions",
    icon: ChartIcon,
  },
  {
    href: "/admin/security",
    label: "Security & Errors",
    description: "Operational failures and access attempts",
    icon: ShieldIcon,
  },
  {
    href: "/admin/system",
    label: "System",
    description: "Permissions, authentication, configuration",
    icon: ActivityIcon,
  },
];

export default function AdminDashboard() {
  const overviewLoader = useCallback(() => Promise.all([
    adminSessionOversight(30),
    adminErrorStats(24),
    fetchSystemHealth(),
  ]), []);
  const { data, error, loading } = useAsyncData(overviewLoader);

  const sessions = data?.[0];
  const errorStats = data?.[1];
  const health = data?.[2];

  return (
    <div className="space-y-6">
      {error && <ErrorState message={error.message} />}

      {sessions && (
        <div className="grid gap-5 sm:grid-cols-4">
          <StatCard
            label="Scheduled Sessions"
            value={sessions.total}
            tone="primary"
            icon={CalendarIcon}
            hint="Read-only view of the session channel"
          />
          <StatCard
            label="Confirmed Upcoming"
            value={sessions.upcoming}
            tone="emerald"
            icon={CalendarIcon}
            hint="Accepted sessions yet to start"
          />
          <StatCard
            label="Pending Requests"
            value={sessions.pending_requests}
            tone="accent"
            icon={CalendarIcon}
            hint="Awaiting a consultant's reply"
          />
          <StatCard
            label="Unresolved Errors"
            value={errorStats ? errorStats.unresolved : loading ? "—" : 0}
            tone="rose"
            icon={ShieldIcon}
            hint="Operational entries not yet triaged"
          />
        </div>
      )}

      <Panel
        title="Admin Console"
        subtitle="Every governance surface lives in its own section"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          {CONSOLE_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="group surface-card p-5 transition duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-lift focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-600">
                  <link.icon className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-900 transition group-hover:text-primary-700">
                    {link.label}
                  </p>
                  <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">
                    {link.description}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button href="/admin" icon={ShieldIcon}>
            Open the admin console
          </Button>
          <Button href="/admin/analytics" variant="secondary" icon={ChartIcon}>
            Platform analytics
          </Button>
        </div>
      </Panel>

      {loading && !sessions && <SkeletonRow lines={4} />}

      <SystemStatusPanel health={health} />

      <AuditLogPanel limit={5} />

      <SessionOversightPanel />
    </div>
  );
}
