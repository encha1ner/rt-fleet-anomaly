import pandas as pd

from detector import iforest, rules
from detector.evaluate import evaluate
from detector.features import compute_features

normal = compute_features(pd.read_csv("sample_data/normal.csv", parse_dates=["ts"]))
baseline = rules.fit_baseline(normal)

# Tuning set ONLY. The test set stays untouched until you have chosen a variant.
tune = compute_features(pd.read_csv("sample_data/tune_faulty.csv", parse_dates=["ts"]))
log = pd.read_csv("sample_data/tune_faulty_log.csv", parse_dates=["start_ts", "end_ts"])

ALL = iforest.IF_FEATURES
NO_HEAD = [c for c in ALL if c != "heading_change"]
CORE = ["speed_ratio", "accel", "dist_from_route", "speed_std10"]

VARIANTS = [
    ("all 6 features, q=0.999 (current)", ALL, 0.999),
    ("drop heading_change, q=0.999", NO_HEAD, 0.999),
    ("drop heading_change, q=0.995", NO_HEAD, 0.995),
    ("drop heading_change, q=0.99", NO_HEAD, 0.99),
    ("core 4 features, q=0.999", CORE, 0.999),
    ("core 4 features, q=0.995", CORE, 0.995),
    ("core 4 features, q=0.99", CORE, 0.99),
]

rows = []
flags = rules.detect(tune, baseline)
_, s, _ = evaluate(flags, log)
rows.append({"variant": "RULES (for reference)", **s})
for name, feats, q in VARIANTS:
    bundle = iforest.fit(normal, baseline, quantile=q, features=feats)
    _, s, _ = evaluate(iforest.detect(tune, bundle), log)
    rows.append({"variant": name, **s})

pd.set_option("display.width", 220)
cols = ["variant", "row_precision", "row_recall", "events_detected", "median_delay_s", "false_alarm_rows"]
print(pd.DataFrame(rows)[cols].to_string(index=False))
