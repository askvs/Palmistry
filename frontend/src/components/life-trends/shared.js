// Shared primitives for life trend views (dashboard summary panel + the detailed /life-trends page).
import { Badge } from "@/components/ui";
import { api } from "@/services/api";

export const DIRECTION_META = {
  rising: { label: "Rising", tone: "emerald" },
  stable: { label: "Stable", tone: "accent" },
  declining: { label: "Declining", tone: "rose" },
};

const METER_TONES = {
  primary: "bg-primary-600",
  indigo: "bg-primary-400",
  accent: "bg-accent-500",
};

export function Meter({ value, tone = "primary" }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full ${METER_TONES[tone] || METER_TONES.primary} transition-[width] duration-[240ms]`}
        style={{ width: `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%` }}
      />
    </div>
  );
}

const INSIGHT_TITLE_TONES = {
  emerald: "text-emerald-800",
  accent: "text-accent-800",
};

export function InsightList({ items, tone }) {
  if (!items?.length) {
    return <p className="text-sm italic text-slate-500">Not enough evidence yet.</p>;
  }
  const titleTone = INSIGHT_TITLE_TONES[tone] || INSIGHT_TITLE_TONES.emerald;
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li
          key={item.title}
          className="flex items-start gap-3 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[inset_0_1px_0_rgba(255,255,255,.85),var(--shadow-rest)]"
        >
          <span className="mt-0.5 text-sm leading-none text-accent-700" aria-hidden="true">
            ✦
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className={`text-sm font-semibold ${titleTone}`}>{item.title}</p>
              {typeof item.confidence === "number" && (
                <span className="text-[12.5px] font-medium text-slate-500">
                  {Math.round(item.confidence * 100)}% confident
                </span>
              )}
            </div>
            <p className="mt-1 text-sm leading-relaxed text-slate-700">{item.explanation}</p>
            {item.signals?.length > 0 && (
              <p className="mt-1.5 text-[12.5px] text-slate-500">
                Signals: {item.signals.join(" · ")}
              </p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

// "career_growth" -> "Career Growth" for chart legends and labels.
export function formatDomainLabel(domain) {
  if (!domain) return "Unknown";
  return domain
    .split(/[_\s-]+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

// Module-level loader so useAsyncData can re-run it safely (retry = refresh).
export async function fetchLifeTrends() {
  try {
    return await api.get("/api/v1/life-trends");
  } catch (err) {
    console.error("Error fetching life trends:", err);
    throw err;
  }
}
