// Admin analytics: usage, readings, engagement, and session oversight.
import { useCallback, useState } from "react";
import { PageHeader } from "@/components/ui";
import {
  AnalyticsWindowPicker,
  ConsultationOversightPanel,
  DivinationStatsPanel,
  EngagementPanel,
  GrowthPanel,
  PlatformStatCards,
  ReadingOversightPanel,
  UsersByRolePanel,
} from "@/components/admin/AnalyticsPanels";
import SessionOversightPanel from "@/components/admin/SessionOversightPanel";
import Seo from "@/components/Seo";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  adminListConsultations,
  adminListPlatformReadings,
  adminPlatformAnalytics,
  adminReadingStatistics,
} from "@/services/roles";
import { ChartIcon } from "@/components/icons";

export default function AdminAnalyticsPage() {
  const [days, setDays] = useState(30);

  const platformLoader = useCallback(() => adminPlatformAnalytics(days), [days]);
  const { data: platform, error: platformError, loading } = useAsyncData(platformLoader);

  const readingsLoader = useCallback(() => adminReadingStatistics(days), [days]);
  const { data: readings } = useAsyncData(readingsLoader);

  const oversightLoader = useCallback(() => adminListPlatformReadings(), []);
  const { data: platformReadings } = useAsyncData(oversightLoader);

  const consultationsLoader = useCallback(() => adminListConsultations(), []);
  const { data: consultations } = useAsyncData(consultationsLoader);

  return (
    <div className="space-y-6">
      <Seo
        title="Analytics"
        description="Usage, engagement and reading statistics across the platform, with the read-only view of the live-consultation channel."
      />

      <PageHeader
        icon={ChartIcon}
        eyebrow="Administration"
        title="Platform Analytics"
        description="Usage, engagement and reading statistics, with the read-only view of the platform's live-consultation channel."
      />

      {platformError && (
        <p className="text-sm text-rose-700">Analytics could not be loaded: {platformError.message}</p>
      )}

      <AnalyticsWindowPicker days={days} onChange={setDays} />

      <PlatformStatCards platform={platform} readings={readings} days={days} loading={loading} />

      <div className="grid gap-5 lg:grid-cols-2">
        <UsersByRolePanel platform={platform} loading={loading} />
        <DivinationStatsPanel readings={readings} loading={loading} />
      </div>

      <GrowthPanel platform={platform} readings={readings} days={days} loading={loading} />

      <EngagementPanel platform={platform} readings={readings} loading={loading} />

      <SessionOversightPanel />

      <div className="grid gap-5 lg:grid-cols-2">
        <ConsultationOversightPanel consultations={consultations} loading={!consultations} />
        <ReadingOversightPanel readings={platformReadings} loading={!platformReadings} />
      </div>
    </div>
  );
}
