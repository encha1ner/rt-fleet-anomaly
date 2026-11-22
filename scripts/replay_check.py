"""Feed a CSV through the streaming detector one second at a time and compare with the batch result."""
import argparse

import pandas as pd

from detector.alerts import events_to_alerts, evaluate_alerts, flags_to_alerts
from detector.detector import MODEL_PATH, Detector
from detector.features import compute_features
from detector.stream import StreamDetector

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="tune_faulty")
ap.add_argument("--method", default="combined")
args = ap.parse_args()

det = Detector.load(MODEL_PATH)
df = pd.read_csv(f"sample_data/{args.data}.csv", parse_dates=["ts"])
log = pd.read_csv(f"sample_data/{args.data}_log.csv", parse_dates=["start_ts", "end_ts"])

# streaming: one tick (one reading per bus) at a time
stream, events, stream_flags = StreamDetector(det, method=args.method), [], []
for ts, tick in df.groupby("ts"):
    flags, ev = stream.update(tick.to_dict("records"))
    if flags is not None:
        stream_flags.append(flags)
    events += ev
stream_flags = pd.concat(stream_flags)

# batch: everything at once
batch_flags = det.detect(compute_features(df), args.method)

m = stream_flags.merge(batch_flags, on=["vehicle_id", "ts"], suffixes=("_s", "_b"))
print(f"rows compared: {len(m)}")
print(f"anomaly flag differs in {(m.anomaly_s != m.anomaly_b).sum()} rows")
print("score max abs diff:", round((m.score_s - m.score_b).abs().max(), 4))

alerts = events_to_alerts(events, df.ts.max())
print("\nstreaming alerts:", evaluate_alerts(alerts, log))
print("batch alerts:    ", evaluate_alerts(flags_to_alerts(batch_flags, method=args.method), log))
