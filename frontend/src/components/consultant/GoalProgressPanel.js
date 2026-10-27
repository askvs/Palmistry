// Goal progress for one client (Spiritual Consultant: analyze users' progress toward personal-development goals).
import { Panel } from "@/components/ui";
import { MeterBar } from "@/components/dashboards/shared";
import { SourceBadge } from "@/components/consultant/shared";
import { TargetIcon } from "@/components/icons";

function ActivityRow({ label, value, hint }) {
  return (
    <div className="rounded-card border border-slate-100 bg-slate-50/60 p-3 transition hover:border-primary-100">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-0.5 text-lg font-bold text-slate-900 tabular-nums">{value}</p>
      {hint && <p className="text-[11px] text-slate-500">{hint}</p>}
    </div>
  );
}

export default function GoalProgressPanel({ client }) {
  const goals = client?.goals || [];
  const engagement = client?.engagement || null;
  const readings = engagement?.readings ?? client?.readingCount ?? 0;
  const recent = engagement?.readings_last_30_days ?? null;
  const threads = engagement?.threads ?? client?.consultationCount ?? 0;
  const resolved = engagement?.resolved_threads ?? 0;
  const resolutionShare = threads ? resolved / threads : 0;

  return (
    <Panel
      title="Personal-Development Goals"
      subtitle="The seeker's recorded spiritual goals, paired with their real activity"
      action={<SourceBadge source={client?.source || "demo"} />}
    >
      <div className="grid gap-5 lg:grid-cols-2">
        <div>
          {goals.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-10 text-center">
              <TargetIcon className="mx-auto h-6 w-6 text-slate-400" />
              <h3 className="mt-3 text-sm font-semibold text-slate-900">No goals recorded</h3>
              <p className="mx-auto mt-1.5 max-w-sm text-sm leading-relaxed text-slate-500">
                This seeker has not recorded any personal-development goals yet. Ask them to add
                goals in their profile so progress can be tracked here.
              </p>
            </div>
          ) : (
            <ul className="space-y-2.5">
              {goals.map((goal, index) => (
                <li
                  key={`${goal}-${index}`}
                  className="rounded-card border border-slate-200/90 bg-white p-4 transition hover:border-primary-200 hover:shadow-xs"
                >
                  <div className="flex items-start gap-3">
                    <span
                      aria-hidden="true"
                      className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-50 text-xs font-bold text-primary-700"
                    >
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium leading-relaxed text-slate-800">{goal}</p>
                      {client?.interests?.length > 0 && (
                        <p className="mt-1 text-[11px] text-slate-500">
                          Related interests: {client.interests.slice(0, 4).join(", ")}
                        </p>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <ActivityRow
              label="Readings"
              value={readings}
              hint={recent !== null ? `${recent} in the last 30 days` : "All time"}
            />
            <ActivityRow
              label="Guidance threads"
              value={threads}
              hint={`${resolved} resolved`}
            />
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">Threads resolved</span>
              <span className="font-bold text-slate-900 tabular-nums">
                {threads ? `${Math.round(resolutionShare * 100)}%` : "—"}
              </span>
            </div>
            <MeterBar
              value={resolutionShare}
              tone="emerald"
              label="Share of this client's guidance threads resolved"
            />
            <p className="mt-1 text-xs text-slate-500">
              Activity, not a measurement of inner progress — the platform never scores a
              seeker&rsquo;s personal growth.
            </p>
          </div>

          {client?.lastConsultationAt && (
            <p className="text-xs text-slate-500">
              Last contact {new Date(client.lastConsultationAt).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </Panel>
  );
}
