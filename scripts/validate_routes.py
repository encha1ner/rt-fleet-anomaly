import json
from simulator.routes import Route, haversine

DEST = {"LKO-KNP": (26.4499, 80.3319),
        "LKO-AYD": (26.7922, 82.1998),
        "LKO-GKP": (26.7606, 83.3732)}
LKO = (26.8467, 80.9462)

routes = json.load(open("simulator/routes.json"))
for name, r in routes.items():
    pts = r["points"]
    lats, lons = zip(*pts)
    closed = haversine(*pts[0], *pts[-1])
    msg = (f"{name:8s} {r['kind']:8s} {Route(pts).length/1000:6.1f} km  "
           f"start-end gap {closed:5.0f} m  "
           f"lat {min(lats):.2f}-{max(lats):.2f}  lon {min(lons):.2f}-{max(lons):.2f}")
    if name in DEST:
        far = max(pts, key=lambda p: haversine(*LKO, *p))      # farthest point from Lucknow
        msg += f"  turnaround {haversine(*far, *DEST[name])/1000:.1f} km from destination"
    print(msg)
