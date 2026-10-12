// Guidance Effectiveness (FR-037, "guidance effectiveness").
import { useMemo } from "react";
import { Bar, Line } from "react-chartjs-2";
import { Panel, SkeletonRow } from "@/components/ui";
import { ChartIcon, TargetIcon } from "@/components/icons";
import {
  ChartFrame,
  ChartSkeleton,
  SectionError,
  SourceBadge,
  GuidanceDisclaimer,
} from "@/components/consultant/shared";
import { MeterBar } from "@/components/dashboards/shared";
import { CHART_COLORS, barChartOptions, lineChartOptions } from "@/lib/chartjs";

function OverallScore({ value, source }) {
  return (
    <div className="flex flex-col items-start gap-4 rounded-3xl border border-primary-100 bg-primary-50/50 p-6 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-primary-700">
          Overall guidance effectiveness
        </p>
        <p className="mt-2 font-display text-5xl tracking-tight text-slate-900">
          {Math.round(value * 100)}%
        </p>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-600">
          The share of your guidance threads that reached a resolution. A platform analytics
          metric — not a measure of any individual client&rsquo;s outcome.
        </p>
      </div>
      <span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white text-primary-600 shadow-xs ring-1 ring-primary-100">
        <TargetIcon className="h-7 w-7" />
      </span>
      <SourceBadge source={source} />
    </div>
  );
}

export default function GuidanceEffectiveness({ data, loading = false, error = null, onRetry }) {
  const breakdown = data?.breakdown || [];
  const overTime = data?.overTime || [];
  const areas = data?.guidanceAreas || [];

  const overTimeData = useMemo(() => {
    const rows = data?.overTime || [];
    if (rows.length === 0) return null;
    return {
      labels: rows.map((point) => point.period),
      datasets: [
        {
          label: "Effectiveness",
          data: rows.map((point) => point.value),
          borderColor: CHART_COLORS[2],
          backgroundColor: "rgba(245, 158, 11, 0.12)",
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: "#ffffff",
          pointBorderColor: CHART_COLORS[2],
        },
      ],
    };
  }, [data]);

  const areasData = useMemo(() => {
    const rows = data?.guidanceAreas || [];
    if (rows.length === 0) return null;
    return {
      labels: rows.map((item) => item.area),
      datasets: [
        {
          label: "Consultations",
          data: rows.map((item) => item.count),
          backgroundColor: CHART_COLORS[0],
          borderRadius: 8,
          maxBarThickness: 34,
        },
      ],
    };
  }, [data]);

  const areaBarOptions = useMemo(
    () => ({
      ...barChartOptions({ unit: "" }),
      scales: {
        y: {
          min: 0,
          ticks: { color: "#64748b", font: { size: 11 } },
          grid: { color: "rgba(148, 163, 184, 0.2)" },
        },
        x: { ticks: { color: "#64748b", font: { size: 11 } }, grid: { display: false } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          backgroundColor: "#0f172a",
          padding: 10,
          cornerRadius: 10,
        },
      },
    }),
    []
  );

  return (
    <div className="space-y-5">
      {error ? (
        <SectionError title="Unable to load guidance effectiveness." onRetry={onRetry} />
      ) : (
        <OverallScore value={data?.overall ?? 0} source={data?.live ? "live" : "demo"} />
      )}

      <Panel
        title="Effectiveness by guidance area"
        subtitle="How each type of counsel you give resolves"
        action={<SourceBadge source="demo" />}
      >
        {loading ? (
          <SkeletonRow lines={4} />
        ) : breakdown.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-400">No breakdown available yet.</p>
        ) : (
          <ul className="space-y-4">
            {breakdown.map((row) => (
              <li key={row.area}>
                <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
                  <span className="font-medium text-slate-600">
                    {row.area}
                    <span className="ml-2 text-slate-400">{row.sessions} sessions</span>
                  </span>
                  <span className="font-bold text-slate-900">{Math.round(row.value * 100)}%</span>
                </div>
                <MeterBar value={row.value} tone="emerald" label={`${row.area} effectiveness`} />
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel
          title="Effectiveness over time"
          subtitle="Rolling share of resolved guidance threads"
          action={<SourceBadge source="demo" />}
        >
          {loading ? (
            <ChartSkeleton />
          ) : overTimeData ? (
            <ChartFrame height="h-72">
              <Line data={overTimeData} options={lineChartOptions({ max: 1 })} />
            </ChartFrame>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-10 text-center">
              <ChartIcon className="h-6 w-6 text-slate-400" />
              <p className="mt-3 text-sm font-medium text-slate-900">Not enough history yet</p>
              <p className="mt-1 max-w-xs text-sm text-slate-500">
                The trend line fills in as more of your consultations close.
              </p>
            </div>
          )}
        </Panel>

        <Panel
          title="Most common guidance areas"
          subtitle="Where your consultations concentrate"
          action={<SourceBadge source="demo" />}
        >
          {loading ? (
            <ChartSkeleton />
          ) : areasData ? (
            <ChartFrame height="h-72">
              <Bar data={areasData} options={areaBarOptions} />
            </ChartFrame>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-10 text-center">
              <ChartIcon className="h-6 w-6 text-slate-400" />
              <p className="mt-3 text-sm font-medium text-slate-900">No guidance areas yet</p>
              <p className="mt-1 max-w-xs text-sm text-slate-500">
                Categories appear once your consultations start closing.
              </p>
            </div>
          )}
        </Panel>
      </div>

      <GuidanceDisclaimer>
        These are platform analytics about your own consultation workload. They describe patterns
        in sessions you delivered, not predictions about any client, and should not be read as
        clinical, financial or outcome guarantees.
      </GuidanceDisclaimer>
    </div>
  );
}
