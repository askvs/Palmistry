// Canonical loading, empty and error states.
import Button from "@/components/ui/Button";
import { AlertIcon, RetryIcon } from "@/components/icons";

export function Spinner({ className = "h-5 w-5", label }) {
  return (
    <span className="inline-flex items-center gap-2.5" role="status" aria-live="polite">
      <span
        className={`inline-block animate-spin rounded-full border-2 border-primary-100 border-t-primary-600 ${className}`}
        aria-hidden="true"
      />
      {label && <span className="text-sm text-slate-500">{label}</span>}
      {!label && <span className="sr-only">Loading</span>}
    </span>
  );
}

// Row-level skeleton for lists/tables inside panels.
export function SkeletonRow({ lines = 2, className = "" }) {
  return (
    <div className={`animate-pulse space-y-2.5 py-2 ${className}`} aria-hidden="true">
      <div className="h-4 w-3/4 rounded bg-slate-200/80" />
      {Array.from({ length: Math.max(0, lines - 1) }).map((_, i) => (
        <div key={i} className="h-3 w-1/2 rounded bg-slate-100" />
      ))}
    </div>
  );
}

// Card-grid skeleton whose shape mirrors a `grid` of panels.
export function SkeletonCards({ count = 3, className = "" }) {
  return (
    <div
      className={`grid gap-5 sm:grid-cols-2 lg:grid-cols-3 ${className}`}
      aria-hidden="true"
    >
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-[20px] border border-slate-200/70 bg-white p-6">
          <div className="h-9 w-9 rounded-xl bg-slate-200/80" />
          <div className="mt-4 h-4 w-2/3 rounded bg-slate-200/80" />
          <div className="mt-2.5 h-3 w-full rounded bg-slate-100" />
          <div className="mt-1.5 h-3 w-4/5 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action, className = "" }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-[20px] border border-slate-200 bg-[#fbfafe] px-6 py-12 text-center ${className}`}
    >
      {Icon && (
        <span className="flex h-[46px] w-[46px] items-center justify-center rounded-full bg-white text-primary-600 shadow-rest ring-1 ring-slate-200 shadow-[inset_0_1px_0_rgba(255,255,255,.85),0_1px_2px_rgba(30,24,54,.05)]">
          <Icon className="h-6 w-6" />
        </span>
      )}
      <h3 className="mt-4 text-sm font-semibold text-slate-900">{title}</h3>
      {description && (
        <p className="mt-1.5 max-w-[42ch] text-sm leading-relaxed text-slate-500">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", message, onRetry, className = "" }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-[20px] border border-rose-200 bg-[#fff7f8] px-6 py-10 text-center ${className}`}
      role="alert"
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-rose-100 text-rose-600">
        <AlertIcon className="h-5 w-5" />
      </span>
      <h3 className="mt-3.5 text-sm font-semibold text-rose-900">{title}</h3>
      {message && (
        <p className="mt-1.5 max-w-sm text-sm leading-relaxed text-rose-700">{message}</p>
      )}
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-5" icon={RetryIcon} onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

// Compact inline error for use inside forms/sections (not full-page).
export function InlineError({ message, className = "" }) {
  if (!message) return null;
  return (
    <div
      className={`flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700 ${className}`}
      role="alert"
    >
      <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
