// Consultations: live threads plus recorded client sessions in one list.
import Head from "next/head";
import { useRouter } from "next/router";
import { useState } from "react";
import { Button, EmptyState, Panel } from "@/components/ui";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { ArrowRightIcon, CalendarIcon, ChatIcon } from "@/components/icons";
import { fetchConsultantWorkspace } from "@/services/consultant";
import { DEMO_CLIENTS } from "@/services/consultantDemoData";
import {
  ClientAvatar,
  SectionError,
  SourceBadge,
  StatusBadge,
  TrendBadge,
} from "@/components/consultant/shared";
import { formatDateTime, relativeLabel } from "@/lib/format";

const TABS = [
  { value: "all", label: "All" },
  { value: "open", label: "Open" },
  { value: "resolved", label: "Resolved" },
];

export default function ConsultantConsultationsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const { data, error, loading, refresh } = useAsyncData(fetchConsultantWorkspace, {
    enabled: !authLoading && !!user,
  });

  const [tab, setTab] = useState("all");

  const queueItems = data?.queue?.items || [];
  const roster = data?.roster || [];

  const rosterByUserId = new Map(
    roster.filter((client) => client.liveUserId).map((client) => [client.liveUserId, client])
  );

  const liveRows = queueItems
    .filter((thread) => (tab === "all" ? true : thread.status === tab))
    .map((thread) => ({
      id: thread.id,
      href: `/consultant/consultations/${thread.id}`,
      title: thread.topic,
      clientName:
        rosterByUserId.get(thread.user_id)?.name || `Seeker ${String(thread.user_id).slice(0, 8)}`,
      clientId: rosterByUserId.get(thread.user_id)?.id || null,
      status: thread.status,
      when: thread.updated_at || thread.created_at,
      meta: thread.guidance ? "Counsel dispatched" : "Awaiting your reply",
      trend: rosterByUserId.get(thread.user_id)?.trend || null,
      source: "live",
    }));

  const historyRows = DEMO_CLIENTS.flatMap((client) =>
    client.consultations
      .filter((session) => session.type !== "live_thread")
      .map((session) => ({
        id: session.id,
        href: `/consultant/consultations/${session.id}`,
        title: session.purpose,
        clientName: client.name,
        clientId: client.id,
        status: session.status,
        when: session.startedAt,
        meta: session.durationMinutes ? `${session.durationMinutes} min session` : "Session record",
        trend: client.trend,
        source: "demo",
      }))
  );

  const rows = [...liveRows, ...historyRows].sort(
    (a, b) => new Date(b.when || 0) - new Date(a.when || 0)
  );

  return (
    <div className="animate-fade-in space-y-8">
      <Head>
        <title>Consultations | Palmistry &amp; Tarot</title>
      </Head>

      <Panel
        title="Consultations"
        subtitle="Live guidance threads and your recorded sessions"
        action={
          <div className="flex flex-wrap items-center gap-2">
            {TABS.map((option) => (
              <button
                key={option.value}
                type="button"
                aria-pressed={tab === option.value}
                onClick={() => setTab(option.value)}
                className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                  tab === option.value
                    ? "bg-primary-600 text-white shadow-sm shadow-primary-600/25"
                    : "bg-white text-slate-600 ring-1 ring-slate-200 hover:text-slate-900"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        }
      >
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span className="inline-flex items-center gap-1.5">
              <ChatIcon className="h-3.5 w-3.5 text-emerald-600" />
              {queueItems.length} live thread{queueItems.length === 1 ? "" : "s"}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CalendarIcon className="h-3.5 w-3.5 text-slate-400" />
              {historyRows.length} recorded session{historyRows.length === 1 ? "" : "s"}
            </span>
          </div>

          {error ? (
            <SectionError title="Unable to load your consultations." onRetry={refresh} />
          ) : loading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading consultations…</p>
          ) : rows.length === 0 ? (
            <EmptyState
              icon={ChatIcon}
              title="No consultations yet"
              description="Your upcoming and completed consultations will appear here."
              action={
                <Button href="/consultant/clients" variant="secondary" size="sm">
                  Browse clients
                </Button>
              }
            />
          ) : (
            <ul className="space-y-3">
              {rows.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    onClick={() => router.push(row.href)}
                    className="flex w-full cursor-pointer flex-wrap items-center gap-3 rounded-2xl border border-slate-200/90 bg-white p-4 text-left shadow-xs transition hover:border-primary-200 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:flex-nowrap"
                  >
                    <ClientAvatar name={row.clientName} size="md" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate text-sm font-semibold text-slate-900">{row.title}</p>
                        <span className="text-xs text-slate-500">· {row.clientName}</span>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-slate-500">
                        {formatDateTime(row.when)} · {row.meta} · {relativeLabel(row.when)}
                      </p>
                    </div>

                    {row.trend && <TrendBadge trend={row.trend} />}
                    <StatusBadge status={row.status} />
                    <SourceBadge source={row.source} />
                    <span className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-primary-600">
                      Open
                      <ArrowRightIcon className="h-3.5 w-3.5" />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Panel>
    </div>
  );
}
