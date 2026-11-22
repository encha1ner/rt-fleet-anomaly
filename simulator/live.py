import argparse
import csv
import itertools
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from common.api import Api
from simulator.fault_injector import FAULT_TYPES, MIN_GAP_S, Fault, draw_params
from simulator.routes import Route, load_routes
from simulator.simulator import CRUISE_KMH, FLEET, Vehicle


def build_vehicles(rng):
    routes = load_routes()
    vehicles, n = [], 0
    for rid, count in FLEET.items():
        info = routes[rid]
        route = Route(info["points"])
        lo, hi = CRUISE_KMH[info["kind"]]
        for _ in range(count):
            n += 1
            vehicles.append(Vehicle(f"bus_{n:02d}", rid, route, rng, rng.uniform(lo, hi)))
    return vehicles


class LiveFaults:
    """Starts random faults while the simulation runs and records them as ground truth."""

    def __init__(self, seed, per_minute, warmup_s, start, log_path):
        self.rng = np.random.default_rng(seed + 1000)
        self.per_minute = per_minute
        self.warmup_s = warmup_s
        self.start = start
        self.active = {}      # vehicle_id -> Fault
        self.free_at = {}     # vehicle_id -> sim time when it may get another fault
        self.log_path = Path(log_path)
        if not self.log_path.exists():
            self.log_path.write_text("vehicle_id,fault_type,start_ts,end_ts,magnitude\n")

    def tick(self, t, vehicle_ids, dt):
        for vid, f in list(self.active.items()):
            if t >= f.end_s:
                del self.active[vid]
                self.free_at[vid] = t + MIN_GAP_S
        if t < self.warmup_s or self.rng.random() >= self.per_minute / 60.0 * dt:
            return
        idle = [v for v in vehicle_ids if v not in self.active and self.free_at.get(v, 0) <= t]
        if not idle:
            return
        vid = str(self.rng.choice(idle))
        ftype = str(self.rng.choice(FAULT_TYPES))
        dur, mag = draw_params(ftype, self.rng)
        f = Fault(vid, ftype, int(t), int(t) + dur, mag)
        self.active[vid] = f
        with self.log_path.open("a", newline="") as fh:
            csv.writer(fh, lineterminator="\n").writerow([
                vid, ftype,
                (self.start + timedelta(seconds=f.start_s)).isoformat(),
                (self.start + timedelta(seconds=f.end_s)).isoformat(),
                round(mag, 1)])
        print(f"[fault] {ftype} on {vid} for {dur}s")


def main():
    ap = argparse.ArgumentParser(description="Live fleet simulator: sends one reading per bus per second.")
    ap.add_argument("--api", default="http://localhost:8000", help="backend base URL")
    ap.add_argument("--no-send", action="store_true", help="print only, do not call the backend")
    ap.add_argument("--speed", type=float, default=1.0, help="2 = run twice as fast as real time")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--fault-rate", type=float, default=2.0, help="new faults per minute (whole fleet)")
    ap.add_argument("--warmup", type=float, default=60.0, help="seconds before the first fault")
    ap.add_argument("--duration", type=float, default=0, help="stop after N simulated seconds (0 = forever)")
    ap.add_argument("--fault-log", default="live_fault_log.csv")
    args = ap.parse_args()

    dt = 1.0
    rng = np.random.default_rng(args.seed)
    vehicles = build_vehicles(rng)
    start = datetime.now(timezone.utc).replace(microsecond=0)
    faults = LiveFaults(args.seed, args.fault_rate, args.warmup, start, args.fault_log)
    api = None if args.no_send else Api(args.api)
    ids = [v.id for v in vehicles]

    print(f"Simulating {len(vehicles)} buses, sending to {'(nowhere)' if api is None else args.api}. Ctrl+C to stop.")
    next_tick = time.monotonic()
    last_ts = start.isoformat()
    try:
        for k in itertools.count():
            t = k * dt
            if args.duration and t >= args.duration:
                break
            ts = (start + timedelta(seconds=t)).isoformat()
            last_ts = ts
            faults.tick(t, ids, dt)

            readings = []
            for v in vehicles:
                lat, lon, speed = v.step(dt, faults.active.get(v.id), t)
                readings.append({"vehicle_id": v.id, "route_id": v.route_id, "ts": ts,
                                 "lat": round(lat, 6), "lon": round(lon, 6), "speed": round(speed, 1)})
            if api is not None:
                api.post("/telemetry", {"readings": readings})
            elif k % 5 == 0:
                print(readings[0])

            if k % 10 == 0:
                sent = "" if api is None else f" | sent ok={api.ok} failed={api.failed}"
                print(f"t={t:5.0f}s | active faults: {len(faults.active)}{sent}")
            next_tick += dt / args.speed
            time.sleep(max(0.0, next_tick - time.monotonic()))
    except KeyboardInterrupt:
        print("\nStopped.")
    Path(args.fault_log + ".end").write_text(last_ts)


if __name__ == "__main__":
    main()
