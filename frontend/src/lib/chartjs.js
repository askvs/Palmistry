// Chart.js setup with shared presets.
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  BarController,
  BarElement,
  Tooltip,
  Filler,
  Legend
);

// Brand chart colors (porcelain palette, spec §5.13).
export const CHART_COLORS = ["#7c3aed", "#f59e0b", "#c4b5fd", "#059669", "#e11d48"];

const AXIS_TICK = { color: "#5b5675", font: { size: 11 } };

// Dataset-level defaults (tension .35, borderWidth 2, pointRadius 0,
// pointHoverRadius 4) belong to the consuming dataset configs (W2.5/W4).

// Shared line chart options.
export function lineChartOptions({ max = 1, unit = "%", legend = true } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    scales: {
      y: {
        min: 0,
        max,
        ticks: {
          ...AXIS_TICK,
          callback: (value) => `${Math.round(value * 100)}${unit}`,
        },
        grid: { color: "#f1eff9" },
      },
      x: { ticks: AXIS_TICK, grid: { display: false } },
    },
    plugins: {
      legend: {
        display: legend,
        position: "bottom",
        labels: { color: "#46415f", usePointStyle: true, boxWidth: 8, boxHeight: 8 },
      },
      tooltip: {
        enabled: true,
        backgroundColor: "#ffffff",
        titleColor: "#1e1836",
        bodyColor: "#46415f",
        borderColor: "#eae6f5",
        borderWidth: 1,
        padding: 10,
        cornerRadius: 10,
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${Math.round(context.parsed.y * 100)}${unit}`,
        },
      },
    },
  };
}

// Shared bar chart options.
export function barChartOptions({ unit = "%" } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        min: 0,
        max: 1,
        ticks: {
          ...AXIS_TICK,
          callback: (value) => `${Math.round(value * 100)}${unit}`,
        },
        grid: { color: "#f1eff9" },
      },
      x: { ticks: AXIS_TICK, grid: { display: false } },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        backgroundColor: "#ffffff",
        titleColor: "#1e1836",
        bodyColor: "#46415f",
        borderColor: "#eae6f5",
        borderWidth: 1,
        padding: 10,
        cornerRadius: 10,
        callbacks: {
          label: (context) => ` ${context.label}: ${Math.round(context.parsed.y * 100)}${unit}`,
        },
      },
    },
  };
}
