import json
from pathlib import Path

import numpy as np

EARTH_R = 6_371_000.0  # metres
ROUTES_FILE = Path(__file__).parent / "routes.json"


def haversine(lat1, lon1, lat2, lon2):
    """Distance in metres between points (works on numpy arrays too)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_R * np.arcsin(np.sqrt(a))


def load_routes():
    """Returns {name: {"kind": "city" | "highway", "points": [[lat, lon], ...]}}."""
    return json.loads(ROUTES_FILE.read_text())


class Route:
    """A closed polyline: the last point equals the first, so it wraps around."""

    def __init__(self, points):
        pts = []
        for p in points:
            if not pts or tuple(p) != tuple(pts[-1]):   # drop repeated points
                pts.append(tuple(p))
        self.pts = np.array(pts)
        self.seg_len = haversine(self.pts[:-1, 0], self.pts[:-1, 1],
                                 self.pts[1:, 0], self.pts[1:, 1])
        self.cum = np.concatenate([[0.0], np.cumsum(self.seg_len)])
        self.length = float(self.cum[-1])

    def position(self, s):
        """Lat/lon after travelling s metres along the route (wraps around)."""
        s = s % self.length
        i = min(np.searchsorted(self.cum, s, side="right") - 1, len(self.seg_len) - 1)
        frac = (s - self.cum[i]) / self.seg_len[i]
        lat = self.pts[i, 0] + frac * (self.pts[i + 1, 0] - self.pts[i, 0])
        lon = self.pts[i, 1] + frac * (self.pts[i + 1, 1] - self.pts[i, 1])
        return lat, lon
