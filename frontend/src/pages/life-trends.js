// Life trends: momentum, domain history, reading log, and method metadata.
import { useEffect, useMemo } from "react";
import Seo from "@/components/Seo";
import { useRouter } from "next/router";
import { Line } from "react-chartjs-2";
import { CHART_COLORS, lineChartOptions } from "@/lib/chartjs";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  PageHeader,
  Panel,
  SkeletonRow,
  Spinner,
} from "@/components/ui";
import { StatCard } from "@/components/dashboards/shared";
import {
  DIRECTION_META,
  InsightList,
  Meter,
  fetchLifeTrends,
  formatDomainLabel,
} from "@/components/life-trends/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import {
  ActivityIcon,
  AlertIcon,
  ChartIcon,
  CompassIcon,
  FileTextIcon,
  RetryIcon,
  ScanIcon,
  TargetIcon,
  TrendingUpIcon,
} from "@/components/icons";

const LOG_DATE_FORMAT = {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
};

// Momentum bands: |momentum| <= 0.15 counts as steady (recent ≈ baseline).
function momentumMeta(momentum) {
  if (momentum >= 0.15) return { label: "Accelerating", className: "text-emerald-600" };
  if (momentum <= -0.15) return { label: "Cooling", className: "text-rose-600" };
  return { label: "Holding steady", className: "text-slate-500" };
}

