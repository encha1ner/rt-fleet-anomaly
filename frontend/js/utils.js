// utils.js - small shared helpers: time, number formatting, event checks.
// No DOM, Leaflet or Chart.js code here.

import { CONFIG } from "./config.js";

// Does the text end with Z or an offset such as +05:30 ?
const HAS_TIME_ZONE = /(Z|[+-]\d{2}:?\d{2})$/i;

// Turns an ISO 8601 UTC string like "2026-11-18T16:30:00Z" into a Date object.
// Returns null when the text is not a valid timestamp.
export function parseTimestamp(ts) {
  if (typeof ts !== "string" || ts.trim() === "") {
    return null;
  }
  let text = ts.trim();

  // Trap: JavaScript treats "2026-11-18T16:30:00" (no Z) as LOCAL time.
  // The contract says UTC, so we add Z ourselves and warn.
  if (!HAS_TIME_ZONE.test(text)) {
    console.warn(`Timestamp "${ts}" has no time zone. Treating it as UTC.`);
    text += "Z";
  }

  const date = new Date(text);
  return Number.isNaN(date.getTime()) ? null : date;
}

// Shows a UTC timestamp as local date and time in the viewer's time zone.
export function formatLocalTime(ts) {
  const date = parseTimestamp(ts);
  if (date === null) {
    return "--";
  }
  return date.toLocaleString([], { dateStyle: "medium", timeStyle: "medium" });
}

// Time of day only (for chart labels), in the viewer's local time zone.
export function formatClock(ts) {
  const date = parseTimestamp(ts);
  if (date === null) {
    return "--";
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function formatNumber(value, digits) {
  return isFiniteNumber(value) ? value.toFixed(digits) : "--";
}

export function formatSpeed(speed) {
  return isFiniteNumber(speed) ? `${formatNumber(speed, 1)} ${CONFIG.SPEED_UNIT}` : "--";
}

export function formatCoordinate(value) {
  return formatNumber(value, 4);
}

// Plain number, never a percentage (the meaning of anomaly_score is unconfirmed).
export function formatScore(score) {
  return formatNumber(score, 2);
}

const ANOMALY_TYPE_LABELS = {
  speed_spike: "Speed spike",
  sudden_stop: "Sudden stop",
  route_deviation: "Route deviation"
};

// Friendly name for an anomaly_type. Handles null and types we don't know yet.
export function formatAnomalyType(type) {
  if (type === null || type === undefined || type === "") {
    return "Unknown type";
  }
  return ANOMALY_TYPE_LABELS[type] ?? type;
}

// One-line status text shared by the details panel and the map popups.
export function formatStatus(event) {
  return event.anomaly_flag ? `Anomalous: ${formatAnomalyType(event.anomaly_type)}` : "Normal";
}

// PROVISIONAL duplicate rule (unconfirmed): same vehicle + same time + same type = same event.
// It lives in one function so it is easy to replace when Member 2 confirms the real rule.
export function getEventKey(event) {
  return `${event.vehicle_id}|${event.ts}|${event.anomaly_type ?? ""}`;
}

// Checks one telemetry event against the agreed contract.
// Returns a list of problems. An empty list means the event is valid.
// anomaly_type, anomaly_score and route_id may be null or missing.
export function validateTelemetryEvent(event) {
  if (event === null || typeof event !== "object") {
    return ["event is not an object"];
  }

  const problems = [];

  if (typeof event.vehicle_id !== "string" || event.vehicle_id.trim() === "") {
    problems.push("vehicle_id must be a non-empty string");
  }
  if (parseTimestamp(event.ts) === null) {
    problems.push("ts must be a valid ISO 8601 timestamp");
  }
  if (!isFiniteNumber(event.lat) || event.lat < -90 || event.lat > 90) {
    problems.push("lat must be a number between -90 and 90");
  }
  if (!isFiniteNumber(event.lon) || event.lon < -180 || event.lon > 180) {
    problems.push("lon must be a number between -180 and 180");
  }
  if (!isFiniteNumber(event.speed)) {
    problems.push("speed must be a number");
  }
  if (typeof event.anomaly_flag !== "boolean") {
    problems.push("anomaly_flag must be true or false");
  }
  // route_id is ASSUMED to be sent by the backend (unconfirmed). Optional, and not required.
  if (event.route_id != null && typeof event.route_id !== "string" && !isFiniteNumber(event.route_id)) {
    problems.push("route_id must be a string or a number");
  }
  if (event.anomaly_type != null && typeof event.anomaly_type !== "string") {
    problems.push("anomaly_type must be a string or null");
  }
  if (event.anomaly_score != null && !isFiniteNumber(event.anomaly_score)) {
    problems.push("anomaly_score must be a number or null");
  }

  return problems;
}
