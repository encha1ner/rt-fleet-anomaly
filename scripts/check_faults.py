import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("sample_data/test_faulty.csv", parse_dates=["ts"])
log = pd.read_csv("sample_data/test_faulty_log.csv", parse_dates=["start_ts", "end_ts"])
print(log)

fig, axes = plt.subplots(3, 1, figsize=(10, 10))
for ax, ftype in zip(axes[:2], ["sudden_stop", "speed_spike"]):
    f = log[log.fault_type == ftype].iloc[0]
    b = df[df.vehicle_id == f.vehicle_id]
    ax.plot(b.ts, b.speed)
    ax.axvspan(f.start_ts, f.end_ts, color="red", alpha=0.2)
    ax.set_title(f"{f.vehicle_id}: {ftype}")

f = log[log.fault_type == "route_deviation"].iloc[0]       # speed stays normal here, so plot the path
b = df[df.vehicle_id == f.vehicle_id]
w = b[(b.ts >= f.start_ts) & (b.ts < f.end_ts)]
axes[2].plot(b.lon, b.lat, lw=1)
axes[2].plot(w.lon, w.lat, "r", lw=2)
axes[2].set_title(f"{f.vehicle_id}: route_deviation (red = fault window)")
plt.tight_layout()
plt.savefig("check_faults.png", dpi=120)