function TrendDetailCard({ trend }) {
  const dir = DIRECTION_META[trend.direction] || DIRECTION_META.stable;
  const momentum = trend.momentum ?? 0;
  const meta = momentumMeta(momentum);
  const signed = `${momentum > 0 ? "+" : ""}${momentum.toFixed(2)}`;

  return (
    <div className="rounded-2xl border border-primary-100 bg-primary-50/50 p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-semibold text-primary-900">{trend.name}</h4>
        <Badge tone={dir.tone}>{dir.label}</Badge>
      </div>

      <div className="mb-3 space-y-1.5 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <span className="w-20 shrink-0">Score</span>
          <Meter value={trend.score} />
          <span className="w-10 text-right font-medium tabular-nums">{Math.round(trend.score * 100)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-20 shrink-0">Strength</span>
          <Meter value={trend.strength} tone="indigo" />
          <span className="w-10 text-right font-medium tabular-nums">{Math.round(trend.strength * 100)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-20 shrink-0">Confidence</span>
          <Meter value={trend.confidence} tone="accent" />
          <span className="w-10 text-right font-medium tabular-nums">{Math.round(trend.confidence * 100)}%</span>
        </div>
      </div>

      <p className="mb-3 flex items-center gap-1.5 text-xs font-semibold">
        <span className="text-slate-500">Momentum</span>
        <span className={`inline-flex items-center gap-1 ${meta.className}`}>
          <TrendingUpIcon className={`h-3.5 w-3.5 ${momentum <= -0.15 ? "rotate-180" : ""}`} />
          {signed} · {meta.label}
        </span>
      </p>

      <p className="text-sm text-slate-700">{trend.explanation}</p>

      {trend.signals?.length > 0 && (
        <div className="mt-3 rounded-xl border border-primary-100/80 bg-white/70 p-3">
          <p className="text-xs font-semibold text-primary-700">
            Evidence ({trend.signals.length})
          </p>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-slate-500">
            {trend.signals.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// History chart: overall signal plus dashed per-domain lines.
function DetailHistoryChart({ history }) {
  const data = useMemo(() => {
    const points = [...(history || [])].sort((a, b) => a.date.localeCompare(b.date));

    const domainTally = new Map();
    points.forEach((p) => {
      Object.keys(p.domains || {}).forEach((key) => {
        domainTally.set(key, (domainTally.get(key) || 0) + 1);
      });
    });
    const topDomains = [...domainTally.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, CHART_COLORS.length)
      .map(([key]) => key);

    return {
      labels: points.map((p) => new Date(p.date).toLocaleDateString()),
      datasets: [
        {
          label: "Overall signal",
          data: points.map((p) => p.overall_signal),
          fill: true,
          borderColor: CHART_COLORS[0],
          backgroundColor: "rgba(124, 58, 237, 0.12)",
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.35,
        },
        ...topDomains.map((key, i) => ({
          label: formatDomainLabel(key),
          data: points.map((p) => p.domains?.[key] ?? null),
          spanGaps: true,
          borderColor: CHART_COLORS[(i + 1) % CHART_COLORS.length],
          backgroundColor: "transparent",
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderDash: [6, 4],
          tension: 0.35,
        })),
      ],
    };
  }, [history]);

  const options = lineChartOptions();

  return (
    <div className="h-72">
      <Line data={data} options={options} />
    </div>
  );
}

// Recent readings behind the curve, newest first.
function ReadingLog({ history }) {
  const points = [...(history || [])]
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 8);

  if (points.length === 0) return null;

  return (
    <div className="mt-4 border-t border-slate-100 pt-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
        Recent readings behind this curve
      </p>
      <ul className="space-y-1.5">
        {points.map((p, i) => (
          <li
            key={`${p.date}-${p.type}-${i}`}
            className="flex items-center justify-between gap-2 rounded-xl bg-slate-50/80 px-3 py-1.5"
          >
            <div className="flex items-center gap-2">
              <Badge tone={p.type === "tarot" ? "accent" : p.type === "palm" ? "primary" : "slate"}>
                {p.type || "reading"}
              </Badge>
              <span className="text-sm text-slate-700">
                {new Date(p.date).toLocaleString("en-US", LOG_DATE_FORMAT)}
              </span>
            </div>
            <span className="text-sm font-semibold tabular-nums text-slate-900">
              {Math.round(p.overall_signal * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const SCORE_GLOSSARY = [
  { term: "Score", meaning: "Current level of the trend in this life domain" },
  { term: "Strength", meaning: "How much evidence backs the signal" },
  { term: "Confidence", meaning: "How complete your reading data is" },
  { term: "Momentum", meaning: "Recent readings vs. your longer-term baseline" },
];

export default function LifeTrendsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const blocked = useRoleGuard();
  const {
    data: trends,
    error: fetchError,
    loading,
    refresh,
  } = useAsyncData(fetchLifeTrends, { enabled: !!user });

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login?redirect=/life-trends");
    }
  }, [authLoading, user, router]);

  if (blocked) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Returning to your dashboard…" />
      </div>
    );
  }

  if (authLoading || !user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Opening your trend analysis…" />
      </div>
    );
  }

  const error = fetchError
    ? "Could not load your life trend analysis. Please try again later."
    : null;

  const renderContent = () => {
    if (error) {
      return (
        <Panel title="Life Trend Analysis" subtitle="Signals drawn from your own readings">
          <ErrorState message={error} onRetry={refresh} />
        </Panel>
      );
    }

    if (loading || !trends) {
      return (
        <div className="space-y-6" aria-hidden="true">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="skeleton-shimmer h-32 rounded-panel" />
            <div className="skeleton-shimmer h-32 rounded-panel" />
            <div className="skeleton-shimmer h-32 rounded-panel" />
            <div className="skeleton-shimmer h-32 rounded-panel" />
          </div>
          <SkeletonRow lines={3} />
          <div className="h-40 rounded-[20px] bg-slate-100" />
          <div className="h-64 rounded-[20px] bg-slate-100" />
        </div>
      );
    }

    const coverage = trends.data_coverage || {};
    const hasHistory = (trends.history || []).length >= 2;
    const generatedAt = trends.generated_at
      ? new Date(trends.generated_at).toLocaleString("en-US", LOG_DATE_FORMAT)
      : null;

    return (
      <div className="animate-rise-in space-y-6">
        {/* Headline stats */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Growth Potential"
            value={`${Math.round((trends.growth_potential ?? 0) * 100)}%`}
            tone="primary"
            icon={TargetIcon}
            hint="Capacity for development implied by your signals"
          />
          <StatCard
            label="Readings Analyzed"
            value={coverage.readings_analyzed ?? 0}
            tone="accent"
            icon={FileTextIcon}
            hint={`${coverage.palm_readings ?? 0} palm · ${coverage.tarot_readings ?? 0} tarot`}
          />
          <StatCard
            label="Data Completeness"
            value={`${Math.round((coverage.completeness ?? 0) * 100)}%`}
            tone="emerald"
            icon={ChartIcon}
            hint={`${coverage.goals_used ?? 0} goal(s) from your profile included`}
          />
          <StatCard
            label="Active Trends"
            value={trends.current_trends?.length ?? 0}
            tone="blue"
            icon={ActivityIcon}
            hint="Domains with measurable signal"
          />
        </div>

        {/* Life path narrative */}
        <Panel title="Life Path" subtitle="Where your signals place you right now">
          <p className="flex items-start gap-3 text-base leading-relaxed text-slate-800 sm:text-lg">
            <CompassIcon className="mt-1 h-5 w-5 shrink-0 text-primary-600" />
            {trends.life_path}
          </p>
        </Panel>

        {/* Per-domain trend detail */}
        <Panel
          title="Current Trends"
          subtitle="Per-domain scores, momentum, and the evidence behind them"
        >
          {trends.current_trends?.length ? (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {trends.current_trends.map((t) => (
                <TrendDetailCard key={t.domain} trend={t} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={TrendingUpIcon}
              title="No trend signals yet"
              description="Complete a palm or tarot reading to generate real trend signals."
              action={
                <Button href="/readings/palm" variant="secondary" icon={ScanIcon}>
                  Perform a palm scan
                </Button>
              }
            />
          )}
        </Panel>

        {/* History curve + reading log */}
        <Panel
          title="Trend Over Time"
          subtitle="Overall signal after each reading, with the strongest domains"
        >
          {hasHistory ? (
            <>
              <DetailHistoryChart history={trends.history} />
              <ReadingLog history={trends.history} />
            </>
          ) : (
            <EmptyState
              icon={ChartIcon}
              title="No trend history yet"
              description="The timeline fills in after a couple of readings — each new scan adds a point."
            />
          )}
        </Panel>

        {/* Opportunities & challenges */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="Opportunities" subtitle="Favorable openings your signals suggest">
            <InsightList items={trends.opportunities} tone="emerald" />
          </Panel>
          <Panel title="Challenges" subtitle="Friction points worth watching">
            <InsightList items={trends.challenges} tone="accent" />
          </Panel>
        </div>

        {/* Method, coverage, glossary, disclaimer */}
        <Panel title="About this analysis" subtitle="Method, coverage, and how to read the scores">
          <div className="space-y-4">
            <p className="text-sm leading-relaxed text-slate-700">{trends.explanation}</p>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {SCORE_GLOSSARY.map((g) => (
                <div key={g.term} className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-primary-700">
                    {g.term}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-600">{g.meaning}</p>
                </div>
              ))}
            </div>

            <p className="text-xs text-slate-500">
              Data coverage: {coverage.palm_readings ?? 0} palm · {coverage.tarot_readings ?? 0}{" "}
              tarot · {coverage.goals_used ?? 0} goal(s) from your profile · completeness{" "}
              {Math.round((coverage.completeness ?? 0) * 100)}%
            </p>

            <p className="text-xs text-slate-500">
              Engine {trends.engine}
              {trends.engine_version ? ` v${trends.engine_version}` : ""} · {trends.method}
              {generatedAt ? ` · generated ${generatedAt}` : ""}
            </p>

            <p className="border-t border-slate-100 pt-3 text-xs italic leading-relaxed text-slate-500">
              {trends.disclaimer}
            </p>
          </div>
        </Panel>
      </div>
    );
  };

  return (
    <div className="animate-fade-in space-y-6">
      <Seo
        title="Life trends"
        description="Momentum, domain history, and evidence-backed signals computed from your own palm and tarot readings."
      />

      <PageHeader
        icon={TrendingUpIcon}
        tileTone="primary"
        eyebrow="Reading-informed signals"
        title="Life Trend Analysis"
        description="Feature-based signals computed from your own palm and tarot readings. Every score is grounded in evidence from your archive and fully explainable — interpretive guidance for self-reflection, not prediction."
        actions={
          <>
            <Button variant="secondary" icon={RetryIcon} onClick={refresh} loading={loading}>
              Refresh
            </Button>
            <Button href="/readings/palm" icon={ScanIcon}>
              New palm scan
            </Button>
          </>
        }
      />

      {renderContent()}
    </div>
  );
}
