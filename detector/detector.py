from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from detector import iforest, rules
from detector.features import compute_features

MODEL_PATH = Path("models/detector.joblib")


class Detector:
    """One entry point: features in, flags out (vehicle_id, ts, method, anomaly, score, anomaly_type)."""

    def __init__(self, baseline, bundle):
        self.baseline = baseline      # typical speed per route (from clean data)
        self.bundle = bundle          # trained Isolation Forest + its threshold

    @classmethod
    def train(cls, normal_features):
        baseline = rules.fit_baseline(normal_features)
        return cls(baseline, iforest.fit(normal_features, baseline))

    def save(self, path=MODEL_PATH):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"baseline": self.baseline, "bundle": self.bundle}, path)

    @classmethod
    def load(cls, path=MODEL_PATH):
        d = joblib.load(path)
        return cls(d["baseline"], d["bundle"])

    def detect(self, features, method="combined"):
        """method: 'rules', 'iforest', or 'combined' (flag if either one flags)."""
        if method == "rules":
            return rules.detect(features, self.baseline)
        if method == "iforest":
            return iforest.detect(features, self.bundle)
        r = rules.detect(features, self.baseline)
        i = iforest.detect(features, self.bundle)
        out = r.copy()
        out["method"] = "combined"
        out["anomaly"] = r.anomaly.values | i.anomaly.values
        out["score"] = np.maximum(r.score.values, i.score.values)
        out["anomaly_type"] = np.where(r.anomaly.values, r.anomaly_type.values, i.anomaly_type.values)
        return out


if __name__ == "__main__":
    # python -m detector.detector   -> trains on clean data and saves models/detector.joblib
    normal = compute_features(pd.read_csv("sample_data/normal.csv", parse_dates=["ts"]))
    det = Detector.train(normal)
    det.save()
    print("Saved", MODEL_PATH, "| IF threshold:", round(det.bundle["threshold"], 4))
