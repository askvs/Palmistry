// ChartToggle – A styled toggle button to show/hide the insight chart.
export default function ChartToggle({ enabled, onToggle, label = "Show Chart" }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`group inline-flex items-center gap-2.5 rounded-full border px-4 py-2 text-xs font-semibold shadow-xs transition-all duration-200 ${
        enabled
          ? "border-primary-400 bg-primary-100 text-primary-800 hover:bg-primary-200"
          : "border-slate-200 bg-white text-slate-600 hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700"
      }`}
    >
      <span
        className={`inline-block h-3.5 w-7 rounded-full relative transition-colors duration-200 ${
          enabled ? "bg-primary-500" : "bg-slate-300"
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
