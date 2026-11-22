import argparse
import time

from common.api import Api
from detector.detector import MODEL_PATH, Detector
from detector.stream import StreamDetector


def main():
    ap = argparse.ArgumentParser(description="Live detector: polls the backend, posts alert events.")
    ap.add_argument("--api", default="http://localhost:8000", help="backend base URL")
    ap.add_argument("--interval", type=float, default=0.5, help="seconds between polls")
    ap.add_argument("--method", default="combined", choices=["rules", "iforest", "combined"])
    ap.add_argument("--model", default=str(MODEL_PATH))
    args = ap.parse_args()

    try:
        det = Detector.load(args.model)
    except FileNotFoundError:
        raise SystemExit(f"No model at {args.model}. Train one first: python -m detector.detector")

    api = Api(args.api)
    stream = StreamDetector(det, method=args.method)
    print(f"Detector running ({args.method}), polling {args.api}/vehicles/latest every {args.interval}s. Ctrl+C to stop.")

    n_events, last_report = 0, time.monotonic()
    try:
        while True:
            t0 = time.monotonic()
            data = api.get_json("/vehicles/latest")
            if isinstance(data, dict):
                data = data.get("vehicles", data.get("readings", []))
            if data:
                _, events = stream.update(data)
                if events:
                    api.post("/anomalies", {"anomalies": events})
                    n_events += len(events)
                    for e in events:
                        state = "OPEN  " if e["anomaly"] else "CLOSED"
                        print(f"[alert {state}] {e['vehicle_id']} {e['anomaly_type']} score={e['score']} at {e['ts']}")
            if time.monotonic() - last_report > 15:
                print(f"[detector] events sent: {n_events} | api ok={api.ok} failed={api.failed}")
                last_report = time.monotonic()
            time.sleep(max(0.0, args.interval - (time.monotonic() - t0)))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
