// mockSimulator.js - a FRONTEND-ONLY fake data source, for development.
// It is NOT Member 1's Python simulator or ML anomaly detector, and it never talks to the backend.
// It creates telemetry events in the agreed shape (plus the assumed route_id) and passes each one
// to ingest(), exactly like the real data source will.

import { CONFIG } from "./config.js";
import { EVENTS, emit } from "./eventBus.js";
import { ingest } from "./vehicles.js";
import { MOCK_ROUTES, MOCK_VEHICLES, MOCK_ANOMALY_TYPES } from "./mockData.js";

// How many readings a demo anomaly lasts (so it stays visible for a while).
const EPISODE_READINGS = { speed_spike: 3, sudden_stop: 4, route_deviation: 4 };
const METERS_PER_DEGREE_LAT = 111320;

let random = Math.random;   // replaceable, so tests can use repeatable numbers
let timerId = null;         // null = not running
let routesById = new Map(); // route_id -> route with its measured lengths
let fleet = [];             // the moving state of each demo vehicle

// ---------- Small helpers ----------

function round(value, digits) {
  return Number(value.toFixed(digits));
}

function pick(list) {
  return list[Math.floor(random() * list.length)];
}

// Distance and direction between two [lat, lon] points, in metres (east and north).
function toMeters(from, to) {
  const north = (to[0] - from[0]) * METERS_PER_DEGREE_LAT;
  const meanLatitude = (((from[0] + to[0]) / 2) * Math.PI) / 180;
  const east = (to[1] - from[1]) * METERS_PER_DEGREE_LAT * Math.cos(meanLatitude);
  return { east, north };
}

// Measure every segment of a route once, so positions can be found by distance.
function prepareRoute(route) {
  const lengths = [];
  let total = 0;
  for (let i = 1; i < route.points.length; i++) {
    const { east, north } = toMeters(route.points[i - 1], route.points[i]);
    const length = Math.hypot(east, north);
    lengths.push(length);
    total += length;
  }
  return { ...route, lengths, total };
}

// The point that is `distance` metres along the route, plus the direction of travel.
function positionAt(route, distance) {
  let remaining = Math.min(Math.max(distance, 0), route.total);
  const lastIndex = route.lengths.length - 1;

  for (let i = 0; i <= lastIndex; i++) {
    const length = route.lengths[i];
    if (remaining <= length || i === lastIndex) {
      const fraction = Math.min(remaining / length, 1);
      const from = route.points[i];
      const to = route.points[i + 1];
      const { east, north } = toMeters(from, to);
      return {
        lat: from[0] + (to[0] - from[0]) * fraction,
        lon: from[1] + (to[1] - from[1]) * fraction,
        heading: { east: east / length, north: north / length }
      };
    }
    remaining -= length;
  }
}

// Move a position sideways (at a right angle to the direction of travel).
function offsetSideways(position, offsetMeters) {
  const sideEast = -position.heading.north * offsetMeters;
  const sideNorth = position.heading.east * offsetMeters;
  const latitudeRadians = (position.lat * Math.PI) / 180;
  return {
    lat: position.lat + sideNorth / METERS_PER_DEGREE_LAT,
    lon: position.lon + sideEast / (METERS_PER_DEGREE_LAT * Math.cos(latitudeRadians))
  };
}

// ---------- Events ----------

// Builds one telemetry event. anomalyType is null for a normal reading.
// The anomaly_score numbers are PLACEHOLDERS: they have no real meaning.
function makeEvent(vehicle, position, speed, anomalyType) {
  const flagged = anomalyType !== null;
  return {
    vehicle_id: vehicle.vehicleId,
    route_id: vehicle.routeId,
    ts: new Date().toISOString(),
    lat: round(position.lat, 6),
    lon: round(position.lon, 6),
    speed: round(speed, 1),
    anomaly_flag: flagged,
    anomaly_type: anomalyType,
    anomaly_score: round(flagged ? 0.6 + random() * 0.38 : random() * 0.2, 2)
  };
}

function createVehicle(definition) {
  const route = routesById.get(definition.route_id);
  if (route === undefined) {
    throw new Error(`Mock vehicle ${definition.vehicle_id} uses unknown route ${definition.route_id}`);
  }
  return {
    vehicleId: definition.vehicle_id,
    routeId: definition.route_id,
    baseSpeed: definition.baseSpeed,
    distance: definition.startFraction * route.total, // metres along the route
    direction: 1,                                      // 1 = forwards, -1 = backwards
    anomaly: null                                      // or { type, readingsLeft, offsetMeters }
  };
}

function startAnomaly(vehicle, type) {
  vehicle.anomaly = {
    type,
    totalReadings: EPISODE_READINGS[type],
    readingsLeft: EPISODE_READINGS[type],
    // Used by route_deviation: how far (in metres) the vehicle drifts off the route, left or right
    offsetMeters: (random() < 0.5 ? -1 : 1) * (150 + random() * 100)
  };
}

// Move the vehicle along its route; turn around at either end.
function advance(vehicle, speed, intervalSeconds) {
  const route = routesById.get(vehicle.routeId);
  const metres = (speed / 3.6) * intervalSeconds * CONFIG.MOCK_SPEED_UP; // km/h to m/s, then fast-forward
  vehicle.distance += vehicle.direction * metres;

  if (vehicle.distance > route.total) {
    vehicle.distance = route.total - (vehicle.distance - route.total);
    vehicle.direction = -1;
  } else if (vehicle.distance < 0) {
    vehicle.distance = -vehicle.distance;
    vehicle.direction = 1;
  }
  vehicle.distance = Math.min(Math.max(vehicle.distance, 0), route.total);
}

