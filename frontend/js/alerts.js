// alerts.js - the anomaly alerts list.
// Data in: ANOMALY_DETECTED events. Action out: clicking an alert calls selectVehicle().
// Rules: newest first, no duplicates, empty state, a maximum number of alerts,
// and a filter bar (All / Speed spike / Sudden stop / Route deviation).

import { CONFIG } from "./config.js";
import { EVENTS, on } from "./eventBus.js";
import { selectVehicle } from "./vehicles.js";
import {
  parseTimestamp,
  formatLocalTime,
  formatAnomalyType,
  formatScore,
  getEventKey
} from "./utils.js";

// Newest first. Each item: { key, time (ms), type, element }
const alerts = [];
// Keys of alerts already shown. Used to ignore duplicates.
const seenKeys = new Set();

const dom = {};
let activeFilter = "all"; // "all" or an anomaly_type such as "sudden_stop"

function requireElement(id) {
  const element = document.getElementById(id);
  if (element === null) {
    throw new Error(`Missing element with id "${id}" in index.html`);
  }
  return element;
}

export function initAlerts() {
  dom.list = requireElement("alerts-list");
  dom.empty = requireElement("alerts-empty");
  dom.filterBar = requireElement("alerts-filter");

  // One listener on the whole bar (event delegation): it finds which button was clicked.
  dom.filterBar.addEventListener("click", (domEvent) => {
    const button = domEvent.target.closest("[data-filter]");
    if (button !== null) {
      setFilter(button.dataset.filter);
    }
  });

  on(EVENTS.ANOMALY_DETECTED, ({ event }) => addAlert(event));
  refreshFilterBar();
  updateEmptyState();
}

// For testing: how many alerts are shown.
export function getAlertCount() {
  return alerts.length;
}

// Adds one alert. Returns false if it was a duplicate or unusable.
function addAlert(event) {
  const key = getEventKey(event);
  if (seenKeys.has(key)) {
    return false; // already shown
  }

  const date = parseTimestamp(event.ts);
  if (date === null) {
    return false;
  }

  seenKeys.add(key);
  const time = date.getTime();
  const element = buildAlertElement(event);
  const alert = { key, time, type: event.anomaly_type ?? null, element };
  element.hidden = !matchesFilter(alert);

  // "Newest first" means newest by EVENT time. Find the first alert that is the same age
  // or older and insert before it. Equal times: the one that arrived later goes on top.
  let index = alerts.findIndex((alert) => alert.time <= time);
  if (index === -1) {
    index = alerts.length; // older than everything: goes to the bottom
  }
  alerts.splice(index, 0, alert);
  dom.list.insertBefore(element, dom.list.children[index] ?? null);

  // Keep the list from growing forever.
  while (alerts.length > CONFIG.MAX_ALERTS) {
    const oldest = alerts.pop();
    oldest.element.remove();
    seenKeys.delete(oldest.key);
  }

  refreshFilterBar();
  updateEmptyState();
  return true;
}

// ---------- Filter bar ----------

function matchesFilter(alert) {
  return activeFilter === "all" || alert.type === activeFilter;
}

function setFilter(filter) {
  activeFilter = filter;
  alerts.forEach((alert) => {
    alert.element.hidden = !matchesFilter(alert);
  });
  refreshFilterBar();
  updateEmptyState();
}

// Updates the highlighted button and the number on every button.
function refreshFilterBar() {
  dom.filterBar.querySelectorAll("[data-filter]").forEach((button) => {
    const filter = button.dataset.filter;
    const isActive = filter === activeFilter;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));

    const count = filter === "all"
      ? alerts.length
      : alerts.filter((alert) => alert.type === filter).length;
    button.querySelector(".filter-count").textContent = count;
  });
}

// <li class="alert-item"><button class="alert-item-button">
//   <span class="alert-item-title">..</span><span class="alert-item-meta">..</span>
// </button></li>
function buildAlertElement(event) {
  const item = document.createElement("li");
  item.className = "alert-item";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "alert-item-button";
  button.title = "Select this vehicle";

  const title = document.createElement("span");
  title.className = "alert-item-title";
  title.textContent = `${event.vehicle_id} · ${formatAnomalyType(event.anomaly_type)}`;

  const meta = document.createElement("span");
  meta.className = "alert-item-meta";
  meta.textContent = `${formatLocalTime(event.ts)} · Score ${formatScore(event.anomaly_score)}`;

  button.append(title, meta);
  button.addEventListener("click", () => selectVehicle(event.vehicle_id));
  item.append(button);
  return item;
}

function updateEmptyState() {
  const visibleCount = alerts.filter(matchesFilter).length;
  dom.empty.hidden = visibleCount > 0;
  dom.empty.textContent = alerts.length === 0 ? "No anomalies detected." : "No alerts of this type.";
}
