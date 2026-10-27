// Reading report management for the tarot reader (FR-004, FR-036).
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { MeterBar, Segmented } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { listReaderReports } from "@/services/reader";
import { readerReviewReading } from "@/services/roles";
import { downloadReportExcel, downloadReportPdf } from "@/services/reports";
import {
  CheckIcon,
  DownloadIcon,
  FileTextIcon,
  SearchIcon,
  TableIcon,
} from "@/components/icons";

const TYPE_FILTERS = [
  { value: "", label: "All" },
  { value: "palm", label: "Palm" },
  { value: "tarot", label: "Tarot" },
];

const REVIEW_FILTERS = [
  { value: "", label: "All" },
  { value: "false", label: "Awaiting review" },
  { value: "true", label: "Reviewed" },
];

function slug(text) {
  return (
    String(text || "reading")
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .trim()
      .replace(/[\s_-]+/g, "-") || "reading"
  );
}

export default function ReadingReportsTable() {
  const toast = useToast();
  const [type, setType] = useState("");
  const [reviewed, setReviewed] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState({ id: null, kind: null });
  const [actionError, setActionError] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const loader = useCallback(
    () =>
      listReaderReports({
        type: type || undefined,
        reviewed: reviewed === "" ? null : reviewed === "true",
        search: search || undefined,
        limit: 100,
      }),
    [type, reviewed, search]
  );
  const { data, error, loading, refresh } = useAsyncData(loader);

  const items = data?.items || [];
  const reviewedCount = items.filter((row) => row.reviewed).length;

  async function certify(row) {
    setBusy({ id: row.id, kind: "certify" });
    setActionError(null);
    try {
      await readerReviewReading(row.id, { status: "completed" });
      toast.success("Reading certified", `"${row.title}" is marked as reviewed.`);
      await refresh();
    } catch (err) {
      setActionError(err?.message || "Could not certify this reading. Please try again.");
    } finally {
      setBusy({ id: null, kind: null });
    }
  }

  async function exportPdf(row) {
    setBusy({ id: row.id, kind: "pdf" });
    setActionError(null);
    try {
      await downloadReportPdf(row.id, `${slug(row.title)}.pdf`);
      toast.success("Report downloaded", "The detailed PDF report has been saved.");
    } catch (err) {
      setActionError(err?.message || "The PDF report could not be generated. Please try again.");
    } finally {
      setBusy({ id: null, kind: null });
    }
  }

  async function exportExcel(row) {
    setBusy({ id: row.id, kind: "excel" });
    setActionError(null);
    try {
      await downloadReportExcel(row.id, `${slug(row.title)}.xlsx`);
      toast.success("Report downloaded", "The detailed Excel workbook (Overview, Analysis, Guidance, Metadata) has been saved.");
    } catch (err) {
      setActionError(err?.message || "The Excel workbook could not be generated. Please try again.");
    } finally {
      setBusy({ id: null, kind: null });
    }
  }

  const isBusy = (row, kind) => busy.id === row.id && (kind ? busy.kind === kind : true);

  return (
    <Panel
      title="Reading Reports"
      subtitle="Every platform reading with its owner — filter, certify and export"
      action={
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-56">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search reading title…"
              aria-label="Search readings by title"
              className="w-full rounded-control border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-800 transition placeholder:text-slate-500 focus:border-primary-400 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            />
          </div>
          <Segmented
            label="Reading type filter"
            value={type}
            onChange={setType}
            options={TYPE_FILTERS}
          />
          <Segmented
            label="Review state filter"
            value={reviewed}
            onChange={setReviewed}
            options={REVIEW_FILTERS}
          />
        </div>
      }
    >
      <div className="mb-4">
        <div className="mb-1.5 flex items-center justify-between text-xs">
          <span className="font-medium text-slate-700">Reviewed by you or a colleague</span>
          <span className="font-bold text-slate-900">
            {reviewedCount} of {data?.total ?? items.length}
          </span>
        </div>
        <MeterBar
          value={data?.total ? reviewedCount / data.total : 0}
          tone="emerald"
          label="Share of platform readings reviewed"
        />
      </div>

      {actionError && <InlineError message={actionError} />}

      {loading ? (
        <div className="space-y-3 py-2">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : error ? (
        <ErrorState message={error.message} onRetry={refresh} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={FileTextIcon}
          title="No readings match these filters"
          description="Adjust the filters, or wait for seekers to run new divinations."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                <th className="py-2.5 pr-4">Reading</th>
                <th className="py-2.5 pr-4">Owner</th>
                <th className="py-2.5 pr-4">Spread</th>
                <th className="py-2.5 pr-4">State</th>
                <th className="py-2.5 pr-4">Created</th>
                <th className="py-2.5">Reports</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-slate-100 transition last:border-0 hover:bg-slate-50/60"
                >
                  <td className="py-3 pr-4">
                    <Link
                      href={`/readings/${row.id}`}
                      className="font-medium text-slate-800 transition hover:text-primary-700"
                    >
                      {row.title}
                    </Link>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {row.type === "palm" ? "Palm analysis" : "Tarot spread"}
                      {row.card_count ? ` · ${row.card_count} ${row.type === "palm" ? "lines" : "cards"}` : ""}
                      {row.ai_interpreted ? " · AI insight ready" : ""}
                    </p>
                  </td>
                  <td className="py-3 pr-4 text-xs text-slate-600">{row.owner_email || "—"}</td>
                  <td className="py-3 pr-4 text-xs text-slate-600">{row.spread_name || "—"}</td>
                  <td className="py-3 pr-4">
                    <Badge tone={row.reviewed ? "emerald" : "accent"}>
                      {row.reviewed ? "Reviewed" : "Pending"}
                    </Badge>
                  </td>
                  <td className="py-3 pr-4 text-xs text-slate-500">
                    {new Date(row.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Button
                        size="sm"
                        variant="ghost"
                        icon={DownloadIcon}
                        loading={isBusy(row, "pdf")}
                        disabled={busy.id !== null}
                        onClick={() => exportPdf(row)}
                      >
                        PDF
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        icon={TableIcon}
                        loading={isBusy(row, "excel")}
                        disabled={busy.id !== null}
                        onClick={() => exportExcel(row)}
                      >
                        Excel
                      </Button>
                      {!row.reviewed && (
                        <Button
                          size="sm"
                          variant="secondary"
                          icon={CheckIcon}
                          loading={isBusy(row, "certify")}
                          disabled={busy.id !== null}
                          onClick={() => certify(row)}
                        >
                          Certify
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-slate-500">
            Showing {items.length} of {data?.total ?? items.length} reading(s).
          </p>
        </div>
      )}
    </Panel>
  );
}
