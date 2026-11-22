import numpy as np
import pandas as pd

from simulator.routes import Route, haversine, load_routes

M_PER_DEG = 111_320.0
W = 5                      # window (readings) for implied speed and heading
STOP_KMH = 2.0             # below this counts as "stopped"

FEATURES = ["speed", "accel", "step_dist", "speed_gap", "heading_change",
            "dist_from_route", "stopped_secs", "speed_std10"]


def dist_to_route(lat, lon, route, chunk=200):
    """Distance in metres from each point to the nearest part of ONE route."""
    o_lat, o_lon = route.pts[0]
    k = np.cos(np.radians(o_lat))

    def xy(la, lo):
        return np.column_stack([(lo - o_lon) * k * M_PER_DEG, (la - o_lat) * M_PER_DEG])

    A = xy(route.pts[:-1, 0], route.pts[:-1, 1])
    B = xy(route.pts[1:, 0], route.pts[1:, 1])
    d = B - A
    ab2 = np.maximum((d ** 2).sum(axis=1), 1e-9)
    P = xy(np.asarray(lat), np.asarray(lon))

    out = np.empty(len(P))
    for i in range(0, len(P), chunk):            # chunked to keep memory small on long routes
        p = P[i:i + chunk, None, :]
        t = np.clip(((p - A[None]) * d[None]).sum(-1) / ab2[None], 0, 1)
        closest = A[None] + t[..., None] * d[None]
        out[i:i + chunk] = np.sqrt(((p - closest) ** 2).sum(-1)).min(axis=1)
    return out


def bearing(lat1, lon1, lat2, lon2):
    """Compass direction (degrees) from point 1 to point 2."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1)
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return np.degrees(np.arctan2(y, x))


def _vehicle_features(g, route):
    g = g.sort_values("ts").copy()
    lat, lon = g.lat.values, g.lon.values
    dt = g.ts.diff().dt.total_seconds()

    g["accel"] = g.speed.diff() / dt                                   # km/h per second
    g["step_dist"] = haversine(g.lat.shift().values, g.lon.shift().values, lat, lon)   # metres

    # speed implied by GPS movement over W readings, compared with the reported speed
    dW = haversine(g.lat.shift(W).values, g.lon.shift(W).values, lat, lon)
    dtW = g.ts.diff(W).dt.total_seconds()
    g["implied_speed"] = dW / dtW * 3.6
    g["speed_gap"] = g.implied_speed - g.speed.rolling(W).mean()

    # heading change over W readings (wrapped to 0..180 degrees)
    b = bearing(g.lat.shift(W).values, g.lon.shift(W).values, lat, lon)
    db = pd.Series(b, index=g.index).diff(W)
    g["heading_change"] = ((db + 180) % 360 - 180).abs()

    g["dist_from_route"] = dist_to_route(lat, lon, route)

    stop = g.speed < STOP_KMH
    run_id = (stop != stop.shift()).cumsum()
    g["stopped_secs"] = np.where(stop, g.groupby(run_id).cumcount() + 1, 0)

    g["speed_std10"] = g.speed.rolling(10).std()
    return g


def compute_features(df, routes=None, route_objs=None):
    """
    Input: raw telemetry (vehicle_id, route_id, ts, lat, lon, speed). Output: same rows plus features.
    route_objs: optional dict {route_id: Route} that is reused between calls (used by the live detector).
    """
    cache = {} if route_objs is None else route_objs
    parts = []
    for vid, g in df.groupby("vehicle_id"):
        rid = g.route_id.iloc[0]
        if rid not in cache:
            routes = routes or load_routes()
            cache[rid] = Route(routes[rid]["points"])
        parts.append(_vehicle_features(g, cache[rid]))
    return pd.concat(parts).sort_values(["ts", "vehicle_id"]).reset_index(drop=True)
