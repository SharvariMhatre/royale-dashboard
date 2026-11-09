"""Q2 demand and the walkway natural experiment (with placebo windows); Q3 downtime.

Walkway W-ENT-B40 (Main Entrance to Back Forty) was closed 2025-03-03 14:00 UTC to 2025-04-07 13:00 UTC,
i.e. gaming dates 2025-03-03 to 2025-04-06."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import CITY, OPS, ROSTER, TRAF, con, save

CLOSE_START, CLOSE_END = pd.Timestamp("2025-03-03"), pd.Timestamp("2025-04-06")


def walkway(c) -> dict:
    d = c.sql("""SELECT gaming_date, zone_id = 'Z-B40' b40, sum(theo) theo, sum(avail_h) h, sum(occ_h) occ
                 FROM floor GROUP BY ALL""").df()
    d["gaming_date"] = pd.to_datetime(d.gaming_date)
    p = d.pivot_table(index="gaming_date", columns="b40", values=["theo", "h", "occ"], aggfunc="sum")
    ratio = (p["theo"][True] / p["h"][True]) / (p["theo"][False] / p["h"][False])  # B40 rate vs rest of floor
    occ_ratio = (p["occ"][True] / p["h"][True]) / (p["occ"][False] / p["h"][False])
    real = (ratio.index >= CLOSE_START) & (ratio.index <= CLOSE_END)
    phases = {"before": ratio[ratio.index < CLOSE_START], "during": ratio[real], "after": ratio[ratio.index > CLOSE_END]}
    pooled = lambda m: float((p["theo"][True][m].sum() / p["h"][True][m].sum()) / (p["theo"][False][m].sum() / p["h"][False][m].sum()))
    phase_ratio = {k: pooled(ratio.index.isin(v.index)) for k, v in phases.items()}
    effect = phase_ratio["during"] - (phase_ratio["before"] + phase_ratio["after"]) / 2
    # Placebo: every 35-day window that does not touch the real closure, compared with the days outside it
    # (real closure days removed from the comparison so they cannot contaminate the baseline).
    L = int((CLOSE_END - CLOSE_START).days) + 1
    placebo = []
    for s in pd.date_range("2025-01-01", ratio.index.max() - pd.Timedelta(days=L - 1)):
        e = s + pd.Timedelta(days=L - 1)
        if e >= CLOSE_START and s <= CLOSE_END:
            continue
        win = (ratio.index >= s) & (ratio.index <= e)
        out = ~win & ~real
        placebo.append(pooled(win) - pooled(out))
    real_eff = pooled(real) - pooled(~real)
    rank = int(sum(x <= real_eff for x in placebo))
    # Door counters into Back Forty, entries per covered hour (offline hours excluded)
    tr = c.sql(f"""SELECT CAST(hour_start_local - INTERVAL 6 HOUR AS DATE) d, zone_id,
        sum(entries_count) FILTER (WHERE counter_status <> 'offline') e, sum(coverage_minutes)/60.0 cov_h
        FROM {TRAF} GROUP BY ALL""").df()
    tr["d"] = pd.to_datetime(tr.d)
    tr["phase"] = np.where(tr.d < CLOSE_START, "before", np.where(tr.d <= CLOSE_END, "during", "after"))
    t = tr.groupby(["zone_id", "phase"])[["e", "cov_h"]].sum()
    t["per_h"] = t.e / t.cov_h
    entries = t.per_h.unstack().round(2).to_dict("index")
    return {"daily_ratio": {"d": [x.strftime("%Y-%m-%d") for x in ratio.index], "r": ratio.round(4).tolist(),
                            "occ": occ_ratio.round(4).tolist()},
            "phase_ratio": phase_ratio, "effect": effect, "real_effect_vs_rest": real_eff,
            "placebo": {"n": len(placebo), "min": float(min(placebo)), "max": float(max(placebo)),
                        "rank_real": rank, "values": [round(x, 4) for x in placebo]},
            "entries_per_hour": entries}


def demand(c) -> dict:
    m = c.sql("""SELECT month, sum(coin_in) ci, sum(theo) th, sum(avail_h) ah, sum(occ_h) oh, count(DISTINCT gaming_date) n_days
                 FROM floor GROUP BY 1 ORDER BY 1""").df()
    m["ci_per_day"] = m.ci / m.n_days
    m["occ"] = m.oh / m.ah
    m["ci_per_occ_h"] = m.ci / m.oh
    # Weekday-adjusted: each month vs the Jan-Apr mean for its own weekday mix
    d = c.sql("SELECT gaming_date, any_value(local_weekday) wd, any_value(month) mo, sum(coin_in) ci FROM floor GROUP BY 1").df()
    base = d[d.mo <= "2025-04"].groupby("wd").ci.mean()
    d["exp"] = d.wd.map(base)
    adj = d.groupby("mo").apply(lambda x: x.ci.sum() / x.exp.sum(), include_groups=False)
    city = c.sql(f"SELECT month, visitor_volume, visitor_yoy_ratio::DOUBLE yoy, hotel_occupancy_ratio::DOUBLE occ FROM {CITY} ORDER BY 1").df()
    zone_month = c.sql("""SELECT month, zone_id, sum(theo)/sum(avail_h) theo_per_h, sum(occ_h)/sum(avail_h) occ FROM floor GROUP BY ALL ORDER BY ALL""").df()
    return {"monthly": m.to_dict("records"), "weekday_adjusted": adj.round(4).to_dict(),
            "city_context": city.to_dict("records"), "zone_month": zone_month.to_dict("records")}


def downtime(c) -> dict:
    # Lost expected win = down hours x that zone's theo per available hour that day (an upper bound:
    # some players simply move to another machine).
    c.execute("""CREATE OR REPLACE TEMP VIEW zd AS SELECT gaming_date, zone_id, sum(theo)/nullif(sum(avail_h),0) rate FROM floor GROUP BY ALL""")
    tot = c.sql("""SELECT sum(sched_h - avail_h) down_h, sum(sched_h) sched_h, sum((sched_h - avail_h) * zd.rate) lost_theo,
                   sum(theo) theo FROM floor JOIN zd USING (gaming_date, zone_id)""").df().iloc[0].to_dict()
    by_month = c.sql("""SELECT month, sum(sched_h - avail_h) down_h, sum((sched_h - avail_h) * zd.rate) lost_theo
                        FROM floor JOIN zd USING (gaming_date, zone_id) GROUP BY 1 ORDER BY 1""").df()
    by_zone = c.sql("""SELECT zone_id, sum(sched_h - avail_h) down_h, 1 - sum(avail_h)/sum(sched_h) down_share,
                       sum((sched_h - avail_h) * zd.rate) lost_theo FROM floor JOIN zd USING (gaming_date, zone_id) GROUP BY 1 ORDER BY 1""").df()
    by_type = c.sql(f"""SELECT event_type, count(*) n, sum(epoch(available_at_utc - opened_at_utc))/3600 AS hrs,
        median(epoch(available_at_utc - opened_at_utc))/3600 median_h FROM {OPS} GROUP BY 1 ORDER BY hrs DESC""").df()
    by_mfr = c.sql("""SELECT manufacturer, 1 - sum(avail_h)/sum(sched_h) down_share, count(DISTINCT machine_id) machines,
                     sum((sched_h - avail_h)) down_h FROM floor GROUP BY 1 ORDER BY 2 DESC""").df()
    # Repair waits by shift: time from failure to a technician starting work, and tech staffing
    shift = c.sql(f"""WITH o AS (SELECT *, hour(opened_at_local) hr FROM {OPS} WHERE event_type='fault_repair')
        SELECT CASE WHEN hr BETWEEN 6 AND 13 THEN 'day' WHEN hr BETWEEN 14 AND 21 THEN 'swing' ELSE 'grave' END shift,
               count(*) n, avg(epoch(available_at_utc - opened_at_utc))/3600 avg_h FROM o GROUP BY 1""").df()
    staff = c.sql(f"""SELECT strftime(gaming_date, '%Y-%m') AS month, sum(planned_headcount) planned, sum(actual_headcount) actual
        FROM {ROSTER} WHERE role='slot_tech' GROUP BY 1 ORDER BY 1""").df()
    return {"total": tot, "by_month": by_month.to_dict("records"), "by_zone": by_zone.to_dict("records"),
            "by_type": by_type.to_dict("records"), "by_manufacturer": by_mfr.to_dict("records"),
            "by_shift": shift.to_dict("records"), "tech_staffing": staff.to_dict("records")}


def main() -> None:
    c = con()
    w = walkway(c)
    save("walkway", w)
    save("demand", demand(c))
    save("downtime", downtime(c))
    print({k: round(v, 3) for k, v in w["phase_ratio"].items()}, "effect", round(w["real_effect_vs_rest"], 3),
          "placebo", w["placebo"]["n"], round(w["placebo"]["min"], 3), "rank", w["placebo"]["rank_real"])
    print(w["entries_per_hour"].get("Z-B40"), w["entries_per_hour"].get("Z-ENT"))


if __name__ == "__main__":
    main()
