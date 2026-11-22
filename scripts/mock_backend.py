"""
Stand-in for Member 2's backend so the simulator and detector can be tested without it.
  POST /telemetry   {"readings": [...]}     -> stores the newest reading per bus
  GET  /vehicles/latest                     -> list of newest readings
  POST /anomalies   {"anomalies": [...]}    -> prints and stores alert events
  GET  /anomalies                           -> all stored events
Run: python -m scripts.mock_backend
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LATEST, EVENTS, COUNT = {}, [], {"telemetry_batches": 0}


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/vehicles/latest":
            self._send(list(LATEST.values()))
        elif self.path == "/anomalies":
            self._send(EVENTS)
        elif self.path == "/health":
            self._send({"ok": True, **COUNT, "events": len(EVENTS)})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/telemetry":
            for r in body.get("readings", []):
                LATEST[r["vehicle_id"]] = r
            COUNT["telemetry_batches"] += 1
            self._send({"stored": len(body.get("readings", []))})
        elif self.path == "/anomalies":
            for e in body.get("anomalies", []):
                EVENTS.append(e)
                print(f"[mock] anomaly event: {e}")
            self._send({"stored": len(body.get("anomalies", []))})
        else:
            self._send({"error": "not found"}, 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Mock backend on http://localhost:8000  (Ctrl+C to stop)")
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
