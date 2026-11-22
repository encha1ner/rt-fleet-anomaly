from collections import defaultdict, deque

import pandas as pd

from detector.alerts import AlertTracker
from simulator.routes import load_routes
from detector.features import compute_features

BUFFER = 30   # readings kept per bus; the features need at least 11


class StreamDetector:
    """Feed it new readings each tick; it keeps a short history per bus and returns alert events."""

    def __init__(self, detector, method="combined", tracker=None, buffer=BUFFER):
        self.det = detector
        self.method = method
        self.tracker = tracker or AlertTracker(method=method)
        self.buf = defaultdict(lambda: deque(maxlen=buffer))
        self.last_ts = {}
        self.routes = load_routes()      # loaded once
        self.route_objs = {}             # Route objects built once and reused

    def update(self, readings):
        """readings: list of dicts (vehicle_id, route_id, ts, lat, lon, speed), one per bus per call."""
        touched = {}
        for r in readings:
            ts = pd.Timestamp(r["ts"])
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            vid = r["vehicle_id"]
            if vid in self.last_ts and ts <= self.last_ts[vid]:
                continue                                   # duplicate or out of order
            self.last_ts[vid] = ts
            self.buf[vid].append({**r, "ts": ts})
            touched[vid] = True
        if not touched:
            return None, []

        df = pd.DataFrame([row for vid in touched for row in self.buf[vid]])
        feats = compute_features(df, self.routes, self.route_objs)
        latest = feats.sort_values("ts").groupby("vehicle_id").tail(1)
        flags = self.det.detect(latest, self.method)

        events = []
        for r in flags.sort_values("ts").itertuples():
            events += self.tracker.update(r.vehicle_id, r.ts, r.anomaly, r.anomaly_type, r.score)
        return flags, events
