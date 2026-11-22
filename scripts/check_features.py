import pandas as pd
from detector.features import compute_features, FEATURES

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)

df = pd.read_csv("sample_data/test_faulty.csv", parse_dates=["ts"])
log = pd.read_csv("sample_data/test_faulty_log.csv", parse_dates=["start_ts", "end_ts"])

f = compute_features(df)
f["label"] = "normal"
for _, r in log.iterrows():
    m = (f.vehicle_id == r.vehicle_id) & (f.ts >= r.start_ts) & (f.ts < r.end_ts)
    f.loc[m, "label"] = r.fault_type

cols = ["step_dist", "speed_gap", "heading_change", "dist_from_route", "accel", "stopped_secs"]
print(f.groupby("label")[cols].median().round(1))
print(f.groupby("label")[cols].quantile(0.95).round(1))
print(f.groupby("label").size())
