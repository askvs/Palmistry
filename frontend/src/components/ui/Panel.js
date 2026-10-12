// Canonical card/surface.
export default function Panel({
  title,
  subtitle,
  action,
  padded = true,
  className = "",
  bodyClassName = "",
  children,
}) {
  return (
    <section
      className={`rounded-3xl border border-slate-200/90 bg-white shadow-xs ${className}`}
    >
      {(title || action) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 pb-4 pt-5 sm:px-7">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-slate-900">{title}</h2>
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={padded ? "p-6 sm:p-7" : bodyClassName}>{children}</div>
    </section>
  );
}
