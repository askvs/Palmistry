// Tarot Reader dashboard: manage readings, analytics, sessions, reports (FR-004).
import { useState } from "react";
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
import { StatCard, PerDayBars, Segmented } from "@/components/dashboards/shared";
import ReaderEngagementPanel from "@/components/reader/ReaderEngagementPanel";
import { useAsyncData } from "@/hooks/useAsyncData";
import { fetchReaderDashboard, readerReviewReading } from "@/services/roles";
import {
  ActivityIcon,
  ArrowRightIcon,
  CardsIcon,
  CheckIcon,
  ChartIcon,
  ClockIcon,
  FileTextIcon,
  HandIcon,
  TableIcon,
} from "@/components/icons";

// Kit badge tones per reading type.
const TYPE_TONES = { palm: "primary", tarot: "accent" };

export default function ReaderDashboard() {
  const { data, error, loading, refresh } = useAsyncData(fetchReaderDashboard);
  const toast = useToast();
  const readings = data?.readings;
  const analytics = data?.analytics;

  const [activeTab, setActiveTab] = useState("all"); // 'all' | 'pending' | 'completed'
  const [busyId, setBusyId] = useState(null);
  const [actionError, setActionError] = useState(null);

  async function completeReading(e, reading) {
    e.preventDefault();
    e.stopPropagation();
    setBusyId(reading.id);
    setActionError(null);
    try {
      await readerReviewReading(reading.id, { status: "completed" });
      toast.success("Reading certified", `"${reading.title}" has been marked as reviewed.`);
      await refresh();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  const allItems = readings?.items || [];
  const filteredItems = allItems.filter((item) => {
    if (activeTab === "pending") return item.status === "pending";
    if (activeTab === "completed") return item.status === "completed";
    return true;
  });

  return (
    <div className="space-y-8">
      {error && <ErrorState message={error.message} onRetry={refresh} />}
      {actionError && <InlineError message={actionError} />}

      {/* Analytics stat grid */}
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Total Consultations"
          value={analytics ? analytics.total : loading ? "—" : 0}
          tone="accent"
          icon={ActivityIcon}
          hint="All time platform readings"
        />
        <StatCard
          label="Pending Review"
          value={
            analytics
              ? (analytics.by_status.find((s) => s.status === "pending")?.count ?? 0)
              : loading ? "—" : 0
          }
          tone="primary"
          icon={ClockIcon}
          hint="Awaiting consultant verification"
        />
        <StatCard
          label="Tarot Spread Sessions"
          value={
            analytics
              ? (analytics.by_type.find((t) => t.type === "tarot")?.count ?? 0)
              : loading ? "—" : 0
          }
          tone="accent"
          icon={CardsIcon}
          hint="Major & minor arcana"
        />
        <StatCard
          label="Palm Analysis Sessions"
          value={
            analytics
              ? (analytics.by_type.find((t) => t.type === "palm")?.count ?? 0)
              : loading ? "—" : 0
          }
          tone="emerald"
          icon={HandIcon}
          hint="Dermatoglyphic & line analysis"
        />
      </div>

      {/* Reading sessions queue with tab filters */}
      <Panel
        title="Querent Reading Queue"
        subtitle="Review, analyze, and certify querent divinations"
        action={
          <Segmented
            label="Reading queue filter"
            value={activeTab}
            onChange={setActiveTab}
            options={[
              { value: "all", label: `All (${allItems.length})` },
              { value: "pending", label: `Pending (${allItems.filter((i) => i.status === "pending").length})` },
              { value: "completed", label: `Completed (${allItems.filter((i) => i.status === "completed").length})` },
            ]}
          />
        }
      >
        {loading ? (
          <div className="space-y-3 py-2">
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
            <SkeletonRow lines={3} />
          </div>
        ) : filteredItems.length === 0 ? (
          <EmptyState
            icon={FileTextIcon}
            title="No readings found"
            description={`No readings match the selected filter (${activeTab}).`}
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {filteredItems.slice(0, 15).map((reading) => (
              <li key={reading.id}>
                <Link
                  href={`/readings/${reading.id}`}
                  className="-mx-2 flex flex-col justify-between gap-3 rounded-xl px-3 py-3.5 transition group hover:bg-slate-50/80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:flex-row sm:items-center"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="truncate text-sm font-semibold text-slate-800 transition group-hover:text-primary-700">
                        {reading.title}
                      </p>
                      <Badge tone={TYPE_TONES[reading.type] || "slate"}>{reading.type}</Badge>
                    </div>
                    <p className="mt-0.5 truncate text-xs text-slate-500">
                      {new Date(reading.created_at).toLocaleString()}
                      {reading.reviewed_by ? " · Verified by reader" : " · Querent self-drawn"}
                      {reading.summary ? ` · ${reading.summary}` : ""}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-2 self-end sm:self-auto">
                    <Badge tone={reading.status === "completed" ? "emerald" : "accent"}>
                      {reading.status}
                    </Badge>
                    {reading.status !== "completed" ? (
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={CheckIcon}
                        loading={busyId === reading.id}
                        onClick={(e) => completeReading(e, reading)}
                      >
                        Verify & certify
                      </Button>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-400 transition group-hover:text-primary-600">
                        View details
                        <ArrowRightIcon className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {/* Reading frequency chart */}
      <Panel
        title="Weekly Reading Frequency"
        subtitle="Divination activity volume over the last 7 calendar days"
      >
        {!analytics || analytics.per_day.length === 0 ? (
          <EmptyState
            icon={ChartIcon}
            title="No activity in this period"
            description="No reading activity has been recorded in the last 7 days."
          />
        ) : (
          <PerDayBars
            ariaLabel="Daily reading frequency"
            series={[
              {
                key: "readings",
                label: "Readings",
                barClass: "bg-gradient-to-t from-accent-500 to-accent-300",
                swatchClass: "bg-accent-500",
                data: analytics.per_day,
              },
            ]}
          />
        )}
      </Panel>

      {/* User engagement insights (FR-036) */}
      <ReaderEngagementPanel />

      {/* Reader workspace entry points: report management and spread. */}
      <Panel
        title="Reader Workspace"
        subtitle="Report management and spread authoring live in their own sections"
      >
        <div className="flex flex-wrap gap-3">
          <Button href="/reader/reports" variant="secondary" icon={TableIcon}>
            Reading reports
          </Button>
          <Button href="/reader/spreads" variant="secondary" icon={CardsIcon}>
            Spread studio
          </Button>
        </div>
        <p className="mt-3 text-xs text-slate-400">
          Certification marks a reading as reviewed. Reports export as a publication-grade PDF
          or a multi-sheet Excel workbook.
        </p>
      </Panel>
    </div>
  );
}
