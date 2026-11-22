// eventBus.js - a tiny publish/subscribe helper (the "messenger").
// One module announces news with emit(); any module that cares listens with on().
// The sender never needs to know who is listening.

// The agreed event names, in one place, so a typo is easy to spot.
export const EVENTS = Object.freeze({
  VEHICLE_UPDATED: "vehicle:updated",       // payload: { vehicleId, event, isNew }
  VEHICLE_SELECTED: "vehicle:selected",     // payload: { vehicleId }  (null = nothing selected)
  ANOMALY_DETECTED: "anomaly:detected",     // payload: { vehicleId, event }
  COUNTS_CHANGED: "counts:changed",         // payload: { total, active, normal, anomalous }
  CONNECTION_CHANGED: "connection:changed", // payload: { state, label? }  state is "connecting" | "connected" | "disconnected"; label is optional badge text
  DATA_ERROR: "data:error"                  // payload: { message }  (empty message clears the error)
});

// Map of eventName -> Set of handler functions
const listeners = new Map();

// Start listening. Returns a function that stops listening again.
export function on(eventName, handler) {
  if (!listeners.has(eventName)) {
    listeners.set(eventName, new Set());
  }
  listeners.get(eventName).add(handler);
  return () => off(eventName, handler);
}

export function off(eventName, handler) {
  const handlers = listeners.get(eventName);
  if (handlers) {
    handlers.delete(handler);
  }
}

// Announce news to everyone listening for eventName.
export function emit(eventName, payload) {
  const handlers = listeners.get(eventName);
  if (!handlers) {
    return;
  }
  handlers.forEach((handler) => {
    // try/catch: one broken listener must not stop the others.
    try {
      handler(payload);
    } catch (error) {
      console.error(`A listener for "${eventName}" failed:`, error);
    }
  });
}
