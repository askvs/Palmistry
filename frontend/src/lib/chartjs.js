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

// Brand chart colors.
export const CHART_COLORS = ["#6366f1", "#7c3aed", "#f59e0b", "#10b981", "#f43f5e"];

const AXIS_TICK = { color: "#64748b", font: { size: 11 } };

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
        grid: { color: "rgba(148, 163, 184, 0.2)" },
      },
      x: { ticks: AXIS_TICK, grid: { display: false } },
    },
    plugins: {
      legend: {
        display: legend,
        position: "bottom",
        labels: { color: "#475569", usePointStyle: true, boxWidth: 8, boxHeight: 8 },
      },
      tooltip: {
        enabled: true,
        backgroundColor: "#0f172a",
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
        grid: { color: "rgba(148, 163, 184, 0.2)" },
      },
      x: { ticks: AXIS_TICK, grid: { display: false } },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        backgroundColor: "#0f172a",
        padding: 10,
        cornerRadius: 10,
        callbacks: {
          label: (context) => ` ${context.label}: ${Math.round(context.parsed.y * 100)}${unit}`,
        },
      },
    },
  };
}
