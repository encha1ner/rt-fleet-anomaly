import pandas as pd
from detector.features import compute_features

f = compute_features(pd.read_csv("sample_data/normal.csv", parse_dates=["ts"])).dropna()
print(f[["dist_from_route", "speed_gap", "accel", "stopped_secs", "heading_change"]]
      .describe(percentiles=[.5, .99, .999]).round(1))
print(f.groupby("route_id").speed.agg(["median", "min", "max"]).round(1))
