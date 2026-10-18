// Shared primitives for the Spiritual Consultant console.
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Panel,
  SkeletonRow,
} from "@/components/ui";
import { AlertIcon, InfoIcon, SparkleIcon } from "@/components/icons";
import { CLIENT_STATUS_LABELS, CLIENT_TREND_LABELS } from "@/services/consultantDemoData";

export { Badge, Button, EmptyState, ErrorState, Panel, SkeletonRow };

// Avatar section.
const AVATAR_TONES = [
  "from-primary-500 to-indigo-600",
  "from-accent-500 to-amber-600",
  "from-emerald-500 to-teal-600",
  "from-blue-500 to-indigo-600",
  "from-fuchsia-500 to-primary-600",
];

function toneFor(seed = "") {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) hash = (hash * 31 + seed.charCodeAt(i)) % 997;
  return AVATAR_TONES[hash % AVATAR_TONES.length];
}

// Initials avatar.
export function ClientAvatar({ name = "", initials = "", size = "md", className = "" }) {
  const label = initials || name;
  const sizes = {
    sm: "h-8 w-8 text-[11px]",
    md: "h-10 w-10 text-xs",
    lg: "h-14 w-14 text-base",
  };
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br font-bold text-white ${toneFor(
        label
      )} ${sizes[size] || sizes.md} ${className}`}
    >
      {label}
    </span>
  );
}

// Badge section.
const TREND_TONES = {
  positive: "emerald",
  stable: "slate",
  growth: "primary",
  attention: "rose",
};

export function TrendBadge({ trend }) {
  if (!trend) return <Badge tone="slate">—</Badge>;
  return <Badge tone={TREND_TONES[trend] || "slate"}>{CLIENT_TREND_LABELS[trend] || trend}</Badge>;
}

export function StatusBadge({ status }) {
  const tones = {
    upcoming: "primary",
    in_progress: "accent",
    completed: "emerald",
    pending: "slate",
    open: "accent",
    in_review: "blue",
    resolved: "emerald",
  };
  const labels = {
    upcoming: "Upcoming",
    in_progress: "In progress",
    completed: "Completed",
    pending: "Pending",
    open: "Open",
    in_review: "In review",
    resolved: "Resolved",
  };
  return <Badge tone={tones[status] || "slate"}>{labels[status] || status}</Badge>;
}

export function ClientStatusBadge({ status }) {
  const tones = { active: "emerald", follow_up: "accent", recent: "slate" };
  return <Badge tone={tones[status] || "slate"}>{CLIENT_STATUS_LABELS[status] || status}</Badge>;
}

// Honest provenance marker.
export function SourceBadge({ source, label }) {
  if (!source) return null;
  if (source === "live") {
    return (
      <Badge tone="emerald" className="whitespace-nowrap">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
        Live data
      </Badge>
    );
  }
  if (source === "local") {
    return (
      <Badge tone="slate" className="whitespace-nowrap">
        Saved on this device
      </Badge>
    );
  }
  return (
    <Badge tone="slate" className="whitespace-nowrap" title={label || "Sample data for demonstration"}>
      <InfoIcon className="h-3 w-3" />
      Demo data
    </Badge>
  );
}

// Small disclaimer strip used under every AI/insight surface.
export function GuidanceDisclaimer({ children }) {
  return (
    <p className="flex items-start gap-2 rounded-2xl border border-slate-200/80 bg-slate-50/70 px-4 py-3 text-[11px] italic leading-relaxed text-slate-500">
      <InfoIcon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
      <span>
        {children ||
          "AI insights are interpretive reflection points drawn from this client's readings. They are not medical, financial or legal advice, and not a guaranteed prediction."}
      </span>
    </p>
  );
}

// Leading icon tile used by the AI insight cards.
export function AIInsightIcon({ className = "" }) {
  return (
    <span
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-600 ring-1 ring-primary-100 ${className}`}
    >
      <SparkleIcon className="h-4 w-4" />
    </span>
  );
}

// Form controls section.
const FIELD_CLASS =
  "h-9 cursor-pointer rounded-full border border-slate-200 bg-slate-50 pl-3 pr-8 text-xs font-medium text-slate-700 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-60";

export function ConsultantSelect({ label, value, onChange, options, className = "", disabled = false }) {
  return (
    <label className={`relative inline-flex items-center ${className}`}>
      <span className="sr-only">{label}</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label}
        className={FIELD_CLASS}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <span className="pointer-events-none absolute right-2.5 text-slate-400" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-3.5 w-3.5">
          <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    </label>
  );
}

// Compact labelled field wrapper used by the workspace forms.
export function FieldLabel({ children, hint }) {
  return (
    <span className="block">
      <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
        {children}
      </span>
      {hint && <span className="mt-0.5 block text-xs text-slate-500">{hint}</span>}
    </span>
  );
}

// Fixed-height responsive wrapper — chart.js needs a sized parent.
export function ChartFrame({ children, height = "h-72", className = "" }) {
  return <div className={`${height} w-full ${className}`}>{children}</div>;
}

// Skeleton used while a chart's data resolves.
export function ChartSkeleton({ height = "h-72", label = "Loading chart…" }) {
  return (
    <div className={`${height} w-full animate-pulse rounded-2xl bg-slate-100`} aria-hidden="true">
      <span className="sr-only">{label}</span>
    </div>
  );
}

// Section-level error with retry, matching the platform's error language.
export function SectionError({ title = "Unable to load this section", onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50/70 px-5 py-8 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-100 text-rose-600">
        <AlertIcon className="h-5 w-5" />
      </span>
      <p className="text-sm font-medium text-rose-900">{title}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}
