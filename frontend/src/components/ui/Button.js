// Canonical button for the whole app.
import Link from "next/link";

const VARIANTS = {
  primary:
    "bg-primary-600 text-white shadow-sm shadow-primary-600/25 hover:bg-primary-700 active:bg-primary-800",
  secondary:
    "border border-slate-200 bg-white text-slate-700 shadow-xs hover:border-slate-300 hover:bg-slate-50 active:bg-slate-100",
  ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900 active:bg-slate-200/70",
  danger:
    "bg-rose-600 text-white shadow-sm shadow-rose-600/25 hover:bg-rose-700 active:bg-rose-800",
  dangerGhost:
    "border border-rose-200 bg-white text-rose-600 hover:border-rose-300 hover:bg-rose-50 active:bg-rose-100",
  accent:
    "bg-gradient-to-r from-accent-500 to-accent-600 text-white shadow-sm shadow-accent-600/25 hover:from-accent-600 hover:to-accent-700",
};

const SIZES = {
  sm: "h-9 px-3.5 text-xs gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-11 px-6 text-sm gap-2",
};

const Spinner = ({ className = "h-4 w-4" }) => (
  <span
    className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${className}`}
    aria-hidden="true"
  />
);

export default function Button({
  href,
  variant = "primary",
  size = "md",
  type = "button",
  loading = false,
  disabled = false,
  fullWidth = false,
  icon: Icon,
  iconRight: IconRight,
  className = "",
  children,
  onClick,
  ...rest
}) {
  const classes = [
    "inline-flex cursor-pointer items-center justify-center rounded-full font-medium transition-colors duration-150 select-none",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600",
    "disabled:pointer-events-none disabled:opacity-50",
    SIZES[size] || SIZES.md,
    VARIANTS[variant] || VARIANTS.primary,
    fullWidth ? "w-full" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const content = (
    <>
      {loading && <Spinner />}
      {!loading && Icon && <Icon className="h-4 w-4 shrink-0" />}
      {children}
      {!loading && IconRight && <IconRight className="h-4 w-4 shrink-0" />}
    </>
  );

  const isDisabled = disabled || loading;

  if (href && !isDisabled) {
    return (
      <Link href={href} className={classes} onClick={onClick} {...rest}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type={type}
      className={classes}
      disabled={isDisabled}
      onClick={onClick}
      aria-busy={loading || undefined}
      {...rest}
    >
      {content}
    </button>
  );
}
