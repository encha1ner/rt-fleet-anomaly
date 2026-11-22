// map.js - the Leaflet map and the vehicle markers.
// It listens to the event bus; it never talks to the backend or the mock simulator.
// Data in:  VEHICLE_UPDATED, VEHICLE_SELECTED events.
// Action out: when a marker is clicked it calls selectVehicle(id) in vehicles.js.
 
import { CONFIG } from "./config.js";
import { EVENTS, on, emit } from "./eventBus.js";
import { selectVehicle, getSelectedVehicleId, getAllVehicles } from "./vehicles.js";
import { formatSpeed, formatStatus } from "./utils.js";
 
const TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
// OpenStreetMap requires this credit to be visible on the map.
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
 
const MARKER_SIZE = 22; // pixels; must match .vehicle-marker in style.css
const AUTO_FIT_DELAY_MS = 300;
// Markers on top of each other: anomalous above normal, selected above everything.
const Z_OFFSET = { normal: 0, anomalous: 1000, selected: 2000 };
 
let map = null; // the Leaflet map object, created in initMap()
 
// THE MARKER REGISTRY: vehicle_id -> { marker, isAnomalous }
// One entry per vehicle. This is how we find the existing marker and move it
// instead of creating a duplicate.
const markers = new Map();
 
let highlightedVehicleId = null; // the selected vehicle (gets a blue ring)
let userHasMovedMap = false;     // once true, we stop auto-fitting the view
let autoFitTimer = null;
let tileErrorShown = false;
 
// ---------- Setup ----------
 
export function initMap() {
  if (map !== null) {
    return; // already started
  }
 
  map = L.map("map", { center: CONFIG.MAP_CENTER, zoom: CONFIG.MAP_ZOOM });
 
  const tiles = L.tileLayer(TILE_URL, { maxZoom: 19, attribution: TILE_ATTRIBUTION }).addTo(map);
  tiles.on("tileerror", handleTileError);
  tiles.on("tileload", handleTileLoad);
 
  addFitControl();
  watchUserInteraction();
 
  highlightedVehicleId = getSelectedVehicleId();
  // If vehicles arrived before the map was ready, draw them now.
  getAllVehicles().forEach(upsertMarker);
 
  on(EVENTS.VEHICLE_UPDATED, ({ event }) => upsertMarker(event));
  on(EVENTS.VEHICLE_SELECTED, ({ vehicleId }) => highlightVehicle(vehicleId));
}
 
// For testing: how many markers exist. Should always equal the number of vehicles.
export function getMarkerCount() {
  return markers.size;
}
 
// ---------- Markers ----------
 
// Create the marker for a new vehicle, or move and update the existing one.
function upsertMarker(event) {
  const vehicleId = event.vehicle_id;
  const position = [event.lat, event.lon];
  const isAnomalous = event.anomaly_flag;
  const entry = markers.get(vehicleId);
 
  if (entry === undefined) {
    const icon = L.divIcon({
      className: "vehicle-marker",
      html: "",
      iconSize: [MARKER_SIZE, MARKER_SIZE],
      iconAnchor: [MARKER_SIZE / 2, MARKER_SIZE / 2],
      popupAnchor: [0, -MARKER_SIZE / 2]
    });
    const marker = L.marker(position, {
      icon,
      title: vehicleId, // shown on hover and read by screen readers
      alt: `Vehicle ${vehicleId}`
    }).addTo(map);
 
    marker.bindPopup(buildPopupContent(event));
    marker.on("click", () => selectVehicle(vehicleId));
 
    markers.set(vehicleId, { marker, isAnomalous });
    applyMarkerState(vehicleId);
    scheduleAutoFit();
    return;
  }
 
  // Existing vehicle: move the same marker and refresh the popup.
  entry.marker.setLatLng(position);
  entry.marker.setPopupContent(buildPopupContent(event));
 
  if (entry.isAnomalous !== isAnomalous) {
    entry.isAnomalous = isAnomalous;
    applyMarkerState(vehicleId);
  }
}
 
