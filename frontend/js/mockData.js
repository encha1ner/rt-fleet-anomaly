// mockData.js - the starting data for the frontend-only demo.
// Everything here is INVENTED for development. The waypoints are approximate points around
// Lucknow, not real road geometry. This is NOT data from Member 1 or Member 2.

// The three anomaly types of the project (speed_spike, sudden_stop, route_deviation).
export const MOCK_ANOMALY_TYPES = ["speed_spike", "sudden_stop", "route_deviation"];

// Demo routes. Each point is [latitude, longitude]. Vehicles travel along them and turn
// around at the ends.
export const MOCK_ROUTES = [
  {
    route_id: "R01",
    name: "Charbagh - Hazratganj - Gomti Nagar (demo)",
    points: [
      [26.8318, 80.9237],
      [26.8390, 80.9340],
      [26.8467, 80.9462],
      [26.8520, 80.9700],
      [26.8560, 80.9990]
    ]
  },
  {
    route_id: "R02",
    name: "Alambagh - Charbagh - University (demo)",
    points: [
      [26.8090, 80.9020],
      [26.8200, 80.9130],
      [26.8318, 80.9237],
      [26.8480, 80.9230],
      [26.8620, 80.9240]
    ]
  },
  {
    route_id: "R03",
    name: "Airport - Alambagh - Hazratganj (demo)",
    points: [
      [26.7606, 80.8893],
      [26.7850, 80.8960],
      [26.8090, 80.9020],
      [26.8300, 80.9300],
      [26.8467, 80.9462]
    ]
  }
];

// The ten demo vehicles V001 - V010.
//   startFraction: where on the route the vehicle starts (0 = start, 1 = end)
//   baseSpeed:     its normal speed (in the assumed unit, km/h)
export const MOCK_VEHICLES = [
  { vehicle_id: "V001", route_id: "R01", startFraction: 0.05, baseSpeed: 32 },
  { vehicle_id: "V002", route_id: "R01", startFraction: 0.35, baseSpeed: 38 },
  { vehicle_id: "V003", route_id: "R01", startFraction: 0.65, baseSpeed: 28 },
  { vehicle_id: "V004", route_id: "R01", startFraction: 0.90, baseSpeed: 42 },
  { vehicle_id: "V005", route_id: "R02", startFraction: 0.10, baseSpeed: 36 },
  { vehicle_id: "V006", route_id: "R02", startFraction: 0.45, baseSpeed: 30 },
  { vehicle_id: "V007", route_id: "R02", startFraction: 0.80, baseSpeed: 40 },
  { vehicle_id: "V008", route_id: "R03", startFraction: 0.10, baseSpeed: 45 },
  { vehicle_id: "V009", route_id: "R03", startFraction: 0.50, baseSpeed: 34 },
  { vehicle_id: "V010", route_id: "R03", startFraction: 0.85, baseSpeed: 29 }
];
