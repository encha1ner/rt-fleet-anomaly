import numpy as np
import pandas as pd


def evaluate(flags, log, grace_s=10):
    """
    flags: DataFrame with vehicle_id, ts, anomaly (bool), anomaly_type
    log:   injection log (vehicle_id, fault_type, start_ts, end_ts)
    Rows within grace_s after a fault ends are ignored when counting false alarms,
    because windowed features keep reacting for a few seconds.
    """
    flags = flags.reset_index(drop=True)
    ts = flags.ts
    truth = np.zeros(len(flags), bool)
    grace = np.zeros(len(flags), bool)
    pred = flags.anomaly.values.astype(bool)
    events = []

    for r in log.itertuples():
        veh = (flags.vehicle_id == r.vehicle_id).values
        in_win = veh & (ts >= r.start_ts).values & (ts < r.end_ts).values
        end_g = r.end_ts + pd.Timedelta(seconds=grace_s)
        in_grace = veh & (ts >= r.end_ts).values & (ts < end_g).values
        truth |= in_win
        grace |= in_grace

        hit = flags[(in_win | in_grace) & pred]
        events.append({
            "vehicle_id": r.vehicle_id,
            "fault_type": r.fault_type,
            "detected": len(hit) > 0,
            "delay_s": (hit.ts.min() - r.start_ts).total_seconds() if len(hit) else np.nan,
            "type_ok": bool((hit.anomaly_type == r.fault_type).any()) if len(hit) else False,
        })

    tp = int((pred & truth).sum())
    fp = int((pred & ~truth & ~grace).sum())
    fn = int((~pred & truth).sum())
    ev = pd.DataFrame(events)
    summary = {
        "row_precision": round(tp / (tp + fp), 3) if tp + fp else float("nan"),
        "row_recall": round(tp / (tp + fn), 3) if tp + fn else float("nan"),
        "events_detected": f"{int(ev.detected.sum())}/{len(ev)}",
        "type_correct": f"{int(ev.type_ok.sum())}/{len(ev)}",
        "median_delay_s": float(ev.delay_s.median()),
        "false_alarm_rows": fp,
    }
    flags["false_alarm"] = pred & ~truth & ~grace
    return ev, summary, flags
