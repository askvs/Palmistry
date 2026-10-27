// Admin console overview: counters, engagement, growth, and session oversight.
import { useCallback, useState } from "react";
import AdminSessionOversight from "@/components/admin/SessionOversightPanel";
import AuditLogPanel from "@/components/admin/AuditLogPanel";
import { SystemReportsPanel } from "@/components/admin/SystemPanels";
import {
  AnalyticsWindowPicker,
  ConsultationOversightPanel,
  DivinationStatsPanel,
  EngagementPanel,
  GrowthPanel,
  PlatformStatCards,
  ReadingOversightPanel,
  SystemStatusPanel,
  UsersByRolePanel,
} from "@/components/admin/AnalyticsPanels";
import Seo from "@/components/Seo";
import { InlineError, PageHeader } from "@/components/ui";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  adminListConsultations,
  adminListPlatformReadings,
  fetchAdminOverview,
} from "@/services/roles";
import { ShieldIcon } from "@/components/icons";

export default function AdminOverviewPage() {
  const [days, setDays] = useState(7);
  const overviewLoader = useCallback(() => fetchAdminOverview(days), [days]);
  const { data, error, loading } = useAsyncData(overviewLoader);

  const oversightLoader = useCallback(() => adminListPlatformReadings(), []);
  const { data: platformReadings } = useAsyncData(oversightLoader);

  const consultationsLoader = useCallback(() => adminListConsultations(), []);
  const { data: consultations } = useAsyncData(consultationsLoader);

  return (
    <div className="space-y-6">
      <Seo
        title="Admin"
        description="Administration overview: accounts, divination volume, system health and session activity across the platform."
      />

      <PageHeader
        icon={ShieldIcon}
        eyebrow="Administration"
        title="Platform Overview"
        description="Accounts, divination volume, live-system health and session activity across the platform."
      />

      {error && (
        <InlineError message={error.message} />
      )}

      <AnalyticsWindowPicker days={days} onChange={setDays} />

      <PlatformStatCards
        platform={data?.platform}
        readings={data?.readings}
        days={days}
        loading={loading}
      />

      <div className="grid gap-5 lg:grid-cols-2">
        <UsersByRolePanel platform={data?.platform} loading={loading} />
        <DivinationStatsPanel readings={data?.readings} loading={loading} />
      </div>

      <GrowthPanel platform={data?.platform} readings={data?.readings} days={days} loading={loading} />

      <EngagementPanel platform={data?.platform} readings={data?.readings} loading={loading} />

      <AdminSessionOversight />

      <div className="grid gap-5 lg:grid-cols-2">
        <SystemStatusPanel health={data?.health} />
        <ConsultationOversightPanel consultations={consultations} loading={!consultations} />
      </div>

      <ReadingOversightPanel readings={platformReadings} loading={!platformReadings} />

      <div className="grid gap-5 lg:grid-cols-2">
        <SystemReportsPanel />
        <AuditLogPanel limit={10} />
      </div>
    </div>
  );
}