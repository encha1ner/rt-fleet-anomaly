import argparse

import pandas as pd

from detector.alerts import evaluate_alerts, flags_to_alerts
from detector.detector import Detector
from detector.features import compute_features

ap = argparse.ArgumentParser()
ap.add_argument("--open-flags", type=int, default=3)
ap.add_argument("--close-after", type=int, default=10)
args = ap.parse_args()

normal = compute_features(pd.read_csv("sample_data/normal.csv", parse_dates=["ts"]))
det = Detector.train(normal)

rows = []
for name in ["tune_faulty", "test_faulty", "final_faulty"]:
    try:
        feats = compute_features(pd.read_csv(f"sample_data/{name}.csv", parse_dates=["ts"]))
        log = pd.read_csv(f"sample_data/{name}_log.csv", parse_dates=["start_ts", "end_ts"])
    except FileNotFoundError:
        continue
    for method in ["rules", "iforest", "combined"]:
        alerts = flags_to_alerts(det.detect(feats, method), open_flags=args.open_flags,
                                 close_after_s=args.close_after, method=method)
        rows.append({"data": name, "method": method, **evaluate_alerts(alerts, log)})

pd.set_option("display.width", 220)
print(f"open_flags={args.open_flags}, close_after={args.close_after}s")
print(pd.DataFrame(rows).to_string(index=False))
