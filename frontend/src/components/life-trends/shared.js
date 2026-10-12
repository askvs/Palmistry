// Shared primitives for life trend views (dashboard summary panel + the detailed /life-trends page).
import { Badge } from "@/components/ui";
import { api } from "@/services/api";

export const DIRECTION_META = {
  rising: { label: "Rising", tone: "emerald" },
  stable: { label: "Stable", tone: "accent" },
  declining: { label: "Declining", tone: "rose" },
};

const METER_TONES = {
  primary: "bg-primary-500",
  indigo: "bg-indigo-500",
  accent: "bg-accent-500",
};

export function Meter({ value, tone = "primary" }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-primary-100">
      <div
        className={`h-full rounded-full ${METER_TONES[tone] || METER_TONES.primary} transition-all duration-500`}
        style={{ width: `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%` }}
      />
    </div>
  );
}

const INSIGHT_TONES = {
  emerald: {
    wrap: "border-emerald-100 bg-emerald-50/70",
    title: "text-emerald-800",
  },
  accent: {
    wrap: "border-accent-100 bg-accent-50/70",
    title: "text-accent-800",
  },
};

export function InsightList({ items, tone }) {
  if (!items?.length) {
    return <p className="text-sm italic text-slate-500">Not enough evidence yet.</p>;
  }
  const t = INSIGHT_TONES[tone] || INSIGHT_TONES.emerald;
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item.title} className={`rounded-xl border p-3 ${t.wrap}`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className={`text-sm font-semibold ${t.title}`}>{item.title}</p>
            {typeof item.confidence === "number" && (
              <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                {Math.round(item.confidence * 100)}% confident
              </span>
            )}
          </div>
          <p className="mt-0.5 text-sm text-slate-700">{item.explanation}</p>
          {item.signals?.length > 0 && (
            <p className="mt-1 text-xs text-slate-500">Signals: {item.signals.join(" · ")}</p>
          )}
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
