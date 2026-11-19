import json
import pandas as pd
import matplotlib.pyplot as plt

routes = json.load(open("simulator/routes.json"))
df = pd.read_csv("sample_data/normal.csv", parse_dates=["ts"])

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(80.85, 81.05)
ax.set_ylim(26.78, 26.92)
for name, r in routes.items():
    lat, lon = zip(*r["points"])
    ax.plot(lon, lat, lw=1, label=name)
ax.scatter(df.groupby("vehicle_id").lon.last(), df.groupby("vehicle_id").lat.last(),
           c="k", s=25, zorder=3)          # last position of each bus
ax.legend(); plt.savefig("check.png", dpi=150)

print(df.groupby("route_id").speed.describe())
