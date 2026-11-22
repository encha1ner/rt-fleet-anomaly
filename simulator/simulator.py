import argparse
import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from simulator.fault_injector import faults_to_df, make_schedule, offset_from_route
from simulator.routes import Route, load_routes

CRUISE_KMH = {"city": (25, 40), "highway": (50, 70)}
FLEET = {"R1": 2, "R2": 2, "R3": 2, "LKO-KNP": 2, "LKO-AYD": 1, "LKO-GKP": 1}


class Vehicle:
    def __init__(self, vehicle_id, route_id, route, rng, cruise_kmh):
        self.id = vehicle_id
        self.route_id = route_id
        self.route = route
        self.rng = rng
        self.cruise = cruise_kmh
        self.speed = cruise_kmh
        self.s = rng.uniform(0, route.length)

    def step(self, dt, fault=None, t=0.0):
        ftype = fault.fault_type if fault else None

        # always draw the noise, so faults never change the random stream
        speed_noise = self.rng.normal(0, 0.8) * math.sqrt(dt)
        gps_lat_m = self.rng.normal(0, 3)
        gps_lon_m = self.rng.normal(0, 3)

        if ftype == "sudden_stop":
            self.speed = max(0.0, self.speed - 15.0 * dt)       # hard braking, km/h per second
        else:
            target, gain = self.cruise, 0.2
            if ftype == "speed_spike":
                target, gain = self.cruise + fault.magnitude, 0.5
            self.speed += gain * (target - self.speed) * dt + speed_noise
            self.speed = float(np.clip(self.speed, 0, 120))
        self.s += self.speed / 3.6 * dt

        lat, lon = self.route.position(self.s)
        if ftype == "route_deviation":
            lat, lon = offset_from_route(self.route, self.s, lat, lon, fault.offset_m(t))

        lat += gps_lat_m / 111_320
        lon += gps_lon_m / (111_320 * math.cos(math.radians(lat)))
        return lat, lon, self.speed


def generate(duration_s=1800, dt=1.0, seed=42, start=None, n_faults=0):
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

    faults = make_schedule([v.id for v in vehicles], duration_s, n_faults, seed) if n_faults else []
    by_vehicle = {}
    for f in faults:
        by_vehicle.setdefault(f.vehicle_id, []).append(f)

    rows = []
    for k in range(int(duration_s / dt)):
        t = k * dt
        ts = start + timedelta(seconds=t)
        for v in vehicles:
            fault = next((f for f in by_vehicle.get(v.id, []) if f.active(t)), None)
            lat, lon, speed = v.step(dt, fault, t)
            rows.append((v.id, v.route_id, ts, round(lat, 6), round(lon, 6), round(speed, 1)))

    df = pd.DataFrame(rows, columns=["vehicle_id", "route_id", "ts", "lat", "lon", "speed"])
    return df, faults_to_df(faults, start)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=1800, help="seconds")
    ap.add_argument("--dt", type=float, default=1.0, help="seconds between readings")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--faults", type=int, default=0, help="number of faults to inject")
    ap.add_argument("--out", default="sample_data/normal.csv")
    ap.add_argument("--log", default=None, help="fault log path (default: <out>_log.csv)")
    args = ap.parse_args()

    df, log = generate(args.duration, args.dt, args.seed, n_faults=args.faults)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")
    if args.faults:
        log_path = args.log or args.out.replace(".csv", "_log.csv")
        log.to_csv(log_path, index=False)
        print(f"Wrote {len(log)} faults to {log_path}")
