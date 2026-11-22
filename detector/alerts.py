from collections import deque

import numpy as np
import pandas as pd


class AlertTracker:
    """
    Turns per-reading flags into alerts, one vehicle at a time.
      open:  at least `open_flags` flags within `window_s` seconds
      close: `close_after_s` seconds without a flag
    update() returns events in the anomaly_flags format: anomaly=True when an alert opens,
    anomaly=False when it closes.
    """

    def __init__(self, open_flags=3, window_s=5, close_after_s=10, method="combined"):
        self.open_flags = open_flags
        self.window_s = window_s
        self.close_after_s = close_after_s
        self.method = method
        self.recent = {}   # vehicle_id -> deque of recent flag timestamps
        self.open = {}     # vehicle_id -> state of the open alert

    def _event(self, vid, ts, anomaly, kind, score):
        return {"vehicle_id": vid, "ts": ts.isoformat(), "method": self.method,
                "anomaly": bool(anomaly), "score": round(float(score), 3), "anomaly_type": kind}

    def update(self, vid, ts, flagged, kind, score):
        ts = pd.Timestamp(ts)
        events = []
        recent = self.recent.setdefault(vid, deque())
        while recent and (ts - recent[0]).total_seconds() > self.window_s:
            recent.popleft()
        alert = self.open.get(vid)

        if flagged:
            recent.append(ts)
            if alert is None and len(recent) >= self.open_flags:
                self.open[vid] = {"type": kind, "last": ts, "peak": score}
                events.append(self._event(vid, ts, True, kind, score))
            elif alert is not None:
                alert["last"] = ts
                alert["peak"] = max(alert["peak"], score)
        elif alert is not None and (ts - alert["last"]).total_seconds() >= self.close_after_s:
            events.append(self._event(vid, ts, False, alert["type"], alert["peak"]))
            del self.open[vid]
        return events


def events_to_alerts(events, end_ts):
    """Pair open/close events into alerts: vehicle_id, anomaly_type, opened_ts, closed_ts."""
    opened, alerts = {}, []
    for e in events:
        ts = pd.Timestamp(e["ts"])
        if e["anomaly"]:
            opened[e["vehicle_id"]] = (ts, e["anomaly_type"])
        elif e["vehicle_id"] in opened:
            t0, kind = opened.pop(e["vehicle_id"])
            alerts.append({"vehicle_id": e["vehicle_id"], "anomaly_type": kind, "opened_ts": t0, "closed_ts": ts})
    for vid, (t0, kind) in opened.items():                       # still open at the end of the data
        alerts.append({"vehicle_id": vid, "anomaly_type": kind, "opened_ts": t0, "closed_ts": pd.Timestamp(end_ts)})
    return pd.DataFrame(alerts, columns=["vehicle_id", "anomaly_type", "opened_ts", "closed_ts"])


def flags_to_alerts(flags, **tracker_args):
    """Offline: run the tracker over a batch of flags."""
    flags = flags.sort_values("ts")
    tracker = AlertTracker(**tracker_args)
    events = []
    for r in flags.itertuples():
        events += tracker.update(r.vehicle_id, r.ts, r.anomaly, r.anomaly_type, r.score)
    return events_to_alerts(events, flags.ts.max())


def evaluate_alerts(alerts, log, grace_s=10):
    """Alert-level scoring against the injection log."""
    alerts = alerts.reset_index(drop=True)
    grace = pd.Timedelta(seconds=grace_s)
    matched = np.zeros(len(alerts), bool)
    delays, type_ok, per_fault, detected = [], 0, [], 0
    for f in log.itertuples():
        a = alerts[(alerts.vehicle_id == f.vehicle_id)
                   & (alerts.opened_ts <= f.end_ts + grace) & (alerts.closed_ts >= f.start_ts)]
        if len(a):
            detected += 1
            matched[a.index] = True
            delays.append(max(0.0, (a.opened_ts.min() - f.start_ts).total_seconds()))
            type_ok += int((a.anomaly_type == f.fault_type).any())
            per_fault.append(len(a))
    return {
        "faults_caught": f"{detected}/{len(log)}",
        "type_correct": f"{type_ok}/{len(log)}",
        "median_delay_s": float(np.median(delays)) if delays else float("nan"),
        "alerts_total": len(alerts),
        "false_alerts": int((~matched).sum()),
        "alerts_per_fault": round(float(np.mean(per_fault)), 2) if per_fault else float("nan"),
    }
