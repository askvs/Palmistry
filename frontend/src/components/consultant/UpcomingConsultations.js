// Upcoming Consultations — today's schedule for the consultant.
import { Button, EmptyState, Panel, SkeletonRow } from "@/components/ui";
import {
  CalendarIcon,
  ChatIcon,
  ClockIcon,
  PlayIcon,
} from "@/components/icons";
import {
  ClientAvatar,
  SectionError,
  SourceBadge,
  StatusBadge,
} from "@/components/consultant/shared";
import { initialsOf } from "@/lib/format";
import { formatDate } from "@/lib/format";

// Resolve which client a scheduled session belongs to.
function resolveClient(session, roster) {
  if (session.liveClientUserId) {
    return roster.find((client) => client.liveUserId === session.liveClientUserId) || null;
  }
  return roster.find((client) => client.id === session.clientId) || null;
}

export default function UpcomingConsultations({ sessions = [], roster = [], source, loading, error, onRetry }) {
  const renderBody = () => {
    if (error) {
      return <SectionError title="Unable to load your schedule." onRetry={onRetry} />;
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
    if (sessions.length === 0) {
      return (
        <EmptyState
          icon={CalendarIcon}
          title="No consultations scheduled"
          description="Upcoming sessions will appear here once a seeker books time with you."
          action={
            <Button href="/consultant/clients" variant="secondary" size="sm">
              Browse clients
            </Button>
          }
        />
      );
    }

    return (
      <ul className="space-y-3">
        {sessions.map((session) => {
          const client = resolveClient(session, roster);
          const name = client?.name || session.liveClientName || "Seeker";
          const detailHref = client
            ? `/consultant/clients/${client.id}`
            : "/consultant/clients";

          return (
            <li
              key={session.id}
              className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-primary-200 hover:shadow-md sm:flex-nowrap"
            >
              <div className="flex w-16 shrink-0 flex-col items-center justify-center rounded-xl bg-primary-50 px-2 py-2 text-primary-700 ring-1 ring-primary-100">
                <ClockIcon className="h-3.5 w-3.5" />
                <span className="mt-1 text-sm font-bold tracking-tight">{session.time}</span>
              </div>

              <ClientAvatar name={name} size="md" />

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-900">{name}</p>
                <p className="mt-0.5 truncate text-xs text-slate-500">
                  {session.type} · {formatDate(session.date)}
                </p>
              </div>

              <StatusBadge status={session.status} />

              <div className="flex shrink-0 items-center gap-2">
                <Button href={detailHref} variant="secondary" size="sm">
                  View
                </Button>
                {session.status === "in_progress" ? (
                  <Button href={detailHref} size="sm" icon={PlayIcon}>
                    Resume
                  </Button>
                ) : (
                  <Button href={detailHref} size="sm" icon={ChatIcon}>
                    Start
                  </Button>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <Panel
      title="Upcoming Consultations"
      subtitle="Your scheduled sessions and who they are with"
      action={<SourceBadge source={source} />}
    >
      {renderBody()}
    </Panel>
  );
}
