import { useId, useState } from "react";

const LINE_CONFIGS = {
  life_line: {
    color: "#10b981",
    label: "Life Line",
    accent: "text-emerald-600 bg-emerald-50 border-emerald-200",
  },
  head_line: {
    color: "#0284c7",
    label: "Head Line",
    accent: "text-sky-600 bg-sky-50 border-sky-200",
  },
  heart_line: {
    color: "#f43f5e",
    label: "Heart Line",
    accent: "text-rose-600 bg-rose-50 border-rose-200",
  },
  fate_line: {
    color: "#8b5cf6",
    label: "Fate Line",
    accent: "text-violet-600 bg-violet-50 border-violet-200",
  },
  sun_line: {
    color: "#f59e0b",
    label: "Sun Line",
    accent: "text-amber-600 bg-amber-50 border-amber-200",
  },
};

const MOUNT_SYMBOLS = {
  mount_of_jupiter: "♃",
  mount_of_saturn: "♄",
  mount_of_apollo: "☉",
  mount_of_mercury: "☿",
  mount_of_venus: "♀",
  mount_of_moon: "☽",
};

// Hand landmark connections by finger.
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [0, 9], [9, 10], [10, 11], [11, 12],
  [0, 13], [13, 14], [14, 15], [15, 16],
  [0, 17], [17, 18], [18, 19], [19, 20],
  [5, 9], [9, 13], [13, 17],
];

