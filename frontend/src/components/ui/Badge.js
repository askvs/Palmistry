// Semantic status/label pill.

const TONES = {
  slate: "border-slate-200 bg-slate-100 text-slate-700",
  primary: "border-primary-200 bg-primary-50 text-primary-700",
  accent: "border-accent-200 bg-accent-50 text-accent-800",
  emerald: "border-emerald-200 bg-emerald-50 text-emerald-700",
  rose: "border-rose-200 bg-rose-50 text-rose-700",
  indigo: "border-indigo-200 bg-indigo-50 text-indigo-700",
  blue: "border-blue-200 bg-blue-50 text-blue-700",
  amber: "border-amber-200 bg-amber-50 text-amber-800",
};

export default function Badge({ tone = "slate", className = "", children }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
        TONES[tone] || TONES.slate
      } ${className}`}
    >
      {children}
    </span>
  );
}
