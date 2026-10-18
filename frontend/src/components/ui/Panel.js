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
      className={`surface-panel ${className}`}
    >
      {(title || action) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 pb-4 pt-4.5 sm:px-6 sm:pt-5">
          <div>
            <h2 className="text-[15px] font-semibold tracking-tight text-slate-900">{title}</h2>
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={padded ? "p-5 sm:p-6" : bodyClassName}>{children}</div>
    </section>
  );
}
