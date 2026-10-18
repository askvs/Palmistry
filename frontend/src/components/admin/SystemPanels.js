// System & configuration panels for the administrator (FR-038, §49.3).
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
import { MeterBar, StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  adminAuthSettings,
  adminGenerateSystemReport,
  adminPerformance,
  adminPermissions,
  adminSystemConfig,
} from "@/services/roles";
import {
  ActivityIcon,
  AlertIcon,
  ChartIcon,
  ClockIcon,
  DownloadIcon,
  FileTextIcon,
  LayoutGridIcon,
  SettingsIcon,
  ShieldIcon,
} from "@/components/icons";

const ROLE_LABELS = {
  user: "Seeker",
  tarot_reader: "Tarot Reader",
  spiritual_consultant: "Spiritual Consultant",
  admin: "Administrator",
};

function RolePill({ role }) {
  const tone =
    role === "admin" ? "rose" : role === "spiritual_consultant" ? "emerald" : role === "tarot_reader" ? "accent" : "primary";
  return <Badge tone={tone}>{ROLE_LABELS[role] || role}</Badge>;
}

// A live health indicator line: dot + service name + real check result.
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

export function PermissionsPanel() {
  const { data, error, loading } = useAsyncData(adminPermissions);
  return (
    <Panel
      title="Access & Permissions"
      subtitle="The enforced RBAC matrix (§49.3) — the backend stays authoritative"
    >
      {loading ? (
        <SkeletonRow lines={5} />
      ) : error ? (
        <ErrorState message={error.message} />
      ) : !data ? (
        <EmptyState
          icon={ShieldIcon}
          title="No permission data available"
          description="The permission matrix could not be loaded."
        />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Platform roles:</span>
            {data.roles.map((role) => (
              <RolePill key={role} role={role} />
            ))}
          </div>

          <ul className="divide-y divide-slate-100">
            {data.rules.map((rule) => (
              <li key={rule.name} className="py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <code className="rounded-md bg-primary-50 px-2 py-0.5 font-mono text-xs font-semibold text-primary-700">
                    {rule.name}
                  </code>
                  {rule.allowed.map((role) => (
                    <RolePill key={role} role={role} />
                  ))}
                </div>
                <ul className="mt-1.5 space-y-0.5 pl-1">
                  {rule.surfaces.map((surface) => (
                    <li key={surface} className="text-xs text-slate-500">
                      · {surface}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>

          <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            {data.notes.map((note) => (
              <li key={note} className="text-xs text-slate-500">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}

export function AuthSettingsPanel() {
  const { data, error, loading } = useAsyncData(adminAuthSettings);

  if (loading) return <SkeletonRow lines={6} />;
  if (error) return <ErrorState message={error.message} />;
  if (!data) return null;

  const rows = [
    { label: "Signing algorithm", value: data.jwt_algorithm },
    { label: "Access token lifetime", value: `${data.access_token_expire_minutes} minutes` },
    { label: "Refresh token lifetime", value: `${data.refresh_token_expire_days} days` },
    { label: "Refresh cookie", value: `${data.refresh_cookie_name} (${data.refresh_cookie_samesite}, ${data.refresh_cookie_secure ? "secure" : "insecure"})` },
    { label: "Cookie path", value: data.refresh_cookie_path },
    { label: "Password hashing", value: data.password_hashing },
    { label: "OAuth2 providers", value: data.oauth_providers.length ? data.oauth_providers.join(", ") : "none configured" },
    { label: "OAuth2 credentials", value: data.oauth_configured.length ? `${data.oauth_configured.join(", ")} ready` : "not configured" },
    { label: "Admin self-signup", value: data.admin_signup_requires_invite_code ? "invite code required" : "open" },
    { label: "Auth rate limit", value: `${data.rate_limits.auth_requests_per_minute} req/min per IP` },
    { label: "Allowed origins", value: data.cors_origins.join(", ") },
  ];

  return (
    <Panel
      title="Authentication & Security Settings"
      subtitle="Token policy, session cookies and access controls — secrets are never returned"
    >
      <div className="space-y-4">
        <ul className="divide-y divide-slate-100">
          {rows.map((row) => (
            <li key={row.label} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
              <span className="text-sm font-medium text-slate-700">{row.label}</span>
              <span className="text-xs font-semibold text-slate-900">{row.value}</span>
            </li>
          ))}
        </ul>
        <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
          {data.notes.map((note) => (
            <li key={note} className="text-xs text-slate-500">
              {note}
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

export function SystemConfigPanel() {
  const { data, error, loading } = useAsyncData(adminSystemConfig);

  if (loading) return <SkeletonRow lines={7} />;
  if (error) return <ErrorState message={error.message} />;
  if (!data) return null;

  const uptimeHours = (data.uptime_seconds / 3600).toFixed(1);

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Environment"
          value={data.environment}
          tone="primary"
          icon={LayoutGridIcon}
          hint={data.app_name}
        />
        <StatCard
          label="Release"
          value={`v${data.version}`}
          tone="accent"
          icon={FileTextIcon}
          hint={`Migration ${data.migration_revision || "unknown"}`}
        />
        <StatCard
          label="Uptime"
          value={`${uptimeHours} h`}
          tone="emerald"
          icon={ActivityIcon}
          hint={`Since ${new Date(data.started_at).toLocaleString()}`}
        />
        <StatCard
          label="AI Provider"
          value={data.ai_provider === "none" ? "Rule-based" : data.ai_provider}
          tone="blue"
          icon={ChartIcon}
          hint={data.ai_model}
        />
      </div>

      <Panel
        title="System Configuration"
        subtitle="Deployment-shaped view of the running process — read from the environment"
      >
        <div className="space-y-4">
          <ul className="divide-y divide-slate-100">
            {[
              { label: "API prefix", value: data.api_prefix },
              { label: "API docs", value: data.docs_url },
              { label: "Database target", value: data.database_target },
              { label: "Migration revision", value: data.migration_revision || "unknown" },
              { label: "AI provider / model", value: `${data.ai_provider} · ${data.ai_model}` },
              { label: "AI credentials", value: data.ai_configured ? "configured" : "not configured (rule-based fallback)" },
              { label: "Email delivery", value: data.email_configured ? "SMTP configured" : "not configured" },
              { label: "SMS delivery", value: data.sms_configured ? "configured" : "not configured" },
              { label: "Maximum upload", value: `${data.max_upload_size_mb} MB · ${data.allowed_image_types.join(", ")}` },
              { label: "Stored timezone", value: data.timezone },
            ].map((row) => (
              <li key={row.label} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                <span className="text-sm font-medium text-slate-700">{row.label}</span>
                <span className="text-xs font-semibold text-slate-900">{row.value}</span>
              </li>
            ))}
          </ul>

          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
              Background schedulers
            </p>
            <ul className="space-y-2">
              {data.schedulers.map((scheduler) => (
                <li
                  key={scheduler.name}
                  className="rounded-xl border border-slate-100 bg-slate-50/60 p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize text-slate-700">
                      {scheduler.name}
                    </span>
                    <Badge tone={scheduler.running ? "emerald" : "rose"}>
                      {scheduler.running ? "Running" : "Stopped"}
                    </Badge>
                  </div>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {scheduler.jobs.map((job) => (
                      <li key={job.id}>
                        <Badge tone={job.registered ? "blue" : "slate"}>
                          {job.id.replace(/_/g, " ")}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </div>

          <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            {data.notes.map((note) => (
              <li key={note} className="text-xs text-slate-500">
                {note}
              </li>
            ))}
          </ul>
        </div>
      </Panel>
    </div>
  );
}

export function PerformancePanel() {
  const { data, error, loading } = useAsyncData(adminPerformance);

  if (loading) return <SkeletonRow lines={5} />;
  if (error) return <ErrorState message={error.message} />;
  if (!data) return null;

  const minutes = Math.max(data.uptime_seconds / 60, 1 / 60);

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Requests Handled"
          value={data.requests_total.toLocaleString()}
          tone="primary"
          icon={ActivityIcon}
          hint="Since this process started"
        />
        <StatCard
          label="Requests / minute"
          value={data.requests_per_minute.toFixed(1)}
          tone="blue"
          icon={ChartIcon}
          hint="Averaged over the process uptime"
        />
        <StatCard
          label="Error Rate"
          value={`${(data.error_rate * 100).toFixed(2)}%`}
          tone={data.error_rate > 0.01 ? "rose" : "emerald"}
          icon={AlertIcon}
          hint="Share of requests that returned 5xx"
        />
        <StatCard
          label="p95 Latency"
          value={`${data.latency_ms.p95} ms`}
          tone="accent"
          icon={ClockIcon}
          hint={`Median ${data.latency_ms.p50} ms · max ${data.latency_ms.max} ms`}
        />
      </div>

      <Panel
        title="Slowest Routes"
        subtitle="Grouped by request path, averaged since the process started"
      >
        {data.slowest_routes.length === 0 ? (
          <EmptyState
            icon={ChartIcon}
            title="No traffic recorded yet"
            description="Route latency appears once the API serves requests."
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {data.slowest_routes.map((route) => (
              <li key={route.path} className="-mx-2 rounded-lg px-2 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="truncate font-mono text-xs font-medium text-slate-700">
                    {route.path}
                  </span>
                  <span className="text-xs font-bold text-slate-900">
                    avg {route.avg_ms} ms · max {route.max_ms} ms
                  </span>
                </div>
                <div className="mt-1.5">
                  <MeterBar
                    value={Math.min(route.avg_ms / Math.max(data.latency_ms.max, 1), 1)}
                    tone={route.avg_ms > 1000 ? "rose" : "primary"}
                    label={`Average latency for ${route.path}`}
                  />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {route.count} request{route.count === 1 ? "" : "s"} · error rate{" "}
                  {(route.error_rate * 100).toFixed(1)}% · {minutes.toFixed(0)} min of uptime
                </p>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <ul className="space-y-1 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
        {data.notes.map((note) => (
          <li key={note} className="text-xs text-slate-500">
            {note}
          </li>
        ))}
      </ul>
    </div>
  );
}

// System report generation is an audited mutation, so it lives in a panel.
export function SystemReportsPanel() {
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);
  const [actionError, setActionError] = useState(null);
  const toast = useToast();

  async function generate() {
    setBusy(true);
    setActionError(null);
    try {
      const created = await adminGenerateSystemReport();
      setReport(created);
      toast.success("Report generated", "The platform audit report is ready to download.");
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function download() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const stamp = String(report.generated_at || new Date().toISOString()).slice(0, 10);
    link.download = `palmistry-system-report-${stamp}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function downloadCsv() {
    if (!report) return;
    const platform = report.payload?.platform || {};
    const readings = report.payload?.readings || {};
    const lines = [
      "section,metric,value",
      `platform,users_total,${platform.users_total ?? ""}`,
      `platform,users_active,${platform.users_active ?? ""}`,
      `platform,readings_total,${platform.readings_total ?? ""}`,
      `platform,consultations_total,${platform.consultations_total ?? ""}`,
      `readings,total,${readings.total ?? ""}`,
      `readings,reviewed_total,${readings.reviewed_total ?? ""}`,
      ...(Array.isArray(readings.by_type)
        ? readings.by_type.map((r) => `readings_by_type,${r.type},${r.count}`)
        : []),
      ...(Array.isArray(readings.by_status)
        ? readings.by_status.map((r) => `readings_by_status,${r.status},${r.count}`)
        : []),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const stamp = String(report.generated_at || new Date().toISOString()).slice(0, 10);
    link.download = `palmistry-system-report-${stamp}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <Panel
      title="System Reports"
      subtitle="Platform diagnostics snapshots, generated on demand and audited"
      action={
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={ActivityIcon}
            loading={busy}
            onClick={generate}
          >
            Run platform diagnostics
          </Button>
          {report && (
            <>
              <Button variant="secondary" size="sm" icon={DownloadIcon} onClick={download}>
                Download JSON
              </Button>
              <Button variant="ghost" size="sm" icon={DownloadIcon} onClick={downloadCsv}>
                Download CSV
              </Button>
            </>
          )}
        </div>
      }
    >
      {actionError && <InlineError message={actionError} />}
      {!report ? (
        <EmptyState
          icon={FileTextIcon}
          title="No report generated yet"
          description="Run platform diagnostics to snapshot current analytics."
        />
      ) : (
        <div className="space-y-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            <span className="font-medium text-slate-700">Generated at</span>
            <span className="text-xs text-slate-500">
              {new Date(report.generated_at).toLocaleString()}
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
              <p className="text-xs font-medium text-slate-500">Accounts</p>
              <p className="mt-0.5 text-lg font-bold text-slate-900">
                {report.payload?.platform?.users_total ?? "—"}
              </p>
              <p className="text-xs text-slate-500">
                {report.payload?.platform?.users_active ?? 0} active
              </p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
              <p className="text-xs font-medium text-slate-500">Divinations</p>
              <p className="mt-0.5 text-lg font-bold text-slate-900">
                {report.payload?.platform?.readings_total ?? "—"}
              </p>
              <p className="text-xs text-slate-500">
                {report.payload?.readings?.reviewed_total ?? 0} reviewed by a reader
              </p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
              <p className="text-xs font-medium text-slate-500">Consultations</p>
              <p className="mt-0.5 text-lg font-bold text-slate-900">
                {report.payload?.platform?.consultations_total ?? "—"}
              </p>
              <p className="text-xs text-slate-500">Guidance threads on platform</p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
              <p className="text-xs font-medium text-slate-500">Signups (7d)</p>
              <p className="mt-0.5 text-lg font-bold text-slate-900">
                {report.payload?.platform?.signups_in_period ?? "—"}
              </p>
              <p className="text-xs text-slate-500">
                Prev. period: {report.payload?.platform?.signups_previous_period ?? 0}
              </p>
            </div>
          </div>
          {Array.isArray(report.payload?.readings?.by_type) && report.payload.readings.by_type.length > 0 && (
            <div className="rounded-xl border border-slate-100 bg-white p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Readings by type
              </p>
              <ul className="flex flex-wrap gap-2">
                {report.payload.readings.by_type.map((row) => (
                  <li key={row.type} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {row.type}: {row.count}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {Array.isArray(report.payload?.readings?.by_status) && report.payload.readings.by_status.length > 0 && (
            <div className="rounded-xl border border-slate-100 bg-white p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Readings by status
              </p>
              <ul className="flex flex-wrap gap-2">
                {report.payload.readings.by_status.map((row) => (
                  <li key={row.status} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {row.status}: {row.count}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
