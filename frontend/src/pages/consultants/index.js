// Consultant directory with search and filters.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import { Button, EmptyState, ErrorState, InlineError, Panel, PageHeader, SkeletonCards } from "@/components/ui";
import { CompassIcon, SearchIcon, UsersIcon } from "@/components/icons";
import { ConsultantCard } from "@/components/booking/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { fetchConsultants } from "@/services/booking";
import { useAuth } from "@/hooks/useAuth";

const PAGE_SIZE = 24;

const EMPTY_FILTERS = { search: "", specialization: "", maxRate: "" };

// Common tags used across the platform's specialisations; shown as quick filters.
const SUGGESTED_SPECIALIZATIONS = [
  "tarot",
  "palmistry",
  "astrology",
  "love",
  "career",
  "spiritual_growth",
  "numerology",
];

// Read supported filter keys from the URL for dashboard deep links.
function filtersFromQuery(query) {
  const read = (key) => (typeof query[key] === "string" ? query[key] : "");
  return {
    search: read("search"),
    specialization: read("specialization"),
    maxRate: read("max_rate"),
  };
}

export default function ConsultantsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [offset, setOffset] = useState(0);

  // Deep-link the initial filter state (?specialization=love). React's
  // documented "adjust state when a prop changes" pattern: compare during
  // render instead of syncing from an effect.
  const urlFilters = router.isReady ? filtersFromQuery(router.query) : null;
  // `filtersFromQuery` builds a fresh object each render, so compare a stable
  // string key rather than object identity — otherwise this block would call
  // setState on every render and trigger an infinite re-render loop.
  const urlFiltersKey = urlFilters ? JSON.stringify(urlFilters) : null;
  const [appliedUrlFiltersKey, setAppliedUrlFiltersKey] = useState(null);
  if (urlFiltersKey && urlFiltersKey !== appliedUrlFiltersKey) {
    setAppliedUrlFiltersKey(urlFiltersKey);
    setFilters(urlFilters);
    setSearchInput(urlFilters.search);
    setOffset(0);
  }

  const search = filters.search;
  const specialization = filters.specialization;
  const maxRate = filters.maxRate;

  // Debounce the search box so typing doesn't hammer the directory endpoint.
  useEffect(() => {
    const handle = setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: searchInput.trim() }));
      setOffset(0);
    }, 350);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const loader = useCallback(
    () =>
      fetchConsultants({
        search: search || undefined,
        specialization: specialization || undefined,
        max_rate: maxRate || undefined,
        limit: PAGE_SIZE,
        offset,
      }),
    [search, specialization, maxRate, offset],
  );
  const { data, error, loading, refresh } = useAsyncData(loader);
  const consultants = data?.items || [];
  const total = data?.total ?? 0;
  const hasFilters = Boolean(search || specialization || maxRate);

  const canPaginate = useMemo(
    () => ({ next: offset + PAGE_SIZE < total, prev: offset > 0 }),
    [offset, total],
  );

  if (!authLoading && !user) {
    return (
      <div className="animate-fade-in space-y-8">
        <PageHeader
          icon={CompassIcon}
          eyebrow="Live consultations"
          title="Find your consultant"
          description="Sign in to browse consultant profiles and book a live consultation."
          actions={
            <Button href="/login?redirect=/consultants" icon={UsersIcon}>
              Sign in to continue
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-8">
      <PageHeader
        icon={CompassIcon}
        eyebrow="Live consultations"
        title="Find your consultant"
        description="Book a live session with a tarot reader or spiritual consultant. Sessions
          happen over Google Meet."
        gradient="gold"
        actions={
          <Button href="/sessions" variant="secondary" icon={UsersIcon}>
            My sessions
          </Button>
        }
      />

      <Panel
        title="Filters"
        subtitle="Search by name or specialisation, or cap the session rate"
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label
              htmlFor="consultant-search"
              className="text-xs font-bold uppercase tracking-wide text-slate-500"
            >
              Search
            </label>
            <div className="relative mt-1.5">
              <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="consultant-search"
                type="search"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="Tarot, career, a name…"
                className="w-full rounded-2xl border border-slate-200 bg-white py-2.5 pl-9 pr-4 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="consultant-rate"
              className="text-xs font-bold uppercase tracking-wide text-slate-500"
            >
              Max rate
            </label>
            <select
              id="consultant-rate"
              value={maxRate}
              onChange={(event) => {
                setOffset(0);
                setFilters((prev) => ({ ...prev, maxRate: event.target.value }));
              }}
              className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-xs transition focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
            >
              <option value="">Any price</option>
              <option value="25">Up to 25</option>
              <option value="50">Up to 50</option>
              <option value="100">Up to 100</option>
              <option value="200">Up to 200</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Specialisation
            </p>
            <div className="mt-1.5 flex flex-wrap gap-2">
              <button
                type="button"
                aria-pressed={!specialization}
                onClick={() => {
                  setOffset(0);
                  setFilters((prev) => ({ ...prev, specialization: "" }));
                }}
                className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition ${
                  !specialization
                    ? "border-primary-500 bg-primary-50 text-primary-700"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                All
              </button>
              {SUGGESTED_SPECIALIZATIONS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  aria-pressed={specialization === tag}
                  onClick={() => {
                    setOffset(0);
                    setFilters((prev) => ({
                      ...prev,
                      specialization: specialization === tag ? "" : tag,
                    }));
                  }}
                  className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition ${
                    specialization === tag
                      ? "border-primary-500 bg-primary-50 text-primary-700"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {tag.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>
        </div>

        {hasFilters && (
          <div className="mt-4 flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchInput("");
                setFilters(EMPTY_FILTERS);
                setOffset(0);
              }}
            >
              Clear filters
            </Button>
          </div>
        )}
      </Panel>

      {error ? (
        <ErrorState message={error.message} onRetry={refresh} />
      ) : loading ? (
        <SkeletonCards count={6} />
      ) : consultants.length === 0 ? (
        <Panel>
          <EmptyState
            icon={UsersIcon}
            title="No consultants match those filters"
            description="Try widening your search, or clear the filters to see everyone."
            action={
              <Button variant="secondary" size="sm" onClick={refresh}>
                Refresh
              </Button>
            }
          />
        </Panel>
      ) : (
        <>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {consultants.map((consultant) => (
              <ConsultantCard key={consultant.id} consultant={consultant} />
            ))}
          </div>

          {(canPaginate.next || canPaginate.prev) && (
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-slate-500">
                Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!canPaginate.prev}
                  onClick={() => setOffset((v) => Math.max(0, v - PAGE_SIZE))}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!canPaginate.next}
                  onClick={() => setOffset((v) => v + PAGE_SIZE)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