// Sets the look of one marker (normal / anomalous / selected) by switching CSS classes.
// We change classes on the existing element instead of building a new icon: it is faster
// and does not disturb an open popup.
function applyMarkerState(vehicleId) {
  const entry = markers.get(vehicleId);
  if (entry === undefined) {
    return;
  }
  const element = entry.marker.getElement();
  if (!element) {
    return;
  }
 
  const isSelected = vehicleId === highlightedVehicleId;
  element.classList.toggle("is-anomalous", entry.isAnomalous);
  element.classList.toggle("is-normal", !entry.isAnomalous);
  element.classList.toggle("is-selected", isSelected);
  // "!" so anomalies are not shown by color alone
  element.textContent = entry.isAnomalous ? "!" : "";
 
  let offset = Z_OFFSET.normal;
  if (entry.isAnomalous) {
    offset = Z_OFFSET.anomalous;
  }
  if (isSelected) {
    offset = Z_OFFSET.selected;
  }
  entry.marker.setZIndexOffset(offset);
}
 
function highlightVehicle(vehicleId) {
  const previousId = highlightedVehicleId;
  highlightedVehicleId = vehicleId;
  if (previousId !== null) {
    applyMarkerState(previousId); // remove the ring from the old one
  }
  if (vehicleId !== null) {
    applyMarkerState(vehicleId);  // add the ring to the new one
    revealMarker(vehicleId, vehicleId !== previousId);
  }
}
 
// Make sure the selected vehicle can be seen. Useful when the selection came from
// somewhere other than the map, for example a click in the alerts list.
function revealMarker(vehicleId, shouldOpenPopup) {
  const entry = markers.get(vehicleId);
  if (entry === undefined) {
    return;
  }
  const position = entry.marker.getLatLng();
  if (!map.getBounds().contains(position)) {
    map.panTo(position);
  }
  // Open the popup only when the selection CHANGED. Clicking the same marker again
  // must still be able to close its popup (Leaflet toggles it).
  if (shouldOpenPopup) {
    entry.marker.openPopup();
  }
}
 
// Popup content is built from DOM elements with textContent, never from an HTML string,
// so text from outside can never be run as HTML.
function buildPopupContent(event) {
  const box = document.createElement("div");
  box.className = "popup-content";
 
  const title = document.createElement("strong");
  title.textContent = event.vehicle_id;
 
  const speed = document.createElement("div");
  speed.textContent = `Speed: ${formatSpeed(event.speed)}`;
 
  const status = document.createElement("div");
  status.textContent = `Status: ${formatStatus(event)}`;
 
  box.append(title, speed, status);
  return box;
}
 
// ---------- View control ----------
 
// Zoom and pan so every marker is visible.
function fitToMarkers() {
  if (markers.size === 0) {
    return;
  }
  const points = Array.from(markers.values(), (entry) => entry.marker.getLatLng());
  // maxZoom stops a single vehicle from zooming in absurdly far.
  map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 15 });
}
 
// Wait a moment so a burst of new vehicles causes one fit, not ten.
function scheduleAutoFit() {
  if (userHasMovedMap) {
    return;
  }
  clearTimeout(autoFitTimer);
  autoFitTimer = setTimeout(fitToMarkers, AUTO_FIT_DELAY_MS);
}
 
// As soon as the person touches the map, stop moving the view for them.
function watchUserInteraction() {
  const container = map.getContainer();
  ["pointerdown", "wheel", "keydown"].forEach((type) => {
    container.addEventListener(type, () => { userHasMovedMap = true; }, { passive: true });
  });
}
 
// A small "Fit all" button on the map, so the person can re-fit manually.
function addFitControl() {
  const FitControl = L.Control.extend({
    options: { position: "topleft" },
    onAdd() {
      const button = L.DomUtil.create("button", "map-fit-button");
      button.type = "button";
      button.textContent = "Fit all";
      button.title = "Zoom the map to show all vehicles";
      L.DomEvent.disableClickPropagation(button);
      button.addEventListener("click", fitToMarkers);
      return button;
    }
  });
  new FitControl().addTo(map);
}
 
// ---------- Tile loading problems (usually no internet) ----------
 
function handleTileError() {
  if (tileErrorShown) {
    return; // many tiles fail at once; report only the first
  }
  tileErrorShown = true;
  console.warn("Map tiles failed to load.");
  emit(EVENTS.DATA_ERROR, { message: "Map tiles could not be loaded. Check your internet connection." });
}
 
function handleTileLoad() {
  if (!tileErrorShown) {
    return;
  }
  tileErrorShown = false;
  emit(EVENTS.DATA_ERROR, { message: "" }); // an empty message clears the banner
}
 