import pandas as pd

from detector import iforest, rules
from detector.evaluate import evaluate
from detector.features import compute_features

normal = compute_features(pd.read_csv("sample_data/normal.csv", parse_dates=["ts"]))
baseline = rules.fit_baseline(normal)
bundle = iforest.fit(normal, baseline)
print("iforest threshold:", round(bundle["threshold"], 4))

rows = []
for name in ["tune_faulty", "test_faulty", "final_faulty"]:
    feats = compute_features(pd.read_csv(f"sample_data/{name}.csv", parse_dates=["ts"]))
    log = pd.read_csv(f"sample_data/{name}_log.csv", parse_dates=["start_ts", "end_ts"])
    for method, flags in [("rules", rules.detect(feats, baseline)),
                          ("iforest", iforest.detect(feats, bundle))]:
        ev, summ, detail = evaluate(flags, log)
        rows.append({"data": name, "method": method, **summ})
        if method == "iforest":
            print(f"\n--- iforest on {name}: per fault ---")
            print(ev.round(1).to_string())
            print("false alarms by vehicle/type:")
            print(detail[detail.false_alarm].groupby(["vehicle_id", "anomaly_type"]).size().to_string())

pd.set_option("display.width", 200)
print("\n", pd.DataFrame(rows).to_string(index=False))