export default function PalmVisualizer({
  imageUrl,
  result,
  activeLineId,
  onHoverLine,
}) {
  const filterId = useId();
  const [showLines, setShowLines] = useState(true);
  const [showMounts, setShowMounts] = useState(true);
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [hoveredMount, setHoveredMount] = useState(null);

  if (!result) return null;

  const lines = result.lines || [];
  const mounts = result.mounts || [];
  const landmarks = result.hand?.landmarks || [];

  // Build SVG path from coordinates.
  function buildSvgPath(coords) {
    if (!coords || coords.length < 2) return "";
    const pts = coords.map((c) => ({ x: c.x * 1000, y: c.y * 1000 }));
    let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;

    for (let i = 1; i < pts.length; i++) {
      const prev = pts[i - 1];
      const curr = pts[i];
      const midX = (prev.x + curr.x) / 2;
      const midY = (prev.y + curr.y) / 2;
      d += ` Q ${prev.x.toFixed(1)} ${prev.y.toFixed(1)}, ${midX.toFixed(1)} ${midY.toFixed(1)}`;
    }
    const last = pts[pts.length - 1];
    d += ` T ${last.x.toFixed(1)} ${last.y.toFixed(1)}`;
    return d;
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Visualizer Frame */}
      <div className="relative w-full overflow-hidden rounded-3xl border border-slate-200 bg-slate-900 shadow-lg">
        {/* Underlay Image */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt="Analyzed Palm"
          className="block w-full h-auto select-none opacity-95 transition-opacity"
        />

        {/* Ambient Dark Gradient Edge */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-slate-950/40 via-transparent to-slate-950/20" />

        {/* Scaled SVG Biometric Overlay */}
        <svg
          viewBox="0 0 1000 1000"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
        >
          <defs>
            <filter id={`glow-${filterId}`} x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id={`bright-glow-${filterId}`} x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="12" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Landmark connections layer */}
          {showLandmarks && landmarks.length >= 21 && (
            <g opacity="0.65" className="transition-opacity duration-300">
              {HAND_CONNECTIONS.map(([i1, i2], idx) => {
                const p1 = landmarks[i1];
                const p2 = landmarks[i2];
                if (!p1 || !p2) return null;
                return (
                  <line
                    key={idx}
                    x1={p1.x * 1000}
                    y1={p1.y * 1000}
                    x2={p2.x * 1000}
                    y2={p2.y * 1000}
                    stroke="#a5b4fc"
                    strokeWidth="2.5"
                    strokeDasharray="4 4"
                  />
                );
              })}
              {landmarks.map((lm) => (
                <circle
                  key={lm.index}
                  cx={lm.x * 1000}
                  cy={lm.y * 1000}
                  r="5"
                  fill="#6366f1"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              ))}
            </g>
          )}

          {/* Palm crease lines layer */}
          {showLines && (
            <g className="transition-opacity duration-300">
              {lines.map((line) => {
                if (!line.detected || !line.coordinates?.length) return null;
                const cfg = LINE_CONFIGS[line.line_id] || { color: "#ffffff" };
                const isSelected = activeLineId === line.line_id;
                const pathData = buildSvgPath(line.coordinates);

                return (
                  <g
                    key={line.line_id}
                    className="cursor-pointer transition"
                    onMouseEnter={() => onHoverLine?.(line.line_id)}
                    onMouseLeave={() => onHoverLine?.(null)}
                  >
                    {/* Hover hit zone */}
                    <path
                      d={pathData}
                      fill="none"
                      stroke="transparent"
                      strokeWidth="28"
                      strokeLinecap="round"
                    />

                    {/* Glow halo */}
                    <path
                      d={pathData}
                      fill="none"
                      stroke={cfg.color}
                      strokeWidth={isSelected ? "14" : "9"}
                      strokeOpacity={isSelected ? "0.9" : "0.45"}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      filter={`url(#${isSelected ? `bright-glow-${filterId}` : `glow-${filterId}`})`}
                    />

                    {/* Core line */}
                    <path
                      d={pathData}
                      fill="none"
                      stroke={isSelected ? "#ffffff" : cfg.color}
                      strokeWidth={isSelected ? "5" : "3.5"}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </g>
                );
              })}
            </g>
          )}

          {/* Planetary mounts layer */}
          {showMounts && (
            <g className="transition-opacity duration-300">
              {mounts.map((mount) => {
                if (!mount.center) return null;
                const cx = mount.center.x * 1000;
                const cy = mount.center.y * 1000;
                const sym = MOUNT_SYMBOLS[mount.mount_id] || "✦";
                const isProminent = mount.prominence === "prominent";

                return (
                  <g
                    key={mount.mount_id}
                    className="cursor-pointer"
                    onMouseEnter={() => setHoveredMount(mount)}
                    onMouseLeave={() => setHoveredMount(null)}
                  >
                    {/* Pulsing ring */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isProminent ? "24" : "18"}
                      fill="rgba(255, 255, 255, 0.15)"
                      stroke={isProminent ? "#fbbf24" : "rgba(255, 255, 255, 0.7)"}
                      strokeWidth="1.5"
                      strokeDasharray={isProminent ? "none" : "3 3"}
                    />
                    {/* Glyph dot */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r="12"
                      fill={isProminent ? "#f59e0b" : "rgba(15, 23, 42, 0.85)"}
                      stroke="#ffffff"
                      strokeWidth="1.5"
                    />
                    <text
                      x={cx}
                      y={cy + 4.5}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize="11"
                      fontWeight="bold"
                      className="select-none pointer-events-none"
                    >
                      {sym}
                    </text>
                  </g>
                );
              })}
            </g>
          )}
        </svg>

        {/* Floating Tooltip for Hovered Mount */}
        {hoveredMount && hoveredMount.center && (
          <div
            className="pointer-events-none absolute z-20 -translate-x-1/2 -translate-y-full rounded-xl border border-white/20 bg-slate-900/90 px-3 py-1.5 text-xs text-white shadow-xl backdrop-blur-md"
            style={{
              left: `${hoveredMount.center.x * 100}%`,
              top: `calc(${hoveredMount.center.y * 100}% - 14px)`,
            }}
          >
            <div className="flex items-center gap-1.5 font-semibold text-amber-300">
              <span>{MOUNT_SYMBOLS[hoveredMount.mount_id]}</span>
              <span>{hoveredMount.name}</span>
            </div>
            <div className="text-[10px] text-slate-300">
              Prominence: <span className="capitalize font-medium text-white">{hoveredMount.prominence}</span>
            </div>
          </div>
        )}

        {/* Top Control HUD */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full border border-white/20 bg-slate-900/80 px-3 py-1 text-xs text-white shadow-md backdrop-blur-md">
          <label className="flex items-center gap-1 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showLines}
              onChange={(e) => setShowLines(e.target.checked)}
              className="rounded accent-violet-500"
            />
            <span className="text-[11px] font-medium">Lines</span>
          </label>
          <span className="text-white/30">|</span>
          <label className="flex items-center gap-1 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showMounts}
              onChange={(e) => setShowMounts(e.target.checked)}
              className="rounded accent-violet-500"
            />
            <span className="text-[11px] font-medium">Mounts</span>
          </label>
          <span className="text-white/30">|</span>
          <label className="flex items-center gap-1 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showLandmarks}
              onChange={(e) => setShowLandmarks(e.target.checked)}
              className="rounded accent-violet-500"
            />
            <span className="text-[11px] font-medium">Mesh</span>
          </label>
        </div>

        {/* Bottom Overlay Hint */}
        <div className="pointer-events-none absolute bottom-3 left-3 right-3 flex items-center justify-between text-[11px] text-white/80">
          <span className="rounded-full bg-slate-900/60 px-2.5 py-0.5 backdrop-blur-sm">
            Biometric Crease Overlay
          </span>
          <span className="rounded-full bg-slate-900/60 px-2.5 py-0.5 backdrop-blur-sm">
            {result.hand?.detected_handedness} Hand Identified
          </span>
        </div>
      </div>

      {/* Color Legend for Palm Lines */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        {lines.map((l) => {
          const cfg = LINE_CONFIGS[l.line_id];
          if (!cfg || !l.detected) return null;
          const isSelected = activeLineId === l.line_id;

          return (
            <button
              type="button"
              key={l.line_id}
              onClick={() => onHoverLine?.(isSelected ? null : l.line_id)}
              onMouseEnter={() => onHoverLine?.(l.line_id)}
              onMouseLeave={() => onHoverLine?.(null)}
              className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition border ${
                isSelected
                  ? "bg-slate-900 text-white border-slate-900 shadow-sm scale-105"
                  : "bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: cfg.color }}
              />
              <span>{cfg.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
