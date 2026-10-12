// ChartToggle – A styled toggle button to show/hide the insight chart.
export default function ChartToggle({ enabled, onToggle, label = "Show Chart" }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`group inline-flex items-center gap-2.5 rounded-full border px-4 py-2 text-xs font-semibold shadow-xs transition-all duration-200 ${
        enabled
          ? "border-violet-400 bg-violet-100 text-violet-800 hover:bg-violet-200"
          : "border-slate-200 bg-white text-slate-600 hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700"
      }`}
    >
      <span
        className={`inline-block h-3.5 w-7 rounded-full relative transition-colors duration-200 ${
          enabled ? "bg-violet-500" : "bg-slate-300"
        }`}
      >
        <span
          className={`absolute top-0.5 h-2.5 w-2.5 rounded-full bg-white shadow-sm transition-transform duration-200 ${
            enabled ? "translate-x-3.5" : "translate-x-0.5"
          }`}
        />
      </span>
      {label}
    </button>
  );
}
