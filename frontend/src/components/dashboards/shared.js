// Shared presentational primitives for role dashboards.
import Link from "next/link";
import KitBadge from "@/components/ui/Badge";
import KitButton from "@/components/ui/Button";
import { ArrowRightIcon, CardsIcon, FileTextIcon, HandIcon } from "@/components/icons";

// Kit Panel and SkeletonRow are canonical; re-exported so existing consumers of the dashboards/shared barrel keep working.
export { Panel, SkeletonRow } from "@/components/ui";

const DAY_MS = 24 * 60 * 60 * 1000;

// Grouped per-day bar chart for recent-activity series.
export function PerDayBars({ series, days = 7, ariaLabel = "Daily activity chart" }) {
  // UTC day keys match the backend's date_trunc("day", ...) buckets.
  const now = new Date();
  const utcToday = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const dayKeys = [];
  for (let i = days - 1; i >= 0; i -= 1) {
    dayKeys.push(new Date(utcToday - i * DAY_MS).toISOString().slice(0, 10));
  }

  const counts = series.map((s) => {
    const byDay = new Map(s.data.map((d) => [d.day, d.count]));
    return { ...s, values: dayKeys.map((k) => byDay.get(k) || 0) };
  });
  const maxCount = Math.max(1, ...counts.flatMap((s) => s.values));
  const windowTotal = counts.reduce((sum, s) => sum + s.values.reduce((a, b) => a + b, 0), 0);

  return (
    <div>
      <div
        role="img"
        aria-label={`${ariaLabel} (${windowTotal} total in window)`}
        className="flex h-40 items-end gap-2 border-b border-slate-200 pb-2"
      >
        {dayKeys.map((day, dayIndex) => (
          <div key={day} className="flex h-full flex-1 items-end justify-center gap-1">
            {counts.map((s) => {
              const value = s.values[dayIndex];
              const height =
                value === 0 ? "3px" : `${Math.max(6, Math.round((value / maxCount) * 100))}%`;
              return (
                <div
                  key={s.key}
                  className="group flex h-full w-full max-w-[24px] items-end justify-center"
                >
                  <span className="mb-1 text-[11px] font-bold tabular-nums text-slate-600 opacity-0 transition group-hover:opacity-100">
                    {value}
                  </span>
                  <div
                    className={`w-full rounded-t-md transition-all ${s.barClass}`}
                    style={{ height }}
                    title={`${s.label}: ${value} on ${day}`}
                  />
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 px-1 text-[12.5px] text-slate-500">
        <div className="flex items-center gap-3">
          {counts.map((s) => (
            <span key={s.key} className="inline-flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${s.swatchClass || s.barClass}`} />
              {s.label}
            </span>
          ))}
        </div>
        <span>
          Last {days} days · {windowTotal} total
        </span>
      </div>
    </div>
  );
}

const STAT_TONES = {
  primary: "bg-primary-50 text-primary-600",
  accent: "bg-accent-50 text-accent-600",
  emerald: "bg-emerald-50 text-emerald-600",
  blue: "bg-blue-50 text-blue-600",
  slate: "bg-slate-100 text-slate-600",
};

// Legacy tone names kept for pre-kit consumers (e.g. personality page).
const STAT_TONE_ALIASES = { violet: "primary", amber: "accent" };

export function StatCard({ label, value, hint, icon, trend, tone = "primary" }) {
  const resolvedTone = STAT_TONE_ALIASES[tone] || tone;
  const iconClasses = STAT_TONES[resolvedTone] || STAT_TONES.primary;
  // Icons may be a kit SVG component (new call sites) or a plain string (legacy call sites render it as text inside the tile).
  const Icon = typeof icon === "function" ? icon : null;

  return (
    <div className="surface-card p-6 transition duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-lift">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}</h2>
        {icon && (
          <span
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${iconClasses}`}
          >
            {Icon ? <Icon className="h-5 w-5" /> : <span className="text-base leading-none">{icon}</span>}
          </span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-2">
        <p className="text-[26px] font-bold leading-[1.2] tracking-[-0.01em] tabular-nums text-slate-900 sm:text-[30px]">
          {value}
        </p>
        {trend && (
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              trend.positive
                ? "bg-emerald-50 text-emerald-700"
                : "bg-rose-50 text-rose-700"
            }`}
          >
            <span aria-hidden="true">{trend.positive ? "▲" : "▼"}</span>
            {trend.text}
          </span>
        )}
      </div>

      {hint && <p className="mt-1.5 text-[12.5px] leading-relaxed text-slate-500">{hint}</p>}
    </div>
  );
}

// Legacy tone names (violet/amber) map onto the kit's semantic tones so existing call sites keep their look now that.
const BADGE_TONE_ALIASES = { violet: "primary", amber: "accent" };

export function Badge({ tone = "slate", className = "", children }) {
  return (
    <KitBadge tone={BADGE_TONE_ALIASES[tone] || tone} className={className}>
      {children}
    </KitBadge>
  );
}

export function EmptyRow({ children }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

// Display labels for ConsultationStatus values (consultant + admin panels).
export const CONSULTATION_STATUS_LABELS = {
  open: "Open",
  in_review: "In review",
  resolved: "Resolved",
};

// Horizontal 0–100% meter for ratios and rates (accessible role="meter").
const METER_TONES = {
  primary: "bg-primary-600",
  accent: "bg-accent-500",
  emerald: "bg-emerald-500",
  blue: "bg-blue-500",
  rose: "bg-rose-500",
};

export function MeterBar({ value, tone = "primary", label, className = "" }) {
  const pct = Math.round(Math.min(1, Math.max(0, value || 0)) * 100);
  return (
    <div
      role="meter"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
      className={`h-2 w-full overflow-hidden rounded-full bg-slate-100 ${className}`}
    >
      <div
        className={`h-full rounded-full transition-[width] duration-[240ms] ${METER_TONES[tone] || METER_TONES.primary}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// "95 min" / "2.4 h" / "1.3 days" — null renders an em dash.
export function formatDuration(minutes) {
  if (minutes == null) return "—";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  if (minutes < 60 * 24) {
    const hours = minutes / 60;
    return `${hours >= 10 ? Math.round(hours) : hours.toFixed(1)} h`;
  }
  return `${(minutes / (60 * 24)).toFixed(1)} days`;
}

// Low-key self-reading entry points for staff consoles.
export function PersonalPracticeRow({ note, className = "" }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200/70 bg-white/60 p-4 ${className}`}
    >
      <div className="min-w-0 flex-1">
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
          Personal practice
        </p>
        <p className="mt-0.5 text-xs text-slate-500">{note}</p>
      </div>
      <KitButton href="/readings/tarot" variant="ghost" size="sm" icon={CardsIcon}>
        Tarot session
      </KitButton>
      <KitButton href="/readings/palm" variant="ghost" size="sm" icon={HandIcon}>
        Palm scan
      </KitButton>
      <KitButton href="/readings" variant="ghost" size="sm" icon={FileTextIcon}>
        Your readings
      </KitButton>
    </div>
  );
}

// Compact inset toggle for panel toolbars (timeline/list, tab filters).
export function Segmented({ options, value, onChange, label, className = "" }) {
  return (
    <div
      role="group"
      aria-label={label}
      className={`inline-flex items-center rounded-full border border-slate-200 bg-slate-100 p-[3px] ${className}`}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-colors duration-[120ms] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
              active
                ? "bg-white text-slate-900 shadow-[0_1px_3px_rgba(30,24,54,0.12)]"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export function ReadingTimeline({ readings = [] }) {
  if (!readings || readings.length === 0) {
    return (
      <EmptyRow>
        No readings recorded yet. Perform a palm scan or tarot reading to begin your timeline.
      </EmptyRow>
    );
  }

  return (
    <div className="relative space-y-6 pl-6 before:absolute before:bottom-2 before:left-2 before:top-2 before:w-0.5 before:bg-slate-200">
      {readings.map((r, idx) => {
        const isTarot = r.type === "tarot";
        const isPalm = r.type === "palm";
        return (
          <div key={r.id || idx} className="group relative">
            <div
              className={`absolute -left-[23px] top-1.5 h-3.5 w-3.5 rounded-full border-2 border-white shadow-xs ${
                isTarot
                  ? "bg-accent-500 ring-2 ring-accent-200"
                  : isPalm
                  ? "bg-primary-600 ring-2 ring-primary-200"
                  : "bg-slate-400 ring-2 ring-slate-200"
              }`}
            />

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-2xs transition-all hover:border-primary-200 hover:shadow-md">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">
                    {new Date(r.created_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                  <KitBadge tone={isTarot ? "accent" : isPalm ? "primary" : "slate"}>
                    {isTarot ? "Tarot" : isPalm ? "Palm" : r.type}
                  </KitBadge>
                  {r.status && (
                    <KitBadge tone={r.status === "completed" ? "emerald" : "accent"}>
                      {r.status}
                    </KitBadge>
                  )}
                </div>

                <Link
                  href={`/readings/${r.id}`}
                  className="inline-flex items-center gap-1 rounded-sm text-xs font-semibold text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                >
                  Inspect reading
                  <ArrowRightIcon className="h-3.5 w-3.5" />
                </Link>
              </div>

              <h4 className="mt-2 text-sm font-semibold text-slate-900 transition-colors group-hover:text-primary-700">
                <Link href={`/readings/${r.id}`}>{r.title}</Link>
              </h4>

              {r.summary && (
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-600">
                  {r.summary}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
