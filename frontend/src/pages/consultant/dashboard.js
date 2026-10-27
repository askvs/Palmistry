// Spiritual consultant dashboard: client trends, guidance effectiveness, follow-ups.
import { useCallback, useState } from "react";
import { useRouter } from "next/router";
import { Button, ErrorState, PageHeader } from "@/components/ui";
import Seo from "@/components/Seo";
import { StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import {
  ChatIcon,
  ChartIcon,
  ClockIcon,
  CompassIcon,
  TrendingUpIcon,
  UsersIcon,
  TargetIcon,
} from "@/components/icons";
import {
  TREND_CATEGORIES,
  TREND_WINDOWS,
} from "@/services/consultantDemoData";
import {
  CONSULTANT_STATUS_LABELS,
  fetchClientTrendSeries,
  fetchConsultantWorkspace,
} from "@/services/consultant";
import ClientTrendChart from "@/components/consultant/ClientTrendChart";
import UpcomingConsultations from "@/components/consultant/UpcomingConsultations";
import RecentClients from "@/components/consultant/RecentClients";
import StartConsultationDialog from "@/components/consultant/StartConsultationDialog";
import {
  ClientAvatar,
  EmptyState,
  Panel,
  SourceBadge,
  SkeletonRow,
} from "@/components/consultant/shared";
import { formatDuration } from "@/components/dashboards/shared";
import { formatPercent, relativeLabel } from "@/lib/format";

const TREND_FILTERS = { clientId: "all", category: "overall", window: "30d" };

function GuidanceQueuePanel({ queue = null, loading, onOpen }) {
  const items = queue?.items || [];

  return (
    <Panel
      title="Seeker guidance queue"
      subtitle="Live threads waiting on you — open one in the consultation workspace"
      action={<SourceBadge source="live" />}
    >
      {loading ? (
        <div className="space-y-3">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={ChatIcon}
          title="No guidance threads are open right now"
          description="New seeker questions will appear here."
        />
      ) : (
        <ul className="divide-y divide-slate-100 overflow-hidden rounded-[16px] border border-slate-100">
          {items.slice(0, 5).map((thread) => (
            <li
              key={thread.id}
              className="flex flex-wrap items-center gap-3 p-4 transition-colors hover:bg-slate-50/70"
            >
              <ClientAvatar name={thread.topic} size="md" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-900">{thread.topic}</p>
                <p className="truncate text-xs text-slate-500">
                  {CONSULTANT_STATUS_LABELS[thread.status] || thread.status} ·{" "}
                  {relativeLabel(thread.created_at)}
                  {thread.guidance ? " · counsel dispatched" : " · awaiting your reply"}
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onOpen?.(thread.id)}
              >
                Open workspace
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export default function ConsultantDashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const { data, error, loading, refresh } = useAsyncData(fetchConsultantWorkspace);

  const [trendFilters, setTrendFilters] = useState(TREND_FILTERS);
  const trendLoader = useCallback(
    () =>
      fetchClientTrendSeries({
        clientId: trendFilters.clientId,
        category: trendFilters.category,
        window: trendFilters.window,
      }),
    [trendFilters]
  );
  const { data: trendSeries, loading: trendLoading, error: trendError, refresh: refreshTrends } =
    useAsyncData(trendLoader, { enabled: !authLoading });

  const [startOpen, setStartOpen] = useState(false);
  const [startClientId, setStartClientId] = useState("");

  const summary = data?.summary;
  const roster = data?.roster || [];
  const firstName = user?.full_name ? user.full_name.split(" ")[0] : user?.email?.split("@")[0] || "Consultant";

  const clientOptions = [
    {
      value: "all",
      label: `All Clients (${roster.length})`,
      initials: "",
    },
    ...roster
      .filter((client) => !client.profilePending)
      .map((client) => ({
        value: client.id,
        label: client.name,
        initials: client.name
          .split(" ")
          .map((part) => part[0])
          .join("")
          .slice(0, 2),
      })),
  ];

  function openStartDialog(clientId = "") {
    setStartClientId(clientId);
    setStartOpen(true);
  }

  function handleTreated() {
    refresh();
  }

  return (
    <div className="animate-fade-in space-y-8">
      <Seo
        title="Consultant dashboard"
        description="Your sessions, clients and guidance impact at a glance."
      />

      <PageHeader
        icon={CompassIcon}
        tileTone="emerald"
        eyebrow="Spiritual Consultant"
        title={`${data?.greeting || "Welcome"}, ${firstName}`}
        description="Here is an overview of your consultations and client insights. Trends, effectiveness and everything waiting on you, in one place."
        actions={
          <>
            <Button variant="secondary" icon={ChartIcon} href="/consultant/insights">
              Effectiveness
            </Button>
            <Button icon={UsersIcon} onClick={() => router.push("/consultant/clients")}>
              My Clients
            </Button>
          </>
        }
      />

      {error && <ErrorState message={error.message} onRetry={refresh} />}

      {/* Summary cards */}
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Active Clients"
          value={summary ? summary.activeClients : loading ? "—" : 0}
          tone="emerald"
          icon={UsersIcon}
          hint={
            summary && summary.activeClientsLive > 0
              ? `${summary.activeClientsLive} from live guidance threads`
              : "Clients in your workspace"
          }
        />
        <StatCard
          label="Consultations This Month"
          value={summary ? summary.consultationsThisMonth : loading ? "—" : 0}
          tone="primary"
          icon={ChatIcon}
          hint="Guidance threads opened this month"
        />
        <StatCard
          label="Guidance Effectiveness"
          value={
            summary?.guidanceEffectiveness != null
              ? formatPercent(summary.guidanceEffectiveness)
              : loading
                ? "—"
                : "—"
          }
          tone="accent"
          icon={TargetIcon}
          hint="Share of your threads that reached resolution"
        />
        <StatCard
          label="Pending Follow-ups"
          value={summary ? summary.pendingFollowUps : loading ? "—" : 0}
          tone="blue"
          icon={ClockIcon}
          hint={
            summary && summary.awaitingReply > 0
              ? `${summary.awaitingReply} thread(s) awaiting your reply`
              : "No threads waiting on you"
          }
        />
      </div>

      {summary?.avgFirstResponseMinutes != null && (
        <p className="flex items-center gap-1.5 text-xs text-slate-500">
          <TrendingUpIcon className="h-3.5 w-3.5 text-emerald-600" />
          Average first response: {formatDuration(summary.avgFirstResponseMinutes)} — measured from
          real thread messages.
        </p>
      )}

      {/* Client trend analysis */}
      <ClientTrendChart
        series={trendSeries}
        loading={trendLoading}
        error={trendError}
        onRetry={refreshTrends}
        filters={trendFilters}
        onFiltersChange={setTrendFilters}
        clientOptions={clientOptions}
        categoryOptions={TREND_CATEGORIES}
        windowOptions={TREND_WINDOWS}
      />

      {/* Upcoming consultations */}
      <UpcomingConsultations
        sessions={data?.scheduled || []}
        roster={roster}
        source={data?.scheduledSource}
        loading={loading}
        error={null}
        onRetry={refresh}
      />

      {/* Recent clients */}
      <RecentClients
        clients={roster}
        source={data?.source}
        loading={loading}
        error={error}
        onRetry={refresh}
        onStartConsultation={(client) => openStartDialog(client.id)}
        limit={6}
      />

      {/* Live guidance queue */}
      <GuidanceQueuePanel
        queue={data?.queue}
        loading={loading}
        onOpen={(id) => router.push(`/consultant/consultations/${id}`)}
      />

      {startOpen && (
        <StartConsultationDialog
          key={startClientId || "new-session"}
          open
          clients={roster}
          preselectedClientId={startClientId}
          onClose={() => setStartOpen(false)}
          onCreated={() => {
            setStartOpen(false);
            handleTreated();
          }}
        />
      )}
    </div>
  );
}
