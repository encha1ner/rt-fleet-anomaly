import argparse

import pandas as pd

from detector.evaluate import evaluate
from detector.features import compute_features
from detector.rules import detect, fit_baseline

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="tune_faulty", help="tune_faulty (default) or test_faulty")
args = ap.parse_args()

normal = compute_features(pd.read_csv("sample_data/normal.csv", parse_dates=["ts"]))
baseline = fit_baseline(normal)
print("baseline speeds:", {k: round(v, 1) for k, v in baseline.items()})

data = compute_features(pd.read_csv(f"sample_data/{args.data}.csv", parse_dates=["ts"]))
log = pd.read_csv(f"sample_data/{args.data}_log.csv", parse_dates=["start_ts", "end_ts"])

flags = detect(data, baseline)
events, summary, detail = evaluate(flags, log)

pd.set_option("display.width", 200)
print(f"\n=== {args.data} ===")
print(events.round(1))
print(summary)
print("\nfalse alarms by vehicle and type:")
print(detail[detail.false_alarm].groupby(["vehicle_id", "anomaly_type"]).size())