// Produces the next reading of one vehicle.
function stepVehicle(vehicle, intervalSeconds) {
  const route = routesById.get(vehicle.routeId);
  const anomalyType = vehicle.anomaly === null ? null : vehicle.anomaly.type;

  let speed = vehicle.baseSpeed + (random() * 2 - 1) * 3; // normal: base speed plus a little noise
  if (anomalyType === "speed_spike") {
    speed = vehicle.baseSpeed * (2 + random() * 0.6);
  } else if (anomalyType === "sudden_stop") {
    speed = random() * 2;
  }
  speed = Math.max(speed, 0);

  if (anomalyType !== "sudden_stop") {
    advance(vehicle, speed, intervalSeconds); // a stopped vehicle stays where it is
  }

  let position = positionAt(route, vehicle.distance);
  if (anomalyType === "route_deviation") {
    // The drift grows and then shrinks again (a smooth bump), instead of jumping away and back.
    const readingIndex = vehicle.anomaly.totalReadings - vehicle.anomaly.readingsLeft; // 0, 1, 2, ...
    const strength = Math.sin((Math.PI * (readingIndex + 1)) / (vehicle.anomaly.totalReadings + 1));
    position = offsetSideways(position, vehicle.anomaly.offsetMeters * strength);
  }

  const event = makeEvent(vehicle, position, speed, anomalyType);

  if (vehicle.anomaly !== null) {
    vehicle.anomaly.readingsLeft -= 1;
    if (vehicle.anomaly.readingsLeft <= 0) {
      vehicle.anomaly = null; // the anomaly is over
    }
  }
  return event;
}

// ---------- Timer ----------

// Chance that ONE idle vehicle starts an anomaly during ONE update.
// Built from "one anomaly every N seconds in the whole fleet", so it stays the same
// if you change the update interval.
function anomalyChancePerVehicle(intervalSeconds) {
  const everySeconds = CONFIG.MOCK_ANOMALY_EVERY_SECONDS;
  if (!Number.isFinite(everySeconds) || everySeconds <= 0) {
    return 0; // automatic anomalies are switched off
  }
  return intervalSeconds / (everySeconds * fleet.length);
}

function tick() {
  const intervalSeconds = CONFIG.MOCK_UPDATE_INTERVAL_MS / 1000;
  const chance = anomalyChancePerVehicle(intervalSeconds);

  // Pass 1: maybe start new anomalies, never more than the configured number at once.
  let active = fleet.filter((vehicle) => vehicle.anomaly !== null).length;
  fleet.forEach((vehicle) => {
    if (vehicle.anomaly === null && active < CONFIG.MOCK_MAX_CONCURRENT_ANOMALIES &&
        random() < chance) {
      startAnomaly(vehicle, pick(MOCK_ANOMALY_TYPES));
      active += 1;
    }
  });

  // Pass 2: every vehicle reports once. Same entry point as the real data source.
  fleet.forEach((vehicle) => ingest(stepVehicle(vehicle, intervalSeconds)));
}

// ---------- Public functions ----------

export function startMockSimulator({ random: randomFunction = Math.random } = {}) {
  if (timerId !== null) {
    return; // already running
  }
  const interval = CONFIG.MOCK_UPDATE_INTERVAL_MS;
  if (!Number.isFinite(interval) || interval < 50) {
    throw new Error("MOCK_UPDATE_INTERVAL_MS must be a number of at least 50");
  }

  random = randomFunction;
  routesById = new Map(MOCK_ROUTES.map((route) => [route.route_id, prepareRoute(route)]));
  fleet = MOCK_VEHICLES.map(createVehicle);

  emit(EVENTS.CONNECTION_CHANGED, { state: "connected", label: "Connected (simulated)" });

  // First readings right away, so the map is not empty for the first interval.
  fleet.forEach((vehicle) => {
    const route = routesById.get(vehicle.routeId);
    ingest(makeEvent(vehicle, positionAt(route, vehicle.distance), vehicle.baseSpeed, null));
  });

  timerId = setInterval(tick, interval);
}

export function stopMockSimulator() {
  if (timerId === null) {
    return;
  }
  clearInterval(timerId);
  timerId = null;
  emit(EVENTS.CONNECTION_CHANGED, { state: "disconnected", label: "Simulator stopped" });
}

export function isMockRunning() {
  return timerId !== null;
}

// Starts a demo anomaly on the next update. Both arguments are optional:
//   triggerMockAnomaly("V003", "sudden_stop")   a specific vehicle and type
//   triggerMockAnomaly()                         random vehicle, random type
// Returns true if it worked.
export function triggerMockAnomaly(vehicleId = null, type = null) {
  if (timerId === null) {
    console.warn("The mock simulator is not running.");
    return false;
  }

  const chosenType = type ?? pick(MOCK_ANOMALY_TYPES);
  if (!MOCK_ANOMALY_TYPES.includes(chosenType)) {
    console.warn(`Unknown anomaly type "${chosenType}". Use one of: ${MOCK_ANOMALY_TYPES.join(", ")}`);
    return false;
  }

  const candidates = vehicleId === null
    ? fleet.filter((vehicle) => vehicle.anomaly === null)
    : fleet.filter((vehicle) => vehicle.vehicleId === vehicleId);
  if (candidates.length === 0) {
    console.warn(`No mock vehicle available for "${vehicleId}".`);
    return false;
  }

  startAnomaly(vehicleId === null ? pick(candidates) : candidates[0], chosenType);
  return true;
}
