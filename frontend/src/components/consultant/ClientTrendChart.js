// Client Trend Analysis (FR-037, "user trend analysis").
import { useMemo } from "react";
import { Line } from "react-chartjs-2";
import { CHART_COLORS, lineChartOptions } from "@/lib/chartjs";
import { Panel } from "@/components/ui";
import {
  ChartFrame,
  ChartSkeleton,
  ClientAvatar,
  ConsultantSelect,
  EmptyState,
  SectionError,
  SourceBadge,
} from "@/components/consultant/shared";
import { ChartIcon, TrendingUpIcon } from "@/components/icons";

const WINDOW_LABELS = {
  "7d": "Last 7 days",
  "30d": "Last 30 days",
  "6m": "Last 6 months",
  "1y": "1 year",
};

function formatAxisLabel(dateValue, windowValue) {
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return "";
  if (windowValue === "7d") {
    return date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric" });
  }
  if (windowValue === "30d") {
    return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  }
  return date.toLocaleDateString("en-GB", { month: "short" });
}

// Signed percentage-point change between the first and last point.
function deltaOf(points = []) {
  if (points.length < 2) return null;
  const first = points[0].value;
  const last = points[points.length - 1].value;
  return last - first;
}

export default function ClientTrendChart({
  series,
  loading = false,
  error = null,
  onRetry,
  filters,
  onFiltersChange,
  clientOptions = [],
  categoryOptions = [],
  windowOptions = [],
}) {
  const points = series?.points || [];
  const activeWindow = filters?.window || "30d";
  const activeCategory = filters?.category || "overall";
  const categoryLabel =
    categoryOptions.find((option) => option.value === activeCategory)?.label || activeCategory;
  const clientLabel =
    clientOptions.find((option) => option.value === filters?.clientId)?.label || "All clients";

  const chartData = useMemo(() => {
    const rows = series?.points || [];
    if (rows.length === 0) return null;
    return {
      labels: rows.map((point) => formatAxisLabel(point.date, activeWindow)),
      datasets: [
        {
          label: `${clientLabel} · ${categoryLabel}`,
          data: rows.map((point) => point.value),
          borderColor: CHART_COLORS[0],
          backgroundColor: "rgba(124,58,237,0.12)",
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          spanGaps: true,
        },
      ],
    };
  }, [series, activeWindow, clientLabel, categoryLabel]);

  const options = useMemo(() => lineChartOptions({ max: 1 }), []);
  const delta = deltaOf(points);
  const latest = points.length ? points[points.length - 1].value : null;
  const selectedClient = clientOptions.find((option) => option.value === filters?.clientId);

  return (
    <Panel
      title="Client Trend Analysis"
      subtitle="Signal strength across life domains over time, drawn from your clients' readings"
      action={<SourceBadge source={series?.source} />}
    >
      <div className="space-y-5">
        {/* Filters */}
        <div className="flex flex-wrap items-end gap-3 rounded-[16px] border border-slate-100 bg-slate-50/60 p-3.5">
          <label className="min-w-[9rem] flex-1">
            <span className="mb-1 block text-xs font-semibold text-slate-700">
              Client
            </span>
            <ConsultantSelect
              label="Client"
              value={filters?.clientId || "all"}
              onChange={(value) => onFiltersChange?.({ ...filters, clientId: value })}
              options={clientOptions}
              className="w-full"
            />
          </label>

          <label className="min-w-[9rem] flex-1">
            <span className="mb-1 block text-xs font-semibold text-slate-700">
              Category
            </span>
            <ConsultantSelect
              label="Category"
              value={activeCategory}
              onChange={(value) => onFiltersChange?.({ ...filters, category: value })}
              options={categoryOptions}
              className="w-full"
            />
          </label>

          <label className="min-w-[8.5rem] flex-1">
            <span className="mb-1 block text-xs font-semibold text-slate-700">
              Time
            </span>
            <ConsultantSelect
              label="Time range"
              value={activeWindow}
              onChange={(value) => onFiltersChange?.({ ...filters, window: value })}
              options={windowOptions}
              className="w-full"
            />
          </label>
        </div>

        {/* Chart + context */}
        {error ? (
          <SectionError
            title="Unable to load client trends."
            onRetry={onRetry}
          />
        ) : loading && points.length === 0 ? (
          <ChartSkeleton />
        ) : points.length === 0 ? (
          <EmptyState
            icon={ChartIcon}
            title="No trend points yet"
            description="Trends appear once this client has at least two readings in the selected period."
          />
        ) : (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                {selectedClient && selectedClient.value !== "all" && selectedClient.initials && (
                  <ClientAvatar
                    name={selectedClient.label}
                    initials={selectedClient.initials}
                    size="sm"
                  />
                )}
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    Latest signal · {WINDOW_LABELS[activeWindow]}
                  </p>
                  <p className="text-lg font-bold tracking-tight text-slate-900 tabular-nums">
                    {latest == null ? "—" : `${Math.round(latest * 100)}%`}
                    {delta != null && (
                      <span
                        className={`ml-2 text-xs font-semibold ${
                          delta >= 0 ? "text-emerald-600" : "text-rose-600"
                        }`}
                      >
                        {delta >= 0 ? "+" : ""}
                        {Math.round(delta * 100)} pts
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <p className="inline-flex items-center gap-1.5 text-xs text-slate-500">
                <TrendingUpIcon className="h-3.5 w-3.5 text-primary-500" />
                {points.length} point{points.length === 1 ? "" : "s"} · {categoryLabel}
              </p>
            </div>

            <ChartFrame height="h-72">
              <Line data={chartData} options={options} />
            </ChartFrame>

            <p className="text-xs leading-relaxed text-slate-500">
              Scores are relative signal strengths (0–100%), not absolute outcomes. They describe
              the direction and consistency of the themes behind {clientLabel.toLowerCase()}&rsquo;s
              readings for the selected period.
            </p>
          </>
        )}
      </div>
    </Panel>
  );
}
