// vehicles.js - the application state ("the memory").
// Stores the latest event per vehicle and a short speed history.
// No DOM code here: it only stores data and announces changes on the event bus.
// Every data source (mock or real) calls ingest(event).
 
import { CONFIG } from "./config.js";
import { EVENTS, emit } from "./eventBus.js";
import { validateTelemetryEvent } from "./utils.js";
 
// vehicle_id -> { event: the latest telemetry event, receivedAt: browser time in ms }
const vehicles = new Map();
 
// vehicle_id -> [ { ts, speed, isAnomalous }, ... ] oldest first, at most CONFIG.HISTORY_LENGTH items
// (isAnomalous is our own copy of anomaly_flag, so the chart can mark flagged readings)
const speedHistory = new Map();
 
let selectedVehicleId = null;
 
// The single entry point for new data. Returns true if the event was accepted.
export function ingest(event) {
  const problems = validateTelemetryEvent(event);
  if (problems.length > 0) {
    console.warn("Ignored invalid telemetry event:", problems, event);
    return false;
  }
 
  const vehicleId = event.vehicle_id;
  const isNew = !vehicles.has(vehicleId);
 
  // { ...event } stores a copy, so later changes to the original can't alter our state.
  vehicles.set(vehicleId, { event: { ...event }, receivedAt: Date.now() });
  addToHistory(vehicleId, event);
 
  emit(EVENTS.VEHICLE_UPDATED, { vehicleId, event, isNew });
  if (event.anomaly_flag) {
    emit(EVENTS.ANOMALY_DETECTED, { vehicleId, event });
  }
  publishCounts();
  return true;
}
 
function addToHistory(vehicleId, event) {
  if (!speedHistory.has(vehicleId)) {
    speedHistory.set(vehicleId, []);
  }
  const points = speedHistory.get(vehicleId);
  points.push({ ts: event.ts, speed: event.speed, isAnomalous: event.anomaly_flag });
  while (points.length > CONFIG.HISTORY_LENGTH) {
    points.shift(); // drop the oldest point
  }
}
 
// Returns { event, receivedAt } or undefined if the vehicle is unknown.
export function getVehicle(vehicleId) {
  return vehicles.get(vehicleId);
}
 
// Returns a list of the latest event of every known vehicle.
export function getAllVehicles() {
  return Array.from(vehicles.values(), (record) => record.event);
}
 
// Returns a copy of the speed history, so outside code can't change our data.
export function getSpeedHistory(vehicleId) {
  return [...(speedHistory.get(vehicleId) ?? [])];
}
 
export function getSelectedVehicleId() {
  return selectedVehicleId;
}
 
// Select a vehicle by id, or pass null to clear the selection.
export function selectVehicle(vehicleId) {
  if (vehicleId !== null && !vehicles.has(vehicleId)) {
    console.warn(`Cannot select unknown vehicle "${vehicleId}"`);
    return;
  }
  selectedVehicleId = vehicleId;
  emit(EVENTS.VEHICLE_SELECTED, { vehicleId });
}
 
// The numbers for the four overview cards, calculated from the stored data.
//   total     = different vehicle_ids seen so far
//   active    = data received within the last ACTIVE_WINDOW_SECONDS (browser clock)
//   anomalous = latest event has anomaly_flag true
//   normal    = total - anomalous
export function getCounts() {
  const now = Date.now();
  const activeWindowMs = CONFIG.ACTIVE_WINDOW_SECONDS * 1000;
  let active = 0;
  let anomalous = 0;
 
  vehicles.forEach(({ event, receivedAt }) => {
    if (now - receivedAt <= activeWindowMs) {
      active += 1;
    }
    if (event.anomaly_flag) {
      anomalous += 1;
    }
  });
 
  const total = vehicles.size;
  return { total, active, normal: total - anomalous, anomalous };
}
 
// Announces the current counts. Does nothing until the first vehicle arrives,
// so the cards keep showing "--" (unknown) instead of a misleading 0.
export function publishCounts() {
  if (vehicles.size === 0) {
    return;
  }
  emit(EVENTS.COUNTS_CHANGED, getCounts());
}
 