import math
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

FAULT_TYPES = ["sudden_stop", "speed_spike", "route_deviation"]
M_PER_DEG = 111_320.0

WARMUP_S = 120     # no faults at the start (detector needs history)
COOLDOWN_S = 60    # no faults right at the end
MIN_GAP_S = 60     # minimum quiet time between faults on the same bus


@dataclass
class Fault:
    vehicle_id: str
    fault_type: str
    start_s: int        # seconds since simulation start
    end_s: int
    magnitude: float    # spike: extra km/h | deviation: peak offset in m (signed) | stop: 0

    def active(self, t):
        return self.start_s <= t < self.end_s

    def offset_m(self, t):
        """Deviation only: ramp out, hold, ramp back (25% / 50% / 25%)."""
        p = (t - self.start_s) / (self.end_s - self.start_s)
        shape = min(1.0, p / 0.25, (1.0 - p) / 0.25)
        return self.magnitude * max(0.0, shape)


def _draw(ftype, rng):
    """Random duration (s) and magnitude for one fault of the given type."""
    if ftype == "sudden_stop":
        return int(rng.integers(60, 181)), 0.0
    if ftype == "speed_spike":
        return int(rng.integers(20, 41)), float(rng.uniform(35, 50))
    return int(rng.integers(60, 121)), float(rng.uniform(300, 1000) * rng.choice([-1, 1]))


def make_schedule(vehicle_ids, duration_s, n_faults=18, seed=42):
    """Pick random faults, cycling through the types, with no overlaps on one bus."""
    rng = np.random.default_rng(seed + 1000)   # own random stream: never disturbs the vehicles
    faults, busy = [], {v: [] for v in vehicle_ids}
    for _ in range(2000):                      # give up eventually instead of looping forever
        if len(faults) >= n_faults:
            break
        ftype = FAULT_TYPES[len(faults) % len(FAULT_TYPES)]
        vid = vehicle_ids[rng.integers(len(vehicle_ids))]
        dur, mag = _draw(ftype, rng)
        latest_start = duration_s - COOLDOWN_S - dur
        if latest_start <= WARMUP_S:
            continue
        start = int(rng.integers(WARMUP_S, latest_start))
        end = start + dur
        if any(start < e + MIN_GAP_S and end + MIN_GAP_S > s for s, e in busy[vid]):
            continue
        busy[vid].append((start, end))
        faults.append(Fault(vid, ftype, start, end, mag))
    return faults


def offset_from_route(route, s, lat, lon, offset_m):
    """Move a point sideways (90 degrees to the direction of travel) by offset_m metres."""
    lat2, lon2 = route.position(s + 10)
    coslat = math.cos(math.radians(lat))
    dy = (lat2 - lat) * M_PER_DEG
    dx = (lon2 - lon) * M_PER_DEG * coslat
    norm = math.hypot(dx, dy) or 1.0
    px, py = -dy / norm, dx / norm             # unit vector pointing left of travel
    return (lat + offset_m * py / M_PER_DEG,
            lon + offset_m * px / (M_PER_DEG * coslat))


def faults_to_df(faults, start):
    """The injection log: the answer key used later to evaluate the detectors."""
    rows = [{"vehicle_id": f.vehicle_id,
             "fault_type": f.fault_type,
             "start_ts": start + timedelta(seconds=f.start_s),
             "end_ts": start + timedelta(seconds=f.end_s),
             "magnitude": round(f.magnitude, 1)}
            for f in sorted(faults, key=lambda f: f.start_s)]
    return pd.DataFrame(rows, columns=["vehicle_id", "fault_type", "start_ts", "end_ts", "magnitude"])
draw_params = _draw   # public name, used by live.py
