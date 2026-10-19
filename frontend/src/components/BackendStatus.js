import { useAsyncData } from "@/hooks/useAsyncData";
import { api } from "@/services/api";
import { RetryIcon } from "@/components/icons";

// Stable module-level loader — required by useAsyncData.
async function loadHealth() {
  return api.get("/api/v1/health");
}

// Subtle one-line status chip for the homepage.
export default function BackendStatus() {
  const { data, error, loading, refresh } = useAsyncData(loadHealth);

  if (loading) {
    return (
      <div className="flex justify-center" data-testid="status-loading">
        <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 text-xs text-slate-500 backdrop-blur-sm">
          <span className="h-2 w-2 animate-pulse rounded-full bg-accent-500" />
          Checking backend…
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center" data-testid="status-error">
        <span
          title={`Backend unreachable${error?.code ? ` (${error.code})` : ""} — start the API with uvicorn app.main:app`}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 py-1 pl-2.5 pr-1 text-xs text-slate-500 backdrop-blur-sm"
        >
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-600" />
          </span>
          Backend offline
          <button
            type="button"
            onClick={refresh}
            className="inline-flex cursor-pointer items-center gap-1 rounded-full px-2 py-0.5 font-medium text-rose-700 transition hover:bg-rose-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-600"
          >
            <RetryIcon className="h-3 w-3" />
            Retry
          </button>
        </span>
      </div>
    );
  }

  return (
    <div className="flex justify-center" data-testid="status-success">
      <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 text-xs text-slate-500 backdrop-blur-sm">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-40" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        Backend connected
        {data?.environment && (
          <>
            <span className="text-slate-300" aria-hidden="true">
              ·
            </span>
            <span className="font-normal text-slate-500">
              env {data.environment} · v{data.version}
            </span>
          </>
        )}
      </span>
    </div>
  );
}
