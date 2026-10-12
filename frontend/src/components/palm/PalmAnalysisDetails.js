// Shared palm detail blocks from the CV pipeline.
import { Badge } from "@/components/ui";

const MOUNT_ELEMENT_TONES = {
  Fire: "rose",
  Water: "blue",
  Air: "indigo",
  Earth: "emerald",
};

const FINGER_ORDER = ["thumb", "index", "middle", "ring", "pinky"];

// Per-finger proportion bars + 2D:4D, pinky-reach, and thumb flexibility signals.
export function PalmFingerStructure({ fingerStructure }) {
  if (!fingerStructure) return null;
  const fingers = fingerStructure.fingers || {};
  const ordered = FINGER_ORDER.filter((k) => fingers[k]);

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            2D:4D Digit Ratio
          </div>
          <div className="mt-0.5 font-display text-lg font-bold text-slate-900">
            {fingerStructure.digit_ratio_2d_4d ?? "—"}
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
            {fingerStructure.digit_ratio_interpretation}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Pinky Reach
          </div>
          <div className="mt-0.5 font-display text-lg font-bold text-slate-900">
            {fingerStructure.pinky_reaches_ring_dip ? "Reaches ring joint" : "Falls short"}
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
            {fingerStructure.pinky_trait}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Thumb Posture ({fingerStructure.thumb_angle_degrees}&deg;)
          </div>
          <div className="mt-0.5 font-display text-lg font-bold text-slate-900">
            {fingerStructure.thumb_flexibility?.split(":")[0] || "Measured"}
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
            {fingerStructure.thumb_flexibility}
          </p>
        </div>
      </div>

      {ordered.length > 0 && (
        <div>
          <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Finger length relative to middle finger
          </div>
          <div className="space-y-2.5">
            {ordered.map((key) => {
              const finger = fingers[key];
              const ratio = typeof finger.ratio_to_middle === "number" ? finger.ratio_to_middle : 0;
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="w-14 shrink-0 text-xs font-semibold capitalize text-slate-700">
                    {key}
                  </span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-sky-400 to-violet-500"
                      style={{ width: `${Math.min(ratio * 100, 100)}%` }}
                      title={`${finger.name}: ${finger.length} units`}
                    />
                  </div>
                  <span className="w-12 shrink-0 text-right text-[11px] font-medium text-slate-500">
                    {ratio.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Rich per-mount cards: planetary ruler, element, prominence, meaning, attributes.
export function PalmMountProfiles({ mounts = [] }) {
  if (!Array.isArray(mounts) || mounts.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {mounts.map((mount) => {
        const score = typeof mount.score === "number" ? mount.score : null;
        return (
          <div
            key={mount.mount_id}
            className="flex flex-col rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="font-display text-sm font-bold text-slate-900">
                  {mount.name?.replace("Mount of ", "")}
                </h4>
                <p className="text-[10px] uppercase tracking-wider text-slate-400">
                  Ruled by {mount.planetary_ruler || "—"}
                </p>
              </div>
              {mount.element && (
                <Badge tone={MOUNT_ELEMENT_TONES[mount.element] || "slate"}>{mount.element}</Badge>
              )}
            </div>

            {score !== null && (
              <div className="mt-3">
                <div className="mb-1 flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-slate-600">{mount.prominence || "Measured"}</span>
                  <span className="font-medium text-slate-500">{Math.round(score * 100)}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-accent-400 to-accent-600"
                    style={{ width: `${Math.round(score * 100)}%` }}
                  />
                </div>
              </div>
            )}

            <p className="mt-3 text-[11px] leading-relaxed text-slate-600">{mount.meaning}</p>

            {mount.core_attributes?.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1 border-t border-slate-100 pt-2.5">
                {mount.core_attributes.map((attr, i) => (
                  <span
                    key={i}
                    className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600"
                  >
                    {attr}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Honest per-line detection list with measured quality metrics.
export function PalmLinesList({ lines = [], activeLineId = null, onHoverLine }) {
  if (!Array.isArray(lines) || lines.length === 0) return null;

  return (
    <div className="space-y-3">
      {lines.map((line) => {
        const isHovered = activeLineId != null && activeLineId === line.line_id;
        const interactive = typeof onHoverLine === "function";
        return (
          <div
            key={line.line_id}
            onMouseEnter={interactive ? () => onHoverLine(line.line_id) : undefined}
            onMouseLeave={interactive ? () => onHoverLine(null) : undefined}
            className={`rounded-2xl border p-4 transition ${
              interactive ? "cursor-pointer" : ""
            } ${
              isHovered
                ? "border-violet-500 ring-2 ring-violet-500/20 bg-violet-50/50 shadow-sm"
                : "border-slate-200/80 bg-slate-50/60 hover:border-slate-300 hover:bg-white"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    line.line_id === "life_line"
                      ? "bg-emerald-500"
                      : line.line_id === "head_line"
                        ? "bg-sky-500"
                        : line.line_id === "heart_line"
                          ? "bg-rose-500"
                          : line.line_id === "fate_line"
                            ? "bg-violet-500"
                            : "bg-amber-500"
                  }`}
                />
                <h4 className="text-sm font-bold text-slate-900">{line.name}</h4>
              </div>
              <span className="text-xs italic text-slate-400">{line.classical_name}</span>
            </div>

            <div className="mt-2 flex flex-wrap gap-1.5">
              {line.detected === false && (
                <span className="rounded-md border border-slate-300 bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                  Not clearly detected in photo
                </span>
              )}
              {line.variation_description && (
                <span className="rounded-md border border-violet-200 bg-violet-50 px-2 py-0.5 text-[10px] font-medium text-violet-700">
                  {line.variation_description}
                </span>
              )}
              {typeof line.depth_clarity === "number" && (
                <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-600 shadow-xs">
                  Depth: {Math.round(line.depth_clarity * 100)}%
                </span>
              )}
              {typeof line.length_normalized === "number" && (
                <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-600 shadow-xs">
                  Length: {Math.round(line.length_normalized * 100)}% of palm
                </span>
              )}
              {line.continuity && (
                <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-600 shadow-xs">
                  Continuity: {line.continuity}
                </span>
              )}
              {line.curvature != null && line.curvature !== "" && (
                <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-600 shadow-xs">
                  Curvature: {line.curvature}
                </span>
              )}
              {typeof line.confidence === "number" && (
                <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-600 shadow-xs">
                  Confidence: {Math.round(line.confidence * 100)}%
                </span>
              )}
            </div>

            {line.interpretation && (
              <p className="mt-2.5 text-xs leading-relaxed text-slate-600">{line.interpretation}</p>
            )}

            {line.significance?.length > 0 && (
              <div className="mt-3 border-t border-slate-200/70 pt-2 text-[11px] leading-relaxed text-slate-500">
                <span className="font-semibold text-slate-700">Significance: </span>
                {line.significance.join(" · ")}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Archive composition: finger structure + mount profiles in one titled flow.
export default function PalmAnalysisDetails({ result }) {
  if (!result) return null;
  return (
    <div className="space-y-8">
      {result.finger_structure && (
        <div>
          <h2 className="mb-4 font-display text-xl font-bold text-slate-900">
            Finger Structure &amp; Dexterity Signals
          </h2>
          <PalmFingerStructure fingerStructure={result.finger_structure} />
        </div>
      )}
      {Array.isArray(result.mounts) && result.mounts.length > 0 && (
        <div>
          <h2 className="mb-4 font-display text-xl font-bold text-slate-900">
            Planetary Mount Profiles
          </h2>
          <PalmMountProfiles mounts={result.mounts} />
        </div>
      )}
    </div>
  );
}
