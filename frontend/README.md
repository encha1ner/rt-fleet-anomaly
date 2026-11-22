# Vehicle Anomaly Detection System - Frontend

Dashboard for the Vehicle Anomaly Detection System (Member 3).
Built with plain HTML, CSS and JavaScript, plus Leaflet.js, OpenStreetMap and Chart.js.

## Run it locally

1. Open the `frontend` folder in VS Code.
2. Install the **Live Server** extension (Ritwick Dey).
3. Right-click `index.html` and choose **Open with Live Server**.

Backup option (needs Python): run `python -m http.server 5500` inside `frontend/`,
then open http://localhost:5500 in your browser.

Do not open `index.html` by double-clicking it. Browsers block JavaScript modules on `file://` pages.
You need internet access, because Leaflet, Chart.js and the map tiles load from the web.

## Mock mode (simulated data)

Open `js/config.js`:

- `USE_MOCK_DATA: true`  -> frontend-only simulated data (banner "Simulated data" is shown)
- `USE_MOCK_DATA: false` -> real backend (only after Member 2 confirms the API contract)

The mock simulator is only for frontend development.
It is NOT the Python simulator or the ML anomaly detector built by Member 1.

## Folder structure

- `index.html`  page structure
- `css/style.css`  styling
- `js/config.js`  settings and temporary assumptions
- `js/app.js`  entry point
- `js/eventBus.js`, `js/utils.js`  shared helpers
- `js/api.js`  backend communication only
- `js/vehicles.js`  application state
- `js/map.js`, `js/charts.js`, `js/alerts.js`  UI modules
- `js/mockData.js`, `js/mockSimulator.js`  frontend-only mock data
- `assets/icons/`  icons

## Try the mock simulator

With `USE_MOCK_DATA: true` the dashboard starts the simulator automatically.
To create an anomaly on demand, open the browser console and run:

    const sim = await import("./js/mockSimulator.js");
    sim.triggerMockAnomaly("V003", "sudden_stop");   // or "speed_spike", "route_deviation"
    sim.triggerMockAnomaly();                         // random vehicle, random type

## Status

Phases 1-7 done (setup, layout, styling, state, map, chart and alerts, mock data).
Next: Phase 8 (real backend), which waits for the API contract from Member 2.
