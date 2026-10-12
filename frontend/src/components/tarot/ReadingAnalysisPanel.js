// Spread-level analysis diagnostics for the tarot result page.
import { Badge, Panel } from "@/components/ui";

const ELEMENT_STYLES = {
  Fire: { bar: "bg-rose-400", text: "text-rose-600" },
  Water: { bar: "bg-blue-400", text: "text-blue-600" },
  Air: { bar: "bg-indigo-300", text: "text-indigo-600" },
  Earth: { bar: "bg-emerald-400", text: "text-emerald-600" },
};

function StatChip({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-primary-600">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-900">{value}</p>
    </div>
  );
}

function AnalysisCard({ title, className = "", children }) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-slate-50/60 p-4 ${className}`}>
      <h4 className="text-[11px] font-semibold uppercase tracking-wider text-primary-700">{title}</h4>
      <div className="mt-3 space-y-2.5">{children}</div>
    </div>
  );
}

function Narrative({ children }) {
  return <p className="text-xs leading-relaxed text-slate-600">{children}</p>;
}

function RatioBar({ segments, ariaLabel }) {
  const total = segments.reduce((sum, s) => sum + s.count, 0);
  if (!total) return null;
  return (
    <div
      className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100"
      role="img"
      aria-label={ariaLabel}
    >
      {segments
        .filter((s) => s.count > 0)
        .map((s) => (
          <div
            key={s.label}
            className={s.className}
            style={{ width: `${(s.count / total) * 100}%` }}
            title={`${s.label}: ${s.count}`}
          />
        ))}
    </div>
  );
}

export default function ReadingAnalysisPanel({ analysis }) {
  const arcana = analysis?.arcana_balance;
  const elemental = analysis?.elemental_balance;
  const reversal = analysis?.reversal_analysis;
  const numerology = analysis?.numerology;

  if (!arcana && !elemental && !reversal && !numerology) return null;

  const elementalEntries = Object.entries(elemental?.counts || {});

  return (
    <Panel
      title="Reading Analysis"
      subtitle="Arcana, elemental, reversal, and numerological diagnostics computed behind your draw."
    >
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {arcana && (
          <StatChip
            label="Arcana Balance"
            value={`${arcana.major_arcana} Major • ${arcana.minor_arcana} Minor`}
          />
        )}
        {elemental && (
          <StatChip
            label="Dominant Element"
            value={elemental.dominant_element ? elemental.dominant_element.toUpperCase() : "Balanced"}
          />
        )}
        {reversal && (
          <StatChip
            label="Reversals"
            value={`${reversal.reversed_count} Reversed • ${reversal.upright_count} Upright`}
          />
        )}
        {numerology && (
          <StatChip
            label="Numerology"
            value={
              numerology.repeats?.length
                ? `${numerology.repeats.length} repeating number(s)`
                : "Harmonic distribution"
            }
          />
        )}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        {arcana && (
          <AnalysisCard title="Arcana Balance">
            <RatioBar
              ariaLabel={`Arcana mix: ${arcana.major_arcana} major, ${arcana.minor_arcana} minor`}
              segments={[
                { label: "Major", count: arcana.major_arcana, className: "bg-primary-600" },
                { label: "Minor", count: arcana.minor_arcana, className: "bg-accent-300" },
              ]}
            />
            <p className="text-xs font-medium text-slate-700">
              {arcana.major_arcana} Major • {arcana.minor_arcana} Minor
              {typeof arcana.major_ratio === "number" &&
                ` • ${Math.round(arcana.major_ratio * 100)}% Major Arcana`}
            </p>
            <Narrative>{arcana.narrative}</Narrative>
          </AnalysisCard>
        )}

        {reversal && (
          <AnalysisCard title="Reversal Current">
            <RatioBar
              ariaLabel={`Orientation mix: ${reversal.upright_count} upright, ${reversal.reversed_count} reversed`}
              segments={[
                { label: "Upright", count: reversal.upright_count, className: "bg-accent-400" },
                { label: "Reversed", count: reversal.reversed_count, className: "bg-primary-500" },
              ]}
            />
            <p className="text-xs font-medium text-slate-700">
              {reversal.upright_count} Upright • {reversal.reversed_count} Reversed
              {typeof reversal.reversal_ratio === "number" &&
                ` • ${Math.round(reversal.reversal_ratio * 100)}% reversed`}
            </p>
            <Narrative>{reversal.narrative}</Narrative>
          </AnalysisCard>
        )}

        {elemental && (
          <AnalysisCard title="Elemental Balance" className={arcana || reversal ? "" : "lg:col-span-2"}>
            <div className="space-y-2">
              {elementalEntries.map(([element, count]) => {
                const style = ELEMENT_STYLES[element] || { bar: "bg-slate-300", text: "text-slate-600" };
                return (
                  <div key={element} className="flex items-center gap-2.5">
                    <span className={`w-12 shrink-0 text-[11px] font-semibold ${style.text}`}>
                      {element}
                    </span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full ${style.bar}`}
                        style={{ width: `${count > 0 ? Math.max((count / elementalEntries.reduce((s, [, c]) => s + c, 0)) * 100, 8) : 0}%` }}
                        title={`${element}: ${count}`}
                      />
                    </div>
                    <span className="w-14 shrink-0 text-right text-[11px] text-slate-500">
                      {count} card{count === 1 ? "" : "s"}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
              {elemental.dominant_element && (
                <Badge tone="primary">Dominant: {elemental.dominant_element}</Badge>
              )}
              {(elemental.missing_elements || []).map((el) => (
                <Badge key={el} tone="rose">
                  No {el}
                </Badge>
              ))}
            </div>
            <Narrative>{elemental.narrative}</Narrative>
          </AnalysisCard>
        )}

        {numerology && (
          <AnalysisCard
            title="Numerological Resonance"
            className={arcana || reversal || elemental ? "lg:col-span-2" : ""}
          >
            {numerology.repeats?.length ? (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {numerology.repeats.map((r, i) => (
                  <div
                    key={r.number ?? i}
                    className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-accent-200 bg-accent-50 font-display text-sm font-bold text-accent-700">
                      {r.number}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-800">
                        {r.count}&times; Number {r.number}
                      </p>
                      {r.cards?.length > 0 && (
                        <p className="mt-0.5 truncate text-[11px] text-slate-500" title={r.cards.join(", ")}>
                          {r.cards.join(" • ")}
                        </p>
                      )}
                      {r.meaning && (
                        <p className="mt-1 text-[11px] leading-relaxed text-slate-600">{r.meaning}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs italic text-slate-500">
                Every card carries a distinct number — no repeating vibration dominates this draw.
              </p>
            )}
            <Narrative>{numerology.narrative}</Narrative>
          </AnalysisCard>
        )}
      </div>
    </Panel>
  );
}
