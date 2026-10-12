// User-engagement insights for the tarot reader (FR-036).
import { useCallback, useState } from "react";
import {
  EmptyState,
  ErrorState,
  Panel,
  SkeletonRow,
} from "@/components/ui";
import { MeterBar, Segmented, StatCard } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { readerEngagement } from "@/services/reader";
import {
  ActivityIcon,
  ChartIcon,
  CardsIcon,
  RepeatIcon,
  UsersIcon,
} from "@/components/icons";

const PERIOD_OPTIONS = [
  { value: "7", label: "7 days" },
  { value: "30", label: "30 days" },
  { value: "90", label: "90 days" },
];

export default function ReaderEngagementPanel() {
  const [days, setDays] = useState(30);
  const loader = useCallback(() => readerEngagement(days), [days]);
  const { data, error, loading } = useAsyncData(loader);

  const engagement = data;

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-4">
        <StatCard
          label="Querents"
          value={engagement ? engagement.unique_querents : loading ? "—" : 0}
          tone="primary"
          icon={UsersIcon}
          hint="Distinct seekers who ran a reading"
        />
        <StatCard
          label="Returning Querents"
          value={engagement ? engagement.repeat_querents : loading ? "—" : 0}
          tone="emerald"
          icon={RepeatIcon}
          hint={
            engagement
              ? `${Math.round(engagement.repeat_rate * 100)}% of querents came back`
              : "Two or more readings"
          }
        />
        <StatCard
          label={`Active (${days}d)`}
          value={engagement ? engagement.active_querents_in_window : loading ? "—" : 0}
          tone="blue"
          icon={ActivityIcon}
          hint={
            engagement
              ? `${engagement.returning_querents_in_window} returning · ${engagement.first_time_querents_in_window} first-time`
              : "Seekers who read in the window"
          }
        />
        <StatCard
          label="Readings per Querent"
          value={engagement ? engagement.readings_per_querent.toFixed(2) : loading ? "—" : 0}
          tone="accent"
          icon={CardsIcon}
          hint={engagement ? `${engagement.total_readings} readings in total` : "Average depth"}
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel
          title="Top Querents"
          subtitle="Most engaged accounts and when they last read"
        >
          {loading ? (
            <SkeletonRow lines={4} />
          ) : error ? (
            <ErrorState message={error.message} />
          ) : !engagement || engagement.top_querents.length === 0 ? (
            <EmptyState
              icon={UsersIcon}
              title="No querent activity yet"
              description="Engagement insights appear once seekers start reading."
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {engagement.top_querents.map((querent) => (
                <li key={querent.user_id} className="-mx-2 rounded-lg px-2 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-slate-800">
                      {querent.full_name || querent.email}
                    </span>
                    <span className="text-xs font-bold text-slate-900">
                      {querent.reading_count} reading{querent.reading_count === 1 ? "" : "s"}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-slate-500">{querent.email}</p>
                  <div className="mt-1.5">
                    <MeterBar
                      value={
                        engagement.top_querents[0]?.reading_count
                          ? querent.reading_count / engagement.top_querents[0].reading_count
                          : 0
                      }
                      tone="primary"
                      label={`${querent.email} reading share of the top querent`}
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    Last read {new Date(querent.last_reading_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title="Popular Spreads"
          subtitle="Which tarot spreads seekers actually draw"
        >
          {loading ? (
            <SkeletonRow lines={4} />
          ) : error ? (
            <ErrorState message={error.message} />
          ) : !engagement || engagement.popular_spreads.length === 0 ? (
            <EmptyState
              icon={ChartIcon}
              title="No tarot activity yet"
              description="Spread popularity appears once tarot readings are recorded."
            />
          ) : (
            <div className="space-y-3.5">
              {engagement.popular_spreads.map((spread) => (
                <div key={spread.spread}>
                  <div className="mb-1.5 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">{spread.spread}</span>
                    <span className="font-bold text-slate-900">{spread.count}</span>
                  </div>
                  <MeterBar
                    value={
                      engagement.popular_spreads[0]?.count
                        ? spread.count / engagement.popular_spreads[0].count
                        : 0
                    }
                    tone="accent"
                    label={`${spread.spread} share of the most drawn spread`}
                  />
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-400">
          Review coverage: {engagement ? Math.round(engagement.review_rate * 100) : 0}% of
          readings have been reviewed by a reader.
        </p>
        <Segmented
          label="Engagement window"
          value={String(days)}
          onChange={(value) => setDays(Number(value))}
          options={PERIOD_OPTIONS}
        />
      </div>
    </div>
  );
}
