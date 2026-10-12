// Consultation Reports — filterable table of reports the consultant generated.
import { Button, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import { DownloadIcon, EyeIcon, FileTextIcon, SearchIcon, ShareIcon } from "@/components/icons";
import { SectionError, SourceBadge } from "@/components/consultant/shared";
import { formatDate } from "@/lib/format";

const STATUS_FILTERS = [
  { value: "all", label: "All" },
  { value: "ready", label: "Ready" },
  { value: "generating", label: "Generating" },
];

const REPORT_STATUS_META = {
  ready: { label: "Ready", tone: "emerald" },
  generating: { label: "Generating", tone: "accent" },
};

export default function ConsultationReportsTable({
  reports = [],
  source,
  total = 0,
  loading = false,
  error = null,
  onRetry,
  status,
  onStatusChange,
  clientId,
  onClientChange,
  clientOptions = [],
  onDownload,
  downloadingId = null,
  onShare,
}) {
  return (
    <Panel
      title="Consultation Reports"
      subtitle="Reports generated from your consultation sessions"
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-5">
        <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-slate-50/60 p-3.5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Filter:</span>
            {STATUS_FILTERS.map((filter) => (
              <button
                key={filter.value}
                type="button"
                aria-pressed={status === filter.value}
                onClick={() => onStatusChange?.(filter.value)}
                className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                  status === filter.value
                    ? "bg-primary-600 text-white shadow-sm shadow-primary-600/25"
                    : "bg-white text-slate-600 ring-1 ring-slate-200 hover:text-slate-900"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>

          <label className="relative inline-flex items-center">
            <span className="sr-only">Filter by client</span>
            <SearchIcon className="pointer-events-none absolute left-3 h-3.5 w-3.5 text-slate-400" />
            <select
              value={clientId}
              onChange={(event) => onClientChange?.(event.target.value)}
              className="h-8 cursor-pointer appearance-none rounded-full border border-slate-200 bg-white pl-8 pr-3 text-xs font-medium text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <option value="">All clients</option>
              {clientOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error ? (
          <SectionError title="Unable to load reports." onRetry={onRetry} />
        ) : loading ? (
          <div className="space-y-3">
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
          </div>
        ) : reports.length === 0 ? (
          <EmptyState
            icon={FileTextIcon}
            title={total === 0 ? "No reports yet" : "No reports match this filter"}
            description={
              total === 0
                ? "Reports are generated from the consultation workspace once you save a session."
                : "Try a different status or client filter."
            }
          />
        ) : (
          <>
            {/* Table (md+) */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full min-w-[42rem] border-collapse text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-[11px] uppercase tracking-wider text-slate-400">
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Client
                    </th>
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Consultation
                    </th>
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Date
                    </th>
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Report status
                    </th>
                    <th scope="col" className="px-4 py-3 text-right font-semibold">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {reports.map((report) => {
                    const meta = REPORT_STATUS_META[report.status] || REPORT_STATUS_META.generating;
                    const ready = report.status === "ready";
                    return (
                      <tr key={report.id} className="transition hover:bg-slate-50/70">
                        <td className="px-4 py-3.5 text-sm font-semibold text-slate-900">
                          {report.clientName}
                        </td>
                        <td className="px-4 py-3.5 text-sm text-slate-700">{report.consultation}</td>
                        <td className="px-4 py-3.5 text-sm text-slate-600">
                          {formatDate(report.date)}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                              meta.tone === "emerald"
                                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                : "border-accent-200 bg-accent-50 text-accent-800"
                            }`}
                          >
                            {meta.label}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={EyeIcon}
                              href={`/consultant/clients/${report.clientId}`}
                            >
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              icon={DownloadIcon}
                              disabled={!ready}
                              loading={downloadingId === report.id}
                              onClick={() => onDownload?.(report)}
                            >
                              PDF
                            </Button>
                            {onShare && (
                              <Button
                                size="sm"
                                variant="ghost"
                                icon={ShareIcon}
                                disabled={!ready}
                                onClick={() => onShare?.(report)}
                              >
                                Share
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Cards (<md) */}
            <ul className="space-y-3 md:hidden">
              {reports.map((report) => {
                const ready = report.status === "ready";
                return (
                  <li
                    key={report.id}
                    className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900">
                          {report.clientName}
                        </p>
                        <p className="truncate text-xs text-slate-500">{report.consultation}</p>
                      </div>
                      <span
                        className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                          ready
                            ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                            : "border-accent-200 bg-accent-50 text-accent-800"
                        }`}
                      >
                        {ready ? "Ready" : "Generating"}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{formatDate(report.date)}</p>
                    <div className="mt-3 flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={EyeIcon}
                        href={`/consultant/clients/${report.clientId}`}
                        fullWidth
                      >
                        View
                      </Button>
                      <Button
                        size="sm"
                        icon={DownloadIcon}
                        disabled={!ready}
                        loading={downloadingId === report.id}
                        onClick={() => onDownload?.(report)}
                      >
                        PDF
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </div>
    </Panel>
  );
}
