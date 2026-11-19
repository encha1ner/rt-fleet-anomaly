import json
import time

import requests

from simulator.routes import ROUTES_FILE, Route

LUCKNOW = (26.8467, 80.9462)

# HARDCODED: city loops. Stops are (lat, lon), approximate; OSRM snaps them to roads.
CITY_LOOPS = {
    "R1": [(26.8315, 80.9230), (26.8450, 80.9200), LUCKNOW],             # Charbagh - Aminabad - Hazratganj
    "R2": [LUCKNOW, (26.8560, 80.9990), (26.8800, 80.9750)],             # Hazratganj - Gomti Nagar - Indira Nagar
    "R3": [(26.8120, 80.9010), (26.8315, 80.9230), (26.8690, 80.9120)],  # Alambagh - Charbagh - Chowk
}

# HARDCODED: intercity destinations. Each becomes a round trip from Lucknow.
DESTINATIONS = {
    "LKO-KNP": (26.4499, 80.3319),   # Kanpur
    "LKO-AYD": (26.7922, 82.1998),   # Ayodhya
    "LKO-GKP": (26.7606, 83.3732),   # Gorakhpur
}


def fetch_loop(stops):
    pts = list(stops) + [stops[0]]                           # close the loop
    coords = ";".join(f"{lon},{lat}" for lat, lon in pts)    # OSRM wants lon,lat
    url = (f"https://router.project-osrm.org/route/v1/driving/{coords}"
           "?overview=full&geometries=geojson")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    geom = resp.json()["routes"][0]["geometry"]["coordinates"]
    return [[lat, lon] for lon, lat in geom]


if __name__ == "__main__":
    plan = {name: ("city", stops) for name, stops in CITY_LOOPS.items()}
    plan.update({name: ("highway", [LUCKNOW, dest]) for name, dest in DESTINATIONS.items()})

    routes = {}
    for name, (kind, stops) in plan.items():
        points = fetch_loop(stops)
        routes[name] = {"kind": kind, "points": points}
        print(f"{name:8s} {kind:8s} {len(points):6d} points  {Route(points).length / 1000:7.1f} km")
        time.sleep(1)   # be polite to the free public server

    ROUTES_FILE.write_text(json.dumps(routes))
    print("Saved", ROUTES_FILE)
