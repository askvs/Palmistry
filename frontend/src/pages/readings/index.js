import React, { useEffect, useState, useMemo, useCallback } from "react";
import Seo from "@/components/Seo";
import { useRouter } from "next/router";
import { useAuth } from "../../hooks/useAuth";
import { listReadings, deleteReading } from "../../services/readings";
import { downloadReportPdf, downloadReportExcel } from "../../services/reports";
import {
  Button,
  Badge,
  PageHeader,
  EmptyState,
  ErrorState,
  ConfirmDialog,
  SkeletonCards,
  useToast,
} from "@/components/ui";
import {
  ArrowRightIcon,
  CardsIcon,
  FileTextIcon,
  HandIcon,
  ListIcon,
  SearchIcon,
  SparkleIcon,
  TableIcon,
  TrashIcon,
} from "@/components/icons";

const FILTERS = [
  { value: "all", label: "All Readings" },
  { value: "palm", label: "Palmistry" },
  { value: "tarot", label: "Tarot" },
];

export default function ReadingsIndexPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const [readings, setReadings] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalAll, setTotalAll] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadReadings = useCallback(
    async (cancelledRef) => {
      try {
        const typeParam = filterType === "all" ? undefined : filterType;
        const data = await listReadings({ type: typeParam, limit: 100 });
        const items = data.items || [];
        if (cancelledRef?.current) return;
        setReadings(items);
        setTotal(data.total ?? items.length);
        if (filterType === "all") setTotalAll(data.total ?? items.length);
        setError(null);
      } catch (err) {
        if (!cancelledRef?.current) {
          setError(err.message || "Failed to load readings");
        }
      } finally {
        if (!cancelledRef?.current) setLoading(false);
      }
    },
    [filterType]
  );

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/readings");
      return undefined;
    }
    if (!user) {
      return undefined;
    }
    const cancelled = { current: false };
    (async () => {
      try {
        const typeParam = filterType === "all" ? undefined : filterType;
        const data = await listReadings({ type: typeParam, limit: 100 });
        if (cancelled.current) return;
        const items = data.items || [];
        setReadings(items);
        setTotal(data.total ?? items.length);
        if (filterType === "all") setTotalAll(data.total ?? items.length);
        setError(null);
      } catch (err) {
        if (!cancelled.current) {
          setError(err.message || "Failed to load readings");
        }
      } finally {
        if (!cancelled.current) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled.current = true;
    };
  }, [user, authLoading, filterType, router]);

  async function confirmDelete() {
    if (!deleteTarget) return;
    setActionLoadingId(`del-${deleteTarget.id}`);
    try {
      await deleteReading(deleteTarget.id);
      toast.success("Deleted", "Reading removed from your archive");
      setDeleteTarget(null);
      await loadReadings();
    } catch (err) {
      toast.error(
        "Delete failed",
        `${err.message || "The reading could not be removed."} Check your connection and try again.`
      );
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleDownloadPdf(id, title) {
    setActionLoadingId(`pdf-${id}`);
    try {
      await downloadReportPdf(id, `${title || "reading"}-report.pdf`);
      toast.success("PDF dossier exported", "Your reading report has been downloaded.");
    } catch (err) {
      toast.error(
        "Export failed",
        `${err.message || "The PDF report could not be generated."} Check your connection and try again.`
      );
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleDownloadExcel(id, title) {
    setActionLoadingId(`xls-${id}`);
    try {
      await downloadReportExcel(id, `${title || "reading"}-report.xlsx`);
      toast.success("Excel workbook exported", "Your reading analysis has been downloaded.");
    } catch (err) {
      toast.error(
        "Export failed",
        `${err.message || "The Excel workbook could not be generated."} Check your connection and try again.`
      );
    } finally {
      setActionLoadingId(null);
    }
  }

  const filteredReadings = useMemo(() => {
    if (!searchQuery.trim()) return readings;
    const q = searchQuery.toLowerCase();
    return readings.filter(
      (r) =>
        r.title?.toLowerCase().includes(q) ||
        r.summary?.toLowerCase().includes(q) ||
        r.type?.toLowerCase().includes(q)
    );
  }, [readings, searchQuery]);

  const deletePending = Boolean(deleteTarget) && actionLoadingId === `del-${deleteTarget.id}`;

  return (
    <div className="space-y-8">
      <Seo
        title="Reading archives"
        description="Every palm and tarot reading you've saved — revisit, export, or continue the reflection."
      />

      <PageHeader
        icon={ListIcon}
        tileTone="accent"
        eyebrow="Reading Archive"
        title="Your Readings & Reports"
        description="Review your historical palm feature analyses and tarot spread readings. Download publication-grade PDF and Excel intelligence dossiers for any session."
        actions={
          <>
            <Button variant="primary" size="sm" href="/readings/palm" icon={HandIcon}>
              New Palm Scan
            </Button>
            <Button variant="secondary" size="sm" href="/readings/tarot" icon={CardsIcon}>
              New Tarot Draw
            </Button>
          </>
        }
      />

      {/* Filter Controls & Search */}
      <div className="flex flex-col items-stretch justify-between gap-4 sm:flex-row sm:items-center">
        <div className="inline-flex self-start rounded-full border border-slate-200 bg-slate-100 p-[3px]">
          {FILTERS.map((f) => {
            const active = filterType === f.value;
            return (
              <button
                key={f.value}
                type="button"
                aria-pressed={active}
                onClick={() => {
                  if (f.value !== filterType) setLoading(true);
                  setFilterType(f.value);
                }}
                className={`cursor-pointer rounded-full px-4 py-1.5 text-xs font-semibold transition-colors duration-[120ms] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                  active
                    ? "bg-white text-slate-900 shadow-[0_1px_3px_rgba(30,24,54,0.12)]"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {f.label}
                {f.value === "all" && totalAll > 0 ? ` (${totalAll})` : ""}
              </button>
            );
          })}
        </div>

        <div className="relative w-full sm:max-w-xs">
          <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            aria-label="Search readings"
            placeholder="Search readings by title or theme..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-[10px] border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          />
        </div>
      </div>

      {/* 1. LOADING STATE */}
      {loading && <SkeletonCards count={6} />}

      {/* 2. ERROR STATE */}
      {!loading && error && (
        <ErrorState
          title="Unable to load readings"
          message={error}
          onRetry={() => {
            setLoading(true);
            loadReadings();
          }}
        />
      )}

      {/* 3. EMPTY STATE */}
      {!loading && !error && filteredReadings.length === 0 && (
        <EmptyState
          icon={SparkleIcon}
          title={searchQuery ? "No matching readings found" : "No Readings Yet"}
          description={
            searchQuery
              ? "Try a different search query or clear your filter."
              : "Embark on your journey of self-reflection. Perform an AI-powered palm line biometric scan or draw a symbolic tarot spread."
          }
          action={
            !searchQuery && (
              <div className="flex flex-wrap items-center justify-center gap-2.5">
                <Button variant="secondary" size="sm" href="/readings/palm" icon={HandIcon}>
                  Start Palm Scan
                </Button>
                <Button variant="secondary" size="sm" href="/readings/tarot" icon={CardsIcon}>
                  Draw Tarot
                </Button>
              </div>
            )
          }
        />
      )}

      {/* 4. SUCCESS STATE: READINGS GRID */}
      {!loading && !error && filteredReadings.length > 0 && (
        <>
          <p className="text-xs text-slate-500">
            Showing {filteredReadings.length} of {total}{" "}
            {filterType === "all" ? "readings" : `${filterType} readings`}
          </p>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredReadings.map((reading) => {
              const isPalm = reading.type === "palm";
              const dateStr = reading.created_at
                ? new Date(reading.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })
                : "Recent";

              return (
                <div
                  key={reading.id}
                  className="group flex flex-col justify-between surface-card p-6 transition duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-lift"
                >
                  <div>
                    {/* Top Row: Type Tile + Badge + Date */}
                    <div className="mb-4 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                            isPalm ? "bg-primary-600 text-white" : "bg-accent-400 text-slate-900"
                          }`}
                        >
                          {isPalm ? (
                            <HandIcon className="h-[18px] w-[18px]" />
                          ) : (
                            <CardsIcon className="h-[18px] w-[18px]" />
                          )}
                        </span>
                        <Badge tone={isPalm ? "accent" : "primary"}>
                          {isPalm ? "Palm" : "Tarot"}
                        </Badge>
                      </div>
                      <span className="text-xs tabular-nums text-slate-500">{dateStr}</span>
                    </div>

                    {/* Title & Summary */}
                    <h3 className="mb-2 line-clamp-1 font-display text-lg font-semibold tracking-[-0.01em] text-slate-900 transition group-hover:text-primary-700">
                      {reading.title || (isPalm ? "Palm Biometrics" : "Tarot Reading")}
                    </h3>
                    <p className="mb-4 line-clamp-3 text-sm leading-relaxed text-slate-500">
                      {reading.summary || "Complete symbolic interpretation and reflective insights."}
                    </p>
                  </div>

                  {/* Action Toolbar */}
                  <div className="flex flex-col gap-3 border-t border-slate-100 pt-4">
                    <Button
                      variant="secondary"
                      size="sm"
                      fullWidth
                      href={`/readings/${reading.id}`}
                      iconRight={ArrowRightIcon}
                    >
                      View Full Reading
                    </Button>

                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={FileTextIcon}
                          onClick={() => handleDownloadPdf(reading.id, reading.title)}
                          loading={actionLoadingId === `pdf-${reading.id}`}
                          disabled={Boolean(actionLoadingId)}
                        >
                          PDF
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={TableIcon}
                          onClick={() => handleDownloadExcel(reading.id, reading.title)}
                          loading={actionLoadingId === `xls-${reading.id}`}
                          disabled={Boolean(actionLoadingId)}
                        >
                          Excel
                        </Button>
                      </div>

                      <Button
                        variant="dangerGhost"
                        size="sm"
                        icon={TrashIcon}
                        aria-label="Delete reading"
                        onClick={() => setDeleteTarget(reading)}
                        disabled={Boolean(actionLoadingId)}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Ethical Notice */}
      <div className="surface-card p-5 text-center">
        <p className="mx-auto max-w-3xl text-[13px] leading-relaxed text-slate-600">
          <span className="mr-1.5 text-accent-700" aria-hidden="true">
            ✦
          </span>
          <span className="italic">
            Safety &amp; Ethics Notice: All palmistry biometric analyses, tarot spreads, and personal
            intelligence reports are intended strictly for introspective guidance, personal
            reflection, and entertainment. They do not substitute for professional medical,
            psychiatric, or financial counsel.
          </span>
        </p>
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete this reading?"
        message={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.title || "this reading"}"? Its report and notes will be permanently removed. This cannot be undone.`
            : ""
        }
        confirmLabel="Delete Reading"
        loading={deletePending}
        onConfirm={confirmDelete}
        onCancel={() => {
          if (!deletePending) setDeleteTarget(null);
        }}
      />
    </div>
  );
}
