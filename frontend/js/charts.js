// charts.js - the speed chart (Chart.js) for the selected vehicle.
// The chart object is created ONCE and then updated in place.
// Data in: VEHICLE_SELECTED and VEHICLE_UPDATED events, plus the stored speed history.
 
import { CONFIG } from "./config.js";
import { EVENTS, on } from "./eventBus.js";
import { getSelectedVehicleId, getSpeedHistory } from "./vehicles.js";
import { formatClock, formatSpeed } from "./utils.js";
 
const dom = {};         // page elements, filled in initChart()
let chart = null;       // the Chart.js object. null until the first vehicle is selected.
let shownHistory = [];  // the points currently drawn (the tooltip reads this)
 
function requireElement(id) {
  const element = document.getElementById(id);
  if (element === null) {
    throw new Error(`Missing element with id "${id}" in index.html`);
  }
  return element;
}
 
export function initChart() {
  if (typeof Chart === "undefined") {
    throw new Error("the Chart.js library did not load");
  }
 
  dom.canvas = requireElement("speed-chart");
  dom.wrap = requireElement("chart-wrap");
  dom.empty = requireElement("chart-empty");
  dom.caption = requireElement("chart-caption");
  dom.caption.textContent = buildCaption();
 
  on(EVENTS.VEHICLE_SELECTED, renderSelectedVehicle);
  on(EVENTS.VEHICLE_UPDATED, ({ vehicleId }) => {
    if (vehicleId === getSelectedVehicleId()) {
      renderSelectedVehicle();
    }
  });
 
  renderSelectedVehicle(); // shows the empty state at start
}
 
// Honest note about where the numbers come from.
function buildCaption() {
  let text = `Last ${CONFIG.HISTORY_LENGTH} readings received since this page opened.`;
  if (!CONFIG.SPEED_UNIT_CONFIRMED) {
    text += ` The speed unit (${CONFIG.SPEED_UNIT}) is assumed, not yet confirmed.`;
  }
  return text;
}
 
// Decides between "empty state" and "chart", then updates the chart.
function renderSelectedVehicle() {
  const vehicleId = getSelectedVehicleId();
  const history = vehicleId === null ? [] : getSpeedHistory(vehicleId);
  const hasData = history.length > 0;
 
  dom.empty.hidden = hasData;
  dom.wrap.hidden = !hasData;
  dom.caption.hidden = !hasData;
  if (!hasData) {
    return;
  }
 
  // The chart is created only now, after the wrapper is visible, so it can measure its size.
  if (chart === null) {
    chart = createChart();
  }
  updateChart(vehicleId, history);
}
 
// Reads a color from the CSS variables, so the chart matches the rest of the page.
function getCssColor(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}
 
function createChart() {
  const lineColor = getCssColor("--color-selected", "#1d5fd1");
  const gridColor = getCssColor("--color-border", "#d9e0e6");
  const textColor = getCssColor("--color-muted", "#52606d");
 
  return new Chart(dom.canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: `Speed (${CONFIG.SPEED_UNIT})`,
        data: [],
        borderColor: lineColor,
        borderWidth: 2,
        tension: 0.25,
        pointBackgroundColor: [],
        pointRadius: []
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false, // fill the wrapper's fixed height (see .chart-wrap in style.css)
      animation: false,           // no animation: updates arrive every second or two
      scales: {
        x: {
          title: { display: true, text: "Time (your local time)", color: textColor },
          ticks: { maxTicksLimit: 6, color: textColor },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: `Speed (${CONFIG.SPEED_UNIT})`, color: textColor },
          ticks: { color: textColor },
          grid: { color: gridColor }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => formatSpeed(item.parsed.y),
            afterLabel: (item) => (shownHistory[item.dataIndex]?.isAnomalous ? "Anomaly flagged" : "")
          }
        }
      }
    }
  });
}
 
// Replaces the chart's data in place and redraws. No new chart is created.
function updateChart(vehicleId, history) {
  const lineColor = getCssColor("--color-selected", "#1d5fd1");
  const anomalyColor = getCssColor("--color-anomaly", "#b42318");
  const dataset = chart.data.datasets[0];
 
  shownHistory = history;
  chart.data.labels = history.map((point) => formatClock(point.ts));
  dataset.data = history.map((point) => point.speed);
  // Flagged readings are drawn as larger red dots.
  dataset.pointBackgroundColor = history.map((point) => (point.isAnomalous ? anomalyColor : lineColor));
  dataset.pointRadius = history.map((point) => (point.isAnomalous ? 6 : 3));
 
  dom.canvas.setAttribute("aria-label", `Line chart of speed over time for vehicle ${vehicleId}`);
  chart.update("none");
}
 