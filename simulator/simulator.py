import argparse
import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from simulator.routes import Route, load_routes

# Cruise speed range (km/h) by route kind
CRUISE_KMH = {"city": (25, 40), "highway": (50, 70)}

# Fleet plan: how many vehicles on each route (10 total)
FLEET = {"R1": 2, "R2": 2, "R3": 2, "LKO-KNP": 2, "LKO-AYD": 1, "LKO-GKP": 1}


class Vehicle:
    def __init__(self, vehicle_id, route_id, route, rng, cruise_kmh):
        self.id = vehicle_id
        self.route_id = route_id
        self.route = route
        self.rng = rng
        self.cruise = cruise_kmh
        self.speed = cruise_kmh                   # km/h
        self.s = rng.uniform(0, route.length)     # metres travelled along the route

    def step(self, dt):
        # speed drifts around the cruise speed with random noise
        self.speed += (0.2 * (self.cruise - self.speed) * dt
                       + self.rng.normal(0, 0.8) * math.sqrt(dt))
        self.speed = float(np.clip(self.speed, 0, 100))
        self.s += self.speed / 3.6 * dt           # km/h -> m/s

        lat, lon = self.route.position(self.s)
        # GPS noise of about 3 m
        lat += self.rng.normal(0, 3) / 111_320
        lon += self.rng.normal(0, 3) / (111_320 * math.cos(math.radians(lat)))
        return lat, lon, self.speed


def generate(duration_s=1800, dt=1.0, seed=42, start=None):
    rng = np.random.default_rng(seed)
    start = start or datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    routes = load_routes()

    vehicles, n = [], 0
    for rid, count in FLEET.items():
        info = routes[rid]
        route = Route(info["points"])
        lo, hi = CRUISE_KMH[info["kind"]]
        for _ in range(count):
            n += 1
            vehicles.append(Vehicle(f"bus_{n:02d}", rid, route, rng, rng.uniform(lo, hi)))

    rows = []
    for k in range(int(duration_s / dt)):
        ts = start + timedelta(seconds=k * dt)
        for v in vehicles:
            lat, lon, speed = v.step(dt)
            rows.append((v.id, v.route_id, ts, round(lat, 6), round(lon, 6), round(speed, 1)))

    return pd.DataFrame(rows, columns=["vehicle_id", "route_id", "ts", "lat", "lon", "speed"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=1800, help="seconds")
    ap.add_argument("--dt", type=float, default=1.0, help="seconds between readings")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="sample_data/normal.csv")
    args = ap.parse_args()

    df = generate(args.duration, args.dt, args.seed)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")
