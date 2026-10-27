// AI Consultation Insights — insight cards for a client.
import { Panel, SkeletonRow } from "@/components/ui";
import { SparklesIcon } from "@/components/icons";
import {
  AIInsightIcon,
  EmptyState,
  SectionError,
  SourceBadge,
  GuidanceDisclaimer,
} from "@/components/consultant/shared";
import { MeterBar } from "@/components/dashboards/shared";
import { formatDateTime } from "@/lib/format";

export function AIInsightCard({ insight, action }) {
  return (
    <article className="surface-card hover-lift flex flex-col p-4">
      <div className="flex items-start gap-3">
        <AIInsightIcon />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-900">{insight.category}</h4>
            <SourceBadge source="demo" />
          </div>
          <p className="mt-0.5 text-[11px] text-slate-500 tabular-nums">
            {formatDateTime(insight.createdAt)}
            {insight.reviewed ? " · reviewed by you" : ""}
          </p>
        </div>
      </div>

      <p className="mt-3 flex-1 text-sm leading-relaxed text-slate-700">{insight.insight}</p>

      {insight.recommendation && (
        <p className="mt-3 rounded-xl border border-primary-100 bg-primary-50/60 px-3 py-2.5 text-xs leading-relaxed text-primary-900">
          <span className="font-semibold">Reflection point: </span>
          {insight.recommendation}
        </p>
      )}

      <div className="mt-3.5 space-y-1.5">
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-medium text-slate-500">Relevance</span>
          <span className="font-bold text-slate-900 tabular-nums">{insight.relevance}%</span>
        </div>
        <MeterBar
          value={(insight.relevance || 0) / 100}
          tone="primary"
          label={`${insight.category} relevance`}
        />
      </div>

      {action && <div className="mt-3.5">{action}</div>}
    </article>
  );
}

export default function AIConsultationInsights({
  insights = [],
  source,
  loading = false,
  error = null,
  onRetry,
}) {
  const body = () => {
    if (error) {
      return <SectionError title="Unable to load client insights." onRetry={onRetry} />;
    }
    if (loading) {
      return (
        <div className="grid gap-4 sm:grid-cols-2">
          <SkeletonRow lines={4} />
          <SkeletonRow lines={4} />
        </div>
      );
    }
    if (insights.length === 0) {
      return (
        <EmptyState
          icon={SparklesIcon}
          title="No insights generated yet"
          description="Generate insights from a consultation to see AI reflection points for this client."
        />
      );
    }
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {insights.map((insight) => (
          <AIInsightCard key={insight.id} insight={insight} />
        ))}
      </div>
    );
  };

  return (
    <Panel
      title="AI Consultation Insights"
      subtitle="Interpretive reflection points drawn from this client's readings"
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-4">
        {body()}
        <GuidanceDisclaimer />
      </div>
    </Panel>
  );
}
