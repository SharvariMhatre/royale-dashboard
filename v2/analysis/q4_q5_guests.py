"""Q4 tracked player outcomes and concentration; Q5 comp cost and the change point.

Player tables are carded play only. Comp cost is already inside POS cogs: counted once here."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import LED, PD, PP, con, save

PERIODS = {"H1": ("2025-01", "2025-06"), "Q1": ("2025-01", "2025-03"), "Q2": ("2025-04", "2025-06")}


def concentration(c) -> dict:
    out = {}
    for pname, (a, b) in PERIODS.items():
        p = c.sql(f"""SELECT player_id, any_value(opening_tier) tier, any_value(coalesce(age_band,'unknown')) age,
            any_value(home_region) region, sum(tracked_coin_in_usd)::DOUBLE ci, sum(tracked_net_usd)::DOUBLE net,
            sum(theo_usd)::DOUBLE th FROM {PP} WHERE period_month BETWEEN '{a}' AND '{b}' GROUP BY 1""").df()
        groups = {"all": p}
        for dim in ["tier", "age", "region"]:
            for v, g in p.groupby(dim):
                groups[f"{dim}:{v}"] = g
        res = {}
        for k, g in groups.items():
            ci = np.sort(g.ci.values)[::-1]
            loss = np.sort(np.clip(-g.net.values, 0, None))[::-1]
            n = len(g)
            top = lambda arr, q: float(arr[: max(1, int(round(n * q)))].sum() / arr.sum()) if arr.sum() > 0 else None
            res[k] = {"players": n, "ahead_share": float((g.net > 0).mean()), "top1_wager": top(ci, 0.01),
                      "top10_wager": top(ci, 0.10), "top10_losses": top(loss, 0.10), "top1_losses": top(loss, 0.01),
                      "net": float(g.net.sum()), "coin_in": float(g.ci.sum()), "theo": float(g.th.sum())}
        out[pname] = res
    return out


def comps(c) -> dict:
    month = c.sql(f"""SELECT strftime(gaming_date, '%Y-%m') AS month, sum(comp_cost_usd)::DOUBLE AS comp_cost,
        sum(comp_face_value_usd)::DOUBLE AS face, sum(theo_usd)::DOUBLE AS theo FROM {PD} GROUP BY 1 ORDER BY 1""").df()
    month["reinvestment"] = month.comp_cost / month.theo
    # Price of a comp in points: points spent per $1 of face value, by gaming day (06:00 local cut).
    day = c.sql(f"""SELECT CAST(timezone('America/Los_Angeles', event_at_utc::TIMESTAMPTZ) - INTERVAL 6 HOUR AS DATE) AS d,
        -sum(points_delta)::DOUBLE / (sum(face_value_cents) / 100.0) AS pts_per_usd, count(*) AS n,
        sum(economic_cost_cents) / 100.0 AS cost
        FROM {LED} WHERE event_type = 'redeem' AND event_at_utc < TIMESTAMP '2025-07-01 13:00' GROUP BY 1 ORDER BY 1""").df()
    day["d"] = pd.to_datetime(day.d)
    # Change point: the single split of the daily series that most reduces squared error (our own scan).
    y = day.pts_per_usd.values
    best = None
    for i in range(7, len(y) - 7):
        sse = ((y[:i] - y[:i].mean()) ** 2).sum() + ((y[i:] - y[i:].mean()) ** 2).sum()
        if best is None or sse < best[0]:
            best = (sse, i)
    i = best[1]
    before, after = y[:i].mean(), y[i:].mean()
    # When was the change visible in the ledger? (available_at vs event_at)
    lag = c.sql(f"""SELECT median(epoch(available_at_utc - event_at_utc))/3600 AS med_h FROM {LED}""").fetchall()[0][0]
    # Who redeemed more after the change: redemptions per active player per month by tier
    tier = c.sql(f"""SELECT period_month AS month, opening_tier AS tier, sum(comps_redeemed)::DOUBLE / count(*) AS comps_per_pm,
        sum(comp_cost_usd)::DOUBLE / nullif(sum(theo_usd)::DOUBLE, 0) AS reinvest FROM {PP} GROUP BY ALL ORDER BY ALL""").df()
    return {"monthly": month.to_dict("records"), "daily_price": {"d": day.d.dt.strftime("%Y-%m-%d").tolist(),
            "pts_per_usd": day.pts_per_usd.round(3).tolist()}, "change_date": day.d.iloc[i].strftime("%Y-%m-%d"),
            "price_before": float(before), "price_after": float(after), "price_change": float(after / before - 1),
            "ledger_lag_hours": float(lag), "by_tier": tier.to_dict("records"),
            "total_cost": float(month.comp_cost.sum()), "total_face": float(month.face.sum())}


def main() -> None:
    c = con()
    conc = concentration(c)
    save("guests", conc)
    cp = comps(c)
    save("comps", cp)
    a = conc["H1"]["all"]
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in a.items()})
    print(cp["change_date"], round(cp["price_before"], 2), round(cp["price_after"], 2), round(cp["price_change"], 3), cp["total_cost"])
    print([(r["month"], round(r["reinvestment"], 4)) for r in cp["monthly"]])


if __name__ == "__main__":
    main()
