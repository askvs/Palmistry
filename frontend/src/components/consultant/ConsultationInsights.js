// Consultation insights across the workload.
import {
  ActivityIcon,
  AlertIcon,
  ChartIcon,
  ClockIcon,
  SearchIcon,
  UsersIcon,
} from "@/components/icons";
import { EmptyState, Panel, SkeletonRow } from "@/components/ui";
import {
  SectionError,
  SourceBadge,
} from "@/components/consultant/shared";
import { formatDateTime, relativeLabel } from "@/lib/format";

const ICONS = {
  trend: ChartIcon,
  pattern: SearchIcon,
  alert: AlertIcon,
  users: UsersIcon,
  time: ClockIcon,
  activity: ActivityIcon,
};

export default function ConsultationInsights({
  items = [],
  source,
  loading = false,
  error = null,
  onRetry,
  trends,
}) {
  const body = () => {
    if (error) {
      return <SectionError title="Unable to load consultation insights." onRetry={onRetry} />;
    }
    if (loading) {
      return (
        <div className="space-y-3">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      );
    }
    if (items.length === 0) {
      return (
        <EmptyState
          icon={ChartIcon}
          title="No insights yet"
          description="Patterns appear once you have closed a few consultations."
        />
      );
    }

    return (
      <ul className="grid gap-3 lg:grid-cols-2">
        {items.map((item) => {
          const Icon = ICONS[item.icon] || ActivityIcon;
          return (
            <li
              key={item.id}
              className="surface-card hover-lift flex items-start gap-3.5 p-4"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-50 text-accent-600 ring-1 ring-accent-100">
                <Icon className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h4 className="text-sm font-semibold text-slate-900">{item.title}</h4>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">
                    {item.category}
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{item.explanation}</p>
                <p className="mt-1.5 text-[11px] text-slate-500 tabular-nums">
                  {item.date ? formatDateTime(item.date) : "Live figure · updated now"}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <Panel
      title="Consultation Insights"
      subtitle="Patterns across your consultations and your clients' readings"
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-4">
        {body()}

        {trends && (
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-card border border-slate-100 bg-slate-50/70 p-3.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Registered seekers
              </p>
              <p className="mt-1 text-lg font-bold tracking-tight text-slate-900 tabular-nums">
                {trends.total_users}
              </p>
            </div>
            <div className="rounded-card border border-slate-100 bg-slate-50/70 p-3.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Active seekers
              </p>
              <p className="mt-1 text-lg font-bold tracking-tight text-slate-900 tabular-nums">
                {trends.active_users}
              </p>
            </div>
            <div className="rounded-card border border-slate-100 bg-slate-50/70 p-3.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Last reading
              </p>
              <p className="mt-1 text-lg font-bold tracking-tight text-slate-900 tabular-nums">
                {relativeLabel(trends.readings_per_day?.[trends.readings_per_day.length - 1]?.day)}
              </p>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
