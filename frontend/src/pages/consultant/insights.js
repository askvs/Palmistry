// Guidance insights: effectiveness, breakdowns, and consultation feed.
import { ChartIcon, TargetIcon } from "@/components/icons";
import Seo from "@/components/Seo";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { Button, PageHeader } from "@/components/ui";
import {
  fetchConsultationInsightFeed,
  fetchGuidanceEffectiveness,
} from "@/services/consultant";
import GuidanceEffectiveness from "@/components/consultant/GuidanceEffectiveness";
import ConsultationInsights from "@/components/consultant/ConsultationInsights";
import { SectionError } from "@/components/consultant/shared";

export default function ConsultantInsightsPage() {
  const { user, loading: authLoading } = useAuth();
  const { data, error, loading, refresh } = useAsyncData(fetchGuidanceEffectiveness, {
    enabled: !authLoading && !!user,
  });
  const { data: insightData, error: insightError, loading: insightLoading, refresh: refreshInsights } =
    useAsyncData(fetchConsultationInsightFeed, { enabled: !authLoading && !!user });

  return (
    <div className="animate-fade-in space-y-8">
      <Seo
        title="Insights"
        description="How effective your guidance is, where your consultations concentrate, and the patterns across your sessions."
      />

      <PageHeader
        icon={TargetIcon}
        tileTone="emerald"
        eyebrow="Spiritual Consultant"
        title="Guidance Insights"
        description="How effective your guidance is, where your consultations concentrate, and the patterns the platform has noticed across your sessions."
        actions={
          <Button
            variant="secondary"
            icon={ChartIcon}
            onClick={() => {
              refresh();
              refreshInsights();
            }}
            loading={loading || insightLoading}
          >
            Refresh
          </Button>
        }
      />

      {error && <SectionError title="Unable to load effectiveness." onRetry={refresh} />}

      <GuidanceEffectiveness
        data={data}
        loading={loading}
        error={error?.message || null}
        onRetry={refresh}
      />

      <ConsultationInsights
        items={insightData?.items || []}
        source={insightData?.source}
        trends={insightData?.trends}
        loading={insightLoading}
        error={insightError?.message || null}
        onRetry={refreshInsights}
      />
    </div>
  );
}
