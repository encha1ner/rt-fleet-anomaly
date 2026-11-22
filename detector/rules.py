import pandas as pd

# A rule fires when its ratio (value / threshold) reaches 1.0
THRESHOLDS = {
    "sudden_stop": 10.0,       # seconds below 2 km/h in a row
    "speed_spike": 1.4,        # speed divided by the route's normal median speed
    "route_deviation": 50.0,   # metres from the bus's own route
}


def fit_baseline(normal_features):
    """Typical speed per route, learned from clean data only."""
    return normal_features.groupby("route_id").speed.median().to_dict()


def detect(features, baseline, thresholds=THRESHOLDS):
    """Returns one row per reading: anomaly flag, type and score (the largest rule ratio)."""
    f = features
    ratios = pd.DataFrame({
        "sudden_stop": f.stopped_secs.fillna(0) / thresholds["sudden_stop"],
        "speed_spike": (f.speed / f.route_id.map(baseline)).fillna(0) / thresholds["speed_spike"],
        "route_deviation": f.dist_from_route.fillna(0) / thresholds["route_deviation"],
    })
    score = ratios.max(axis=1)
    anomaly = score >= 1.0
    return pd.DataFrame({
        "vehicle_id": f.vehicle_id,
        "ts": f.ts,
        "method": "rule",
        "anomaly": anomaly,
        "score": score.round(3),
        "anomaly_type": ratios.idxmax(axis=1).where(anomaly, "none"),
    })
