// My Clients — client-management directory.
import { Button, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import { ArrowUpDownIcon, ChatIcon, EyeIcon, SearchIcon, SlidersIcon, UsersIcon } from "@/components/icons";
import {
  ClientAvatar,
  ClientStatusBadge,
  SectionError,
  SourceBadge,
  TrendBadge,
} from "@/components/consultant/shared";
import { READING_TYPE_LABELS } from "@/services/consultantDemoData";
import { formatDate, relativeLabel } from "@/lib/format";

const STATUS_FILTERS = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "follow_up", label: "Follow-up Required" },
  { value: "recent", label: "Recently Consulted" },
];

const SORT_OPTIONS = [
  { value: "recent", label: "Most recent" },
  { value: "name", label: "Name (A–Z)" },
  { value: "consultations", label: "Most sessions" },
];

function ClientCard({ client, onStartConsultation }) {
  return (
    <li className="flex flex-col rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs transition hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-md">
      <div className="flex items-start gap-3.5">
        <ClientAvatar name={client.name} size="md" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <h3 className="truncate text-sm font-semibold text-slate-900">{client.name}</h3>
            <ClientStatusBadge status={client.status} />
          </div>
          <p className="mt-0.5 truncate text-xs text-slate-400">
            Age {client.ageGroup || "—"} · {client.consultationCount} session
            {client.consultationCount === 1 ? "" : "s"} · {client.readingCount} reading
            {client.readingCount === 1 ? "" : "s"}
          </p>
        </div>
        <TrendBadge trend={client.trend} />
      </div>

      {client.interests.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {client.interests.map((interest) => (
            <span
              key={interest}
              className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
            >
              {interest}
            </span>
          ))}
        </div>
      )}

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-xs">
        <div>
          <dt className="text-slate-400">Last consultation</dt>
          <dd className="mt-0.5 font-semibold text-slate-800">
            {client.lastConsultationAt ? relativeLabel(client.lastConsultationAt) : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-400">Latest reading</dt>
          <dd className="mt-0.5 font-semibold text-slate-800">
            {client.latestReadingAt ? formatDate(client.latestReadingAt) : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-400">Reading type</dt>
          <dd className="mt-0.5 font-semibold text-slate-800">
            {READING_TYPE_LABELS[client.latestReading] || client.latestReading || "—"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-400">Follow-up</dt>
          <dd className="mt-0.5 font-semibold text-slate-800">
            {client.status === "follow_up" ? "Required" : "Not required"}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex items-center gap-2">
        <Button
          href={`/consultant/clients/${client.id}`}
          size="sm"
          icon={EyeIcon}
          fullWidth
        >
          View profile
        </Button>
        <Button
          variant="secondary"
          size="sm"
          icon={ChatIcon}
          onClick={() => onStartConsultation?.(client)}
        >
          Start
        </Button>
      </div>
    </li>
  );
}

export default function ClientDirectory({
  clients = [],
  source,
  total = 0,
  loading = false,
  error = null,
  onRetry,
  search,
  onSearchChange,
  status,
  onStatusChange,
  sort,
  onSortChange,
  onStartConsultation,
}) {
  return (
    <Panel
      title="Client directory"
      subtitle={`${total} client${total === 1 ? "" : "s"} in your workspace`}
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-5">
        {/* Controls */}
        <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-slate-50/60 p-3.5 lg:flex-row lg:items-center">
          <div className="relative min-w-0 flex-1">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <label htmlFor="client-search" className="sr-only">
              Search clients
            </label>
            <input
              id="client-search"
              type="search"
              value={search}
              onChange={(event) => onSearchChange?.(event.target.value)}
              placeholder="Search by name, interest or reading type…"
              className="h-9 w-full rounded-full border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
              <SlidersIcon className="h-3.5 w-3.5" />
              Status
            </span>
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

            <label className="relative inline-flex items-center">
              <span className="sr-only">Sort clients</span>
              <select
                value={sort}
                onChange={(event) => onSortChange?.(event.target.value)}
                className="h-8 cursor-pointer appearance-none rounded-full border border-slate-200 bg-white pl-3 pr-8 text-xs font-medium text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    Sort: {option.label}
                  </option>
                ))}
              </select>
              <ArrowUpDownIcon className="pointer-events-none absolute right-2.5 h-3.5 w-3.5 text-slate-400" />
            </label>
          </div>
        </div>

        {/* Results */}
        {error ? (
          <SectionError title="Unable to load your clients." onRetry={onRetry} />
        ) : loading ? (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            <SkeletonRow lines={5} />
            <SkeletonRow lines={5} />
            <SkeletonRow lines={5} />
          </div>
        ) : clients.length === 0 ? (
          <EmptyState
            icon={UsersIcon}
            title={total === 0 ? "No clients yet" : "No clients match this filter"}
            description={
              total === 0
                ? "Clients appear here as soon as a seeker starts a conversation with you."
                : "Try a different status filter or clear the search."
            }
            action={
              total === 0 ? (
                <Button variant="secondary" size="sm" href="/consultant/consultations">
                  Open consultations
                </Button>
              ) : (
                <Button variant="secondary" size="sm" onClick={() => onStatusChange?.("all")}>
                  Show all clients
                </Button>
              )
            }
          />
        ) : (
          <ul className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {clients.map((client) => (
              <ClientCard
                key={client.id}
                client={client}
                onStartConsultation={onStartConsultation}
              />
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}
