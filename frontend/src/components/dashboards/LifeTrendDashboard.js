// Life trend summary with chart.js history.
import Link from "next/link";
import { useMemo } from "react";
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { Badge, EmptyState, ErrorState, Panel, SkeletonRow } from "@/components/ui";
import {
  DIRECTION_META,
  InsightList,
  Meter,
  fetchLifeTrends,
} from "@/components/life-trends/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { AlertIcon, ArrowRightIcon, TrendingUpIcon } from "@/components/icons";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler, Legend);

function TrendCard({ trend }) {
  const dir = DIRECTION_META[trend.direction] || DIRECTION_META.stable;
  return (
    <div className="rounded-2xl border border-primary-100 bg-primary-50/50 p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h4 className="font-semibold text-primary-900">{trend.name}</h4>
        <Badge tone={dir.tone}>{dir.label}</Badge>
      </div>
      <div className="mb-2 space-y-1.5 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <span className="w-16 shrink-0">Score</span>
          <Meter value={trend.score} />
          <span className="w-9 text-right font-medium">{Math.round(trend.score * 100)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-16 shrink-0">Strength</span>
          <Meter value={trend.strength} tone="indigo" />
          <span className="w-9 text-right font-medium">{Math.round(trend.strength * 100)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-16 shrink-0">Confidence</span>
          <Meter value={trend.confidence} tone="accent" />
          <span className="w-9 text-right font-medium">{Math.round(trend.confidence * 100)}%</span>
        </div>
      </div>
      <p className="text-sm text-slate-700">{trend.explanation}</p>
      {trend.signals?.length > 0 && (
        <details className="mt-2 text-xs text-slate-500">
          <summary className="cursor-pointer font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600">
            Why this result? ({trend.signals.length} signals)
          </summary>
          <ul className="mt-1 list-inside list-disc space-y-0.5">
            {trend.signals.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function HistoryChart({ history }) {
  const data = useMemo(() => {
    const points = [...(history || [])].sort((a, b) => a.date.localeCompare(b.date));
    return {
      labels: points.map((p) => new Date(p.date).toLocaleDateString()),
      datasets: [
        {
          label: "Overall signal",
          data: points.map((p) => p.overall_signal),
          fill: true,
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.12)",
          pointBackgroundColor: "#8b5cf6",
          pointRadius: 3,
          tension: 0.3,
        },
      ],
    };
  }, [history]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 1, ticks: { color: "#64748b" }, grid: { color: "rgba(148, 163, 184, 0.2)" } },
      x: { ticks: { color: "#64748b" }, grid: { display: false } },
    },
    plugins: {
      legend: {
        display: true,
        labels: { color: "#475569", usePointStyle: true, boxWidth: 8, boxHeight: 8 },
      },
      tooltip: { enabled: true },
    },
  };

  return (
    <div className="h-64">
      <Line data={data} options={options} />
    </div>
  );
}

export default function LifeTrendDashboard() {
  const {
    data: trends,
    error: fetchError,
    loading,
    refresh,
  } = useAsyncData(fetchLifeTrends);
  const error = fetchError
    ? "Could not load your life trend analysis. Please try again later."
    : null;

  if (error) {
    return (
      <Panel title="Life Trend Analysis" subtitle="Signals drawn from your own readings">
        <ErrorState message={error} onRetry={refresh} />
      </Panel>
    );
  }

  if (loading || !trends) {
    return (
      <Panel title="Life Trend Analysis" subtitle="Signals drawn from your own readings">
        <div className="animate-pulse space-y-4" aria-hidden="true">
          <SkeletonRow lines={3} />
          <div className="h-24 rounded-2xl bg-slate-100" />
          <div className="h-64 rounded-2xl bg-slate-100" />
        </div>
      </Panel>
    );
  }

  const coverage = trends.data_coverage || {};
  const hasHistory = (trends.history || []).length >= 2;

  return (
    <Panel
      title="Life Trend Analysis"
      subtitle="Feature-based signals derived from your own readings"
      action={
        <div className="flex flex-wrap items-center gap-3">
          <span
            className="inline-flex cursor-help"
            title="Scores are computed from your own readings — interpretive, not predictions"
          >
            <Badge tone="primary">{coverage.readings_analyzed ?? 0} reading(s) analyzed</Badge>
          </span>
          <Link
            href="/life-trends"
            className="inline-flex items-center gap-1 text-sm font-semibold text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            View full analysis
            <ArrowRightIcon className="h-4 w-4" />
          </Link>
        </div>
      }
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-primary-100 bg-primary-50/50 p-4 md:col-span-2">
            <h3 className="text-lg font-semibold text-primary-900">Life Path</h3>
            <p className="mt-1 text-sm text-slate-700">{trends.life_path}</p>
          </div>
          <div className="rounded-2xl border border-primary-100 bg-primary-50/50 p-4">
            <h3 className="text-lg font-semibold text-primary-900">Growth Potential</h3>
            <p className="mb-2 text-2xl font-bold text-primary-900">
              {Math.round((trends.growth_potential ?? 0) * 100)}%
            </p>
            <Meter value={trends.growth_potential ?? 0} />
          </div>
        </div>

        <section>
          <h3 className="mb-2 text-lg font-semibold text-primary-900">Current Trends</h3>
          {trends.current_trends?.length ? (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {trends.current_trends.map((t) => (
                <TrendCard key={t.domain} trend={t} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={TrendingUpIcon}
              title="No trend signals yet"
              description="Complete a palm or tarot reading to generate real trend signals."
            />
          )}
        </section>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
            <h3 className="mb-2 flex items-center gap-1.5 text-lg font-semibold text-emerald-800">
              <TrendingUpIcon className="h-4 w-4" />
              Opportunities
            </h3>
            <InsightList items={trends.opportunities} tone="emerald" />
          </div>
          <div className="rounded-2xl border border-accent-100 bg-accent-50/70 p-4">
            <h3 className="mb-2 flex items-center gap-1.5 text-lg font-semibold text-accent-800">
              <AlertIcon className="h-4 w-4" />
              Challenges
            </h3>
            <InsightList items={trends.challenges} tone="accent" />
          </div>
        </div>

        {hasHistory && (
          <section className="rounded-2xl border border-primary-100 bg-primary-50/50 p-4">
            <h3 className="mb-2 text-lg font-semibold text-primary-900">Trend Over Time</h3>
            <HistoryChart history={trends.history} />
          </section>
        )}

        <section className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4">
          <h3 className="mb-1 text-lg font-semibold text-slate-900">About this analysis</h3>
          <p className="text-sm text-slate-700">{trends.explanation}</p>
          <p className="mt-2 text-xs text-slate-500">
            Data coverage: {coverage.palm_readings ?? 0} palm · {coverage.tarot_readings ?? 0} tarot ·{" "}
            {coverage.goals_used ?? 0} goal(s) from your profile · completeness{" "}
            {Math.round((coverage.completeness ?? 0) * 100)}%
          </p>
        </section>

        <p className="text-xs text-slate-500">{trends.disclaimer}</p>
      </div>
    </Panel>
  );
}
