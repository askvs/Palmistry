// Recent Clients table (dashboard slice).
import { Button, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import { ArrowRightIcon, EyeIcon } from "@/components/icons";
import {
  ClientAvatar,
  SectionError,
  SourceBadge,
  TrendBadge,
} from "@/components/consultant/shared";
import { READING_TYPE_LABELS } from "@/services/consultantDemoData";
import { formatDate, relativeLabel } from "@/lib/format";

function TableRow({ client, onStartConsultation }) {
  return (
    <tr className="transition-colors hover:bg-slate-50/70">
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-3">
          <ClientAvatar name={client.name} size="sm" />
          <div className="min-w-0">
            <p className="truncate text-[13px] font-semibold text-slate-900">{client.name}</p>
            <p className="truncate text-xs text-slate-500 tabular-nums">
              {client.ageGroup || "—"} · {client.consultationCount} consultation
              {client.consultationCount === 1 ? "" : "s"}
            </p>
          </div>
        </div>
      </td>
      <td className="px-4 py-2.5 text-[13px] text-slate-600 tabular-nums">
        {client.latestReadingAt ? formatDate(client.latestReadingAt) : "—"}
      </td>
      <td className="px-4 py-2.5 text-[13px] text-slate-600">
        {READING_TYPE_LABELS[client.latestReading] || client.latestReading || "—"}
      </td>
      <td className="px-4 py-2.5">
        <TrendBadge trend={client.trend} />
      </td>
      <td className="px-4 py-2.5 text-[13px] text-slate-600 tabular-nums">
        {relativeLabel(client.lastConsultationAt)}
      </td>
      <td className="px-4 py-2.5">
        <div className="flex items-center justify-end gap-2">
          <Button href={`/consultant/clients/${client.id}`} variant="secondary" size="sm" icon={EyeIcon}>
            View
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onStartConsultation?.(client)}>
            Start consultation
          </Button>
        </div>
      </td>
    </tr>
  );
}

function CardRow({ client, onStartConsultation }) {
  return (
    <li className="p-4">
      <div className="flex items-start gap-3">
        <ClientAvatar name={client.name} size="md" />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-[13px] font-semibold text-slate-900">{client.name}</p>
              <p className="truncate text-xs text-slate-500 tabular-nums">
                {client.ageGroup || "—"} · {client.consultationCount} consultation
                {client.consultationCount === 1 ? "" : "s"}
              </p>
            </div>
            <TrendBadge trend={client.trend} />
          </div>

          <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div>
              <dt className="text-slate-500">Last reading</dt>
              <dd className="font-medium text-slate-700 tabular-nums">
                {client.latestReadingAt ? formatDate(client.latestReadingAt) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Reading type</dt>
              <dd className="font-medium text-slate-700">
                {READING_TYPE_LABELS[client.latestReading] || client.latestReading || "—"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Last consultation</dt>
              <dd className="font-medium text-slate-700 tabular-nums">
                {relativeLabel(client.lastConsultationAt)}
              </dd>
            </div>
          </dl>

          <div className="mt-3 flex items-center gap-2">
            <Button
              href={`/consultant/clients/${client.id}`}
              variant="secondary"
              size="sm"
              icon={EyeIcon}
              fullWidth
            >
              View client
            </Button>
            <Button size="sm" variant="ghost" onClick={() => onStartConsultation?.(client)}>
              Start
            </Button>
          </div>
        </div>
      </div>
    </li>
  );
}

export default function RecentClients({
  clients = [],
  source,
  loading = false,
  error = null,
  onRetry,
  onStartConsultation,
  limit = 6,
}) {
  const rows = clients.slice(0, limit);

  return (
    <Panel
      title="Recent Clients"
      subtitle="Who you have been working with most recently"
      action={
        <div className="flex items-center gap-2">
          <SourceBadge source={source} />
          <Button href="/consultant/clients" variant="ghost" size="sm" iconRight={ArrowRightIcon}>
            All clients
          </Button>
        </div>
      }
      padded={false}
    >
      {error ? (
        <div className="p-6 sm:p-7">
          <SectionError title="Unable to load your clients." onRetry={onRetry} />
        </div>
      ) : loading && rows.length === 0 ? (
        <div className="space-y-3 p-6 sm:p-7">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : rows.length === 0 ? (
        <div className="p-6 sm:p-7">
          <EmptyState
            icon={EyeIcon}
            title="No clients yet"
            description="Clients appear here as soon as a seeker starts a conversation with you."
          />
        </div>
      ) : (
        <>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[46rem] border-collapse text-left">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] uppercase tracking-wider text-slate-500">
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Client
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Last reading
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Reading type
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Current trend
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Last consultation
                  </th>
                  <th scope="col" className="px-4 py-3 text-right font-semibold">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((client) => (
                  <TableRow
                    key={client.id}
                    client={client}
                    onStartConsultation={onStartConsultation}
                  />
                ))}
              </tbody>
            </table>
          </div>
          <ul className="divide-y divide-slate-100 md:hidden">
            {rows.map((client) => (
              <CardRow key={client.id} client={client} onStartConsultation={onStartConsultation} />
            ))}
          </ul>
        </>
      )}
    </Panel>
  );
}
