// app.js - entry point. Starts the app and connects the bus to the page.
// Phase 7 version: everything from Phase 6, plus the data source.
// USE_MOCK_DATA true  -> the frontend-only mock simulator is loaded and started.
// USE_MOCK_DATA false -> the real backend (api.js) will be started in Phase 8.

import { CONFIG } from "./config.js";
import { EVENTS, on } from "./eventBus.js";
import { getVehicle, getSelectedVehicleId, publishCounts } from "./vehicles.js";
import { initMap } from "./map.js";
import { initChart } from "./charts.js";
import { initAlerts } from "./alerts.js";
import {
  formatLocalTime,
  formatSpeed,
  formatCoordinate,
  formatStatus
} from "./utils.js";

// Finds an element by id. Fails loudly if index.html and this file disagree.
function getElement(id) {
  const element = document.getElementById(id);
  if (element === null) {
    throw new Error(`Missing element with id "${id}" in index.html`);
  }
  return element;
}

// Look up every element once, then reuse the references.
const dom = {
  countTotal: getElement("count-total"),
  countActive: getElement("count-active"),
  countNormal: getElement("count-normal"),
  countAnomalous: getElement("count-anomalous"),
  detailsEmpty: getElement("details-empty"),
  detailsList: getElement("vehicle-details"),
  detailId: getElement("detail-id"),
  detailRoute: getElement("detail-route"),
  detailSpeed: getElement("detail-speed"),
  detailLat: getElement("detail-lat"),
  detailLon: getElement("detail-lon"),
  detailTime: getElement("detail-time"),
  detailStatus: getElement("detail-status"),
  connection: getElement("connection-status"),
  errorBanner: getElement("error-banner"),
  errorMessage: getElement("error-message")
};

const CONNECTION_LABELS = {
  connecting: "Connecting",
  connected: "Connected",
  disconnected: "Disconnected"
};

// ---------- Rendering: each function updates one part of the page ----------

function renderOverview(counts) {
  dom.countTotal.textContent = counts.total;
  dom.countActive.textContent = counts.active;
  dom.countNormal.textContent = counts.normal;
  dom.countAnomalous.textContent = counts.anomalous;
}

function renderDetails() {
  const vehicleId = getSelectedVehicleId();
  const record = vehicleId === null ? undefined : getVehicle(vehicleId);

  // No selection: show the empty message and hide the list.
  dom.detailsEmpty.hidden = record !== undefined;
  dom.detailsList.hidden = record === undefined;
  if (record === undefined) {
    return;
  }

  const { event } = record;
  dom.detailId.textContent = event.vehicle_id;
  dom.detailRoute.textContent = event.route_id != null ? String(event.route_id) : "--";
  dom.detailSpeed.textContent = formatSpeed(event.speed);
  dom.detailLat.textContent = formatCoordinate(event.lat);
  dom.detailLon.textContent = formatCoordinate(event.lon);
  dom.detailTime.textContent = formatLocalTime(event.ts);

  // textContent (not innerHTML): data from outside is shown as plain text, never run as HTML.
  const pill = document.createElement("span");
  pill.className = event.anomaly_flag ? "status-pill is-anomalous" : "status-pill is-normal";
  pill.textContent = formatStatus(event);
  dom.detailStatus.replaceChildren(pill);
}

// state picks the color; the optional label replaces the default text
// (for example "Connected (simulated)").
function renderConnection(state, label) {
  if (!(state in CONNECTION_LABELS)) {
    console.warn(`Unknown connection state "${state}"`);
    return;
  }
  dom.connection.dataset.state = state; // CSS colors the badge from this attribute
  dom.connection.textContent = label ?? CONNECTION_LABELS[state];
}

// An empty or missing message hides the banner.
function renderError(message) {
  const hasMessage = typeof message === "string" && message !== "";
  dom.errorBanner.hidden = !hasMessage;
  dom.errorMessage.textContent = hasMessage ? message : "";
}

// Every element marked data-mock-only is shown only while mock mode is on.
function updateMockLabels() {
  document.querySelectorAll("[data-mock-only]").forEach((element) => {
    element.hidden = !CONFIG.USE_MOCK_DATA;
  });
}

function checkLibraries() {
  if (typeof L === "undefined") {
    console.error("Leaflet did not load. Check the Network tab.");
  }
  if (typeof Chart === "undefined") {
    console.error("Chart.js did not load. Check the Network tab.");
  }
}

// Runs one module's init function; a failure is reported but does not stop the others.
function startModule(name, init) {
  try {
    init();
  } catch (error) {
    console.error(`The ${name} could not start:`, error);
    renderError(`The ${name} could not start: ${error.message}`);
  }
}

// Chooses the data source. Both sources feed the same ingest() function in vehicles.js.
async function startDataSource() {
  if (CONFIG.USE_MOCK_DATA) {
    try {
      // Dynamic import: the mock files are loaded only when mock mode is on,
      // so with USE_MOCK_DATA false the project also works if they are deleted.
      const { startMockSimulator } = await import("./mockSimulator.js");
      startMockSimulator();
    } catch (error) {
      console.error("The mock simulator could not start:", error);
      renderError(`The mock simulator could not start: ${error.message}`);
    }
    return;
  }

  // Phase 8 will start api.js here.
  renderConnection("disconnected", "Not connected");
  renderError(
    "Mock mode is off, but the real backend connection (api.js) is not built yet. " +
    "Set USE_MOCK_DATA to true in config.js to see simulated data."
  );
}

// ---------- Start ----------

function start() {
  // Connect bus events to the page.
  on(EVENTS.COUNTS_CHANGED, renderOverview);
  on(EVENTS.VEHICLE_SELECTED, renderDetails);
  on(EVENTS.VEHICLE_UPDATED, ({ vehicleId }) => {
    if (vehicleId === getSelectedVehicleId()) {
      renderDetails();
    }
  });
  on(EVENTS.CONNECTION_CHANGED, ({ state, label }) => renderConnection(state, label));
  on(EVENTS.DATA_ERROR, ({ message }) => renderError(message));

  // Start the three UI modules. If one fails (for example its library did not load),
  // show the problem and keep the rest of the dashboard working.
  startModule("map", initMap);
  startModule("speed chart", initChart);
  startModule("alerts list", initAlerts);

  // Re-check the counts regularly: a vehicle can stop being "active" without any new event.
  setInterval(publishCounts, CONFIG.COUNTS_REFRESH_MS);

  startDataSource();
  updateMockLabels();
  checkLibraries();
  console.log("Dashboard started. Mock mode:", CONFIG.USE_MOCK_DATA);
}

start();
