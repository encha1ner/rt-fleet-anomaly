import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# stopped_secs is left out: it is 0 for every clean row, so the forest could never split on it
IF_FEATURES = ["speed_ratio", "accel", "speed_gap", "dist_from_route", "speed_std10"]


def _prepare(features, baseline):
    f = features.copy()
    f["speed_ratio"] = f.speed / f.route_id.map(baseline)    # 1.0 = typical for that route
    return f

def fit(normal_features, baseline, quantile=0.999, n_estimators=200, seed=0,
        features=IF_FEATURES):
    """Train on clean data only. The alarm threshold is a quantile of the clean scores."""
    f = _prepare(normal_features, baseline).dropna(subset=features)
    X = f[features]
    model = IsolationForest(n_estimators=n_estimators, random_state=seed).fit(X)
    scores = -model.score_samples(X)                          # higher = more unusual
    return {"model": model, "baseline": baseline, "features": list(features),
            "threshold": float(np.quantile(scores, quantile)),
            "mean": X.mean(), "std": X.std()}

def _label(z):
    """Guess the fault type from which feature is furthest from normal (in std devs)."""
    cols = list(z.columns)
    vals = z.fillna(0).values
    top = np.abs(vals).argmax(axis=1)
    names = np.array(cols)[top]
    signed = vals[np.arange(len(vals)), top]
    low_speed = z["speed_ratio"].fillna(0).values < 0
    out = np.full(len(z), "unknown", dtype=object)
    out[np.isin(names, ["dist_from_route", "speed_gap"])] = "route_deviation"
    speedish = np.isin(names, ["speed_ratio", "accel"])
    out[speedish] = np.where(signed[speedish] < 0, "sudden_stop", "speed_spike")
    out[names == "speed_std10"] = np.where(low_speed[names == "speed_std10"], "sudden_stop", "speed_spike")
    return out


def detect(features, bundle):
    f = _prepare(features, bundle["baseline"])
    X  = f[bundle["features"]] 
    ok = X.notna().all(axis=1)                                # first rows of each bus have no history yet
    raw = pd.Series(0.0, index=f.index)
    #raw[ok] = -bundle["model"].score_samples(X[ok]) # during live crashes in start  if no historry
    if ok.any():                                              # nothing to score during warm-up
        raw[ok] = -bundle["model"].score_samples(X[ok])
    anomaly = ok & (raw >= bundle["threshold"])
    kind = pd.Series(_label((X - bundle["mean"]) / bundle["std"]), index=f.index).where(anomaly, "none")
    return pd.DataFrame({
        "vehicle_id": f.vehicle_id, "ts": f.ts, "method": "iforest",
        "anomaly": anomaly, "score": (raw / bundle["threshold"]).round(3), "anomaly_type": kind,
    })


def save(bundle, path):
    joblib.dump(bundle, path)


def load(path):
    return joblib.load(path)
