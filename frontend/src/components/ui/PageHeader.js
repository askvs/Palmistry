// Canonical page header with optional actions.

const TILE_TONES = {
  primary: "bg-primary-50 text-primary-600 ring-1 ring-primary-100",
  accent: "bg-accent-50 text-accent-600 ring-1 ring-accent-100",
  emerald: "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100",
  slate: "bg-slate-100 text-slate-600 ring-1 ring-slate-200",
};

const GRADIENTS = {
  violet: "bg-gradient-to-br from-primary-600 to-fuchsia-500 shadow-primary-500/30",
  gold: "bg-gradient-to-br from-accent-400 to-accent-600 shadow-accent-500/30",
};

export default function PageHeader({
  icon: Icon,
  avatarUrl,
  avatarAlt = "",
  tileTone = "primary",
  gradient = false,
  eyebrow,
  title,
  description,
  actions,
  className = "",
}) {
  const tileClass = gradient
    ? `flex h-14 w-14 shrink-0 items-center justify-center rounded-[14px] text-white shadow-lg ${GRADIENTS[GRADIENTS[gradient] ? gradient : "violet"]}`
    : `flex h-14 w-14 shrink-0 items-center justify-center rounded-[14px] ${TILE_TONES[tileTone] || TILE_TONES.primary}`;

  return (
    <header
      className={`flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between ${className}`}
    >
      <div className="flex items-start gap-4">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={avatarAlt}
            className="h-14 w-14 shrink-0 rounded-full object-cover ring-1 ring-slate-200"
          />
        ) : (
          Icon && (
            <span className={tileClass}>
              <Icon className="h-6 w-6" />
            </span>
          )
        )}
        <div>
          {eyebrow && (
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-primary-700">
              {eyebrow}
            </p>
          )}
          <h1 className="font-display text-3xl font-semibold tracking-[-0.02em] text-slate-900 sm:text-4xl">
            {title}
          </h1>
          {description && (
            <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-slate-600 sm:text-base">
              {description}
            </p>
          )}
        </div>
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
