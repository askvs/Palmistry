// Client Tarot Reading History.
import { useState } from "react";
import { Badge, Button, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import { CardsIcon, EyeIcon } from "@/components/icons";
import {
  SectionError,
  SourceBadge,
  GuidanceDisclaimer,
} from "@/components/consultant/shared";
import { formatDate } from "@/lib/format";

function ReadingDetail({ entry }) {
  return (
    <div className="mt-3 rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Cards drawn</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {entry.cards.map((card) => (
          <span
            key={card}
            className="rounded-xl border border-accent-200 bg-accent-50 px-2.5 py-1 text-xs font-medium text-accent-900"
          >
            {card}
          </span>
        ))}
      </div>
      <p className="mt-3 text-sm leading-relaxed text-slate-700">{entry.summary}</p>
      {entry.readingId ? (
        <Button
          href={`/readings/${entry.readingId}`}
          variant="secondary"
          size="sm"
          className="mt-3"
          iconRight={EyeIcon}
        >
          Open full reading
        </Button>
      ) : null}
    </div>
  );
}

export default function TarotHistoryTable({
  rows = [],
  source,
  loading = false,
  error = null,
  onRetry,
}) {
  const [openId, setOpenId] = useState(null);

  const body = () => {
    if (error) {
      return <SectionError title="Unable to load tarot history." onRetry={onRetry} />;
    }
    if (loading) {
      return (
        <div className="space-y-3">
          <SkeletonRow lines={2} />
          <SkeletonRow lines={2} />
          <SkeletonRow lines={2} />
        </div>
      );
    }
    if (rows.length === 0) {
      return (
        <EmptyState
          icon={CardsIcon}
          title="No tarot readings yet"
          description="Tarot readings completed by this client will appear here."
        />
      );
    }
    return (
      <ul className="space-y-3">
        {rows.map((entry) => (
          <li
            key={entry.id}
            className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-primary-200"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900">{entry.spread}</span>
                  <Badge tone="accent">{entry.topic}</Badge>
                </div>
                <p className="mt-0.5 text-xs text-slate-500">{formatDate(entry.date)}</p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                icon={EyeIcon}
                onClick={() => setOpenId(openId === entry.id ? null : entry.id)}
              >
                {openId === entry.id ? "Hide" : "View"}
              </Button>
            </div>

            <p className="mt-2.5 text-sm leading-relaxed text-slate-700">{entry.summary}</p>
            {openId === entry.id && <ReadingDetail entry={entry} />}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <Panel
      title="Tarot Reading History"
      subtitle="Spreads this client has completed, newest first"
      action={<SourceBadge source={source} />}
    >
      <div className="space-y-4">
        {body()}
        <GuidanceDisclaimer>
          Tarot readings are reflective prompts chosen from a shuffled deck. They describe themes
          to consider, not events that will happen.
        </GuidanceDisclaimer>
      </div>
    </Panel>
  );
}
