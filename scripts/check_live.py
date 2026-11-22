"""Score a live run: compare the alert events the backend received with live_fault_log.csv.
Before stopping the mock backend, save its events:  curl -s localhost:8000/anomalies > events.json
"""
import json
from pathlib import Path

import pandas as pd

from detector.alerts import events_to_alerts, evaluate_alerts

events = json.load(open("events.json"))
log = pd.read_csv("live_fault_log.csv", parse_dates=["start_ts", "end_ts"])
if not events:
    raise SystemExit("events.json is empty: no alerts were received")

end_file = Path("live_fault_log.csv.end")          # written by simulator.live when it stops
end = pd.Timestamp(end_file.read_text()) if end_file.exists() else max(pd.Timestamp(e["ts"]) for e in events)

alerts = events_to_alerts(events, end)
full = evaluate_alerts(alerts, log)                # false alerts are judged against every injected fault
recent = log.start_ts >= end - pd.Timedelta(seconds=15)
early = evaluate_alerts(alerts, log[~recent])      # detection is judged only on faults that had time to be caught

print(f"faults injected: {len(log)}  ({int(recent.sum())} started in the last 15 s and are not scored for detection)")
print("detection: ", {k: early[k] for k in ["faults_caught", "type_correct", "median_delay_s", "alerts_per_fault"]})
print(f"false alerts: {full['false_alerts']} of {full['alerts_total']} alerts")
print()
print(alerts.assign(open_for_s=(alerts.closed_ts - alerts.opened_ts).dt.total_seconds()).to_string(index=False))
