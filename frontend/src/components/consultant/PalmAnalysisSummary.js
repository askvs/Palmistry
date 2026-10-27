// Client Palm Analysis summary.
import { Badge, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import { HandIcon } from "@/components/icons";
import { SectionError, SourceBadge, GuidanceDisclaimer } from "@/components/consultant/shared";
import { MeterBar } from "@/components/dashboards/shared";
import { formatDate } from "@/lib/format";

const STATUS_META = {
  analyzed: { label: "Analyzed", tone: "emerald" },
  partial: { label: "Partial", tone: "accent" },
  pending: { label: "Not analysed", tone: "slate" },
};

function PalmFeatureRow({ feature }) {
  const meta = STATUS_META[feature.status] || STATUS_META.pending;
  return (
    <li className="surface-card hover-lift p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary-50 text-primary-600 ring-1 ring-primary-100">
            <HandIcon className="h-4 w-4" />
          </span>
          <h4 className="text-sm font-semibold text-slate-900">{feature.label}</h4>
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
      </div>

      <p className="mt-2.5 text-sm leading-relaxed text-slate-700">{feature.insight}</p>

      {feature.status !== "pending" && (
        <div className="mt-3 flex items-center gap-3">
          <span className="w-20 shrink-0 text-[11px] font-medium text-slate-500">Confidence</span>
          <MeterBar
            value={(feature.confidence || 0) / 100}
            tone="primary"
            label={`${feature.label} confidence`}
          />
          <span className="w-9 text-right text-[11px] font-bold text-slate-700 tabular-nums">
            {feature.confidence}%
          </span>
        </div>
      )}
    </li>
  );
}

export default function PalmAnalysisSummary({
  palm,
  source,
  loading = false,
  error = null,
  onRetry,
}) {
  const features = palm?.features || [];

  const body = () => {
    if (error) {
      return <SectionError title="Unable to load palm analysis." onRetry={onRetry} />;
    }
    if (loading) {
      return (
        <div className="space-y-3">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      );
    }
    if (!palm || features.length === 0) {
      return (
        <EmptyState
          icon={HandIcon}
          title="No palm analysis available"
          description="This client has not completed a palm scan yet, or the analysis is not shared with consultants."
        />
      );
    }
    return (
      <>
        <p className="mb-4 text-xs text-slate-500 tabular-nums">
          {features.filter((feature) => feature.status === "analyzed").length} of {features.length}{" "}
          features analysed
          {palm.analyzedAt ? ` · last scan ${formatDate(palm.analyzedAt)}` : ""}
        </p>
        <ul className="grid gap-3 lg:grid-cols-2">
          {features.map((feature) => (
            <PalmFeatureRow key={feature.key} feature={feature} />
          ))}
        </ul>
      </>
    );
  };

  return (
    <Panel
      title="Palm Analysis"
      subtitle="Classical read points captured for this client"
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-4">
        {body()}
        <GuidanceDisclaimer>
          Palm features are interpreted for self-reflection. A detected line is a symbolic reading
          of an image, not a medical finding or a forecast.
        </GuidanceDisclaimer>
      </div>
    </Panel>
  );
}
