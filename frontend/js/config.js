// config.js - one place for every setting the dashboard uses.
// Other files import CONFIG instead of hard-coding values.

export const CONFIG = Object.freeze({
  // true  = use frontend-only simulated data (mockSimulator.js)
  // false = use the real backend (only after Member 2 confirms the API contract)
  USE_MOCK_DATA: true,

  // How often the mock simulator creates new events, in milliseconds
  MOCK_UPDATE_INTERVAL_MS: 3000,

  // Mock only: fast-forward factor. At 4, a vehicle moves as if 4 times more time had passed,
  // so movement is visible on the map. Lower = slower, calmer movement. 1 = real speed.
  MOCK_SPEED_UP: 4,
  // Mock only: on average, one demo anomaly starts somewhere in the fleet every this many
  // seconds. Higher = calmer. 0 = no automatic anomalies (use triggerMockAnomaly instead).
  MOCK_ANOMALY_EVERY_SECONDS: 60,
  // Mock only: how many vehicles may be anomalous at the same time
  MOCK_MAX_CONCURRENT_ANOMALIES: 1,

  // Map start position: Lucknow [latitude, longitude]
  MAP_CENTER: [26.8467, 80.9462],
  MAP_ZOOM: 12,

  // WORKING ASSUMPTIONS - not confirmed by teammates yet
  ACTIVE_WINDOW_SECONDS: 30, // a vehicle is "active" if data arrived in the last 30 s
  COUNTS_REFRESH_MS: 5000,   // how often the overview cards are re-checked (so "active" can expire)
  HISTORY_LENGTH: 30,        // speed readings kept per vehicle for the chart
  MAX_ALERTS: 50,            // oldest alerts are dropped beyond this number
  RECONNECT_DELAY_MS: 3000,  // wait before retrying a lost WebSocket connection
  SPEED_UNIT: "km/h",        // ASSUMED. Confirm with Member 1.
  SPEED_UNIT_CONFIRMED: false, // set to true once confirmed: removes the "assumed" note on the chart
  // anomaly_score is shown as a plain number (assumed 0 to 1, higher = more unusual).
  // It is never shown as a percentage until Member 1 confirms its meaning.

  // Real backend. Left empty on purpose: do not guess these values.
  // Fill them in Phase 8 using the contract from Member 2.
  BACKEND: {
    BASE_URL: "",
    WS_URL: "",
    ENDPOINTS: {}
  }
});
