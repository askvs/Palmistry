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
        <span className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium text-slate-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-slate-300" />
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
          className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 py-1 pl-2.5 pr-1 text-xs font-medium text-rose-700"
        >
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
          </span>
          Backend offline
          <button
            type="button"
            onClick={refresh}
            className="inline-flex cursor-pointer items-center gap-1 rounded-full px-2 py-0.5 font-medium text-rose-600 transition hover:bg-rose-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-600"
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
      <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        Backend connected
        {data?.environment && (
          <>
            <span className="text-emerald-600/60" aria-hidden="true">
              ·
            </span>
            <span className="font-normal text-emerald-600">
              env {data.environment} · v{data.version}
            </span>
          </>
        )}
      </span>
    </div>
  );
}
