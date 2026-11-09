"""Q6: score every legal $100,000 plan for July 1-30, 2025, with Monte Carlo uncertainty,
and simulate the GM's own plan (lease replacements for the bottom 10) beside it.

Each action's benefit is drawn from a range grounded in this data; every assumption is named in ASSUMPTIONS
and shown on the dashboard. Benefits are expected house win (theo), never realized luck."""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from common import ACT, EVT, LOC, con, load, save

BUDGET, WINDOW, DRAWS = 100_000, 30, 4000
rng = np.random.default_rng(7)


def catalog(c) -> pd.DataFrame:
    a = c.sql(f"SELECT * FROM {ACT}").df().set_index("action_type_id")
    a["cost1"] = (a.unit_cost_cents + a.recurring_cost_cents_per_day * np.maximum(0, WINDOW - a.lead_days)) / 100
    return a


def facts(c) -> dict:
    q = lambda s: c.sql(s).fetchall()[0][0]
    f = {}
    f["june"] = c.sql("""SELECT zone_id, sum(theo)/count(DISTINCT gaming_date) AS theo_day, sum(theo)/sum(avail_h) AS rate,
                         sum(avail_h)/count(DISTINCT gaming_date)/count(DISTINCT machine_id) AS h_per_machine_day
                         FROM floor WHERE month='2025-06' GROUP BY 1""").df().set_index("zone_id")
    f["floor_hold_theo"] = q("SELECT sum(theo)/sum(coin_in) FROM floor")
    mech = load("mechanism")
    f["m1158_per_day"] = mech["shortfall_per_day"]
    dt = load("downtime")
    f["lost_theo_per_day"] = dt["total"]["lost_theo"] / 181
    rid = [r for r in dt["by_manufacturer"] if r["manufacturer"] == "Ridgeline"][0]
    f["ridgeline_lost_per_day"] = f["lost_theo_per_day"] * rid["down_h"] / dt["total"]["down_h"]
    # Promotion lift from this property's own promotions: event days vs the same weekdays in the 4 weeks around them
    ev = c.sql(f"SELECT name, start_date, end_date FROM {EVT} WHERE event_type='property_promotion'").df()
    d = c.sql("SELECT gaming_date, any_value(local_weekday) AS wd, sum(coin_in) AS ci FROM floor GROUP BY 1").df()
    d["gaming_date"] = pd.to_datetime(d.gaming_date)
    lifts = []
    for _, e in ev.iterrows():
        s, t = pd.Timestamp(e.start_date), pd.Timestamp(e.end_date)
        on = d[(d.gaming_date >= s) & (d.gaming_date <= t)]
        around = d[(d.gaming_date >= s - pd.Timedelta(days=28)) & (d.gaming_date <= t + pd.Timedelta(days=28)) & ~d.index.isin(on.index)]
        base = on.wd.map(around.groupby("wd").ci.mean())
        lifts.append({"name": e["name"], "days": len(on), "extra_coin_in": float((on.ci - base).sum()),
                      "extra_theo": float((on.ci - base).sum() * f["floor_hold_theo"]), "pct": float(on.ci.sum() / base.sum() - 1)})
    f["promos"] = lifts
    # Placebo: the same estimator on 3-day windows with no event, to measure how noisy a "lift" is by chance.
    evdays = set()
    for _, e in c.sql(f"SELECT start_date, end_date FROM {EVT}").df().iterrows():
        evdays |= set(pd.date_range(e.start_date, e.end_date))
    plac = []
    for s0 in pd.date_range("2025-01-29", "2025-06-01"):
        w = pd.date_range(s0, periods=3)
        if evdays & set(w):
            continue
        on = d[d.gaming_date.isin(w)]
        around = d[(d.gaming_date >= s0 - pd.Timedelta(days=28)) & (d.gaming_date <= w[-1] + pd.Timedelta(days=28)) & ~d.gaming_date.isin(w)]
        plac.append(float((on.ci - on.wd.map(around.groupby("wd").ci.mean())).sum() / 3 * f["floor_hold_theo"]))
    f["promo_lift_per_day"] = float(np.mean([p["extra_theo"] / p["days"] for p in lifts]))
    f["promo_noise_per_day"] = float(np.std(plac))
    f["promo_placebo"] = {"n": len(plac), "sd": float(np.std(plac)), "values": [round(x) for x in plac],
                          "rank_of_each": {p["name"]: int(sum(x >= p["extra_theo"] / p["days"] for x in plac)) for p in lifts}}
    ss = load("experiments")["same_slot"]
    f["same_slot_gain_per_h"] = ss[1]["theo_per_h"] - ss[0]["theo_per_h"]
    return f


def samplers(f: dict) -> dict:
    """Benefit over the 30-day window for ONE unit, as DRAWS samples. Lead time removes days."""
    j = f["june"]
    b40_day = j.theo_day["Z-B40"]
    dest_rate = (j.rate["Z-PIT"] * 2 + j.rate["Z-HTL"]) / 3  # the 3 free slots in busier zones (2 Pit, 1 Hotel)
    hpm = j.h_per_machine_day["Z-B40"]
    S = {
        # Inspection fixes the paytable with probability 0.5-0.9; recovers M-1158's shortfall for the days left.
        "A-INSPECT": lambda: (rng.random(DRAWS) < rng.uniform(0.5, 0.9, DRAWS)) * f["m1158_per_day"] * (WINDOW - 1),
        # Signs lift Back Forty entries 0-10%; the closure showed play tracks entries about 1:1.
        "A-WAYFINDING": lambda: rng.uniform(0.0, 0.10, DRAWS) * b40_day * (WINDOW - 10),
        # Moving a Back Forty machine into a free busy slot earns the destination rate, but 30-80% of that is play
        # taken from neighbours (displacement), so only the rest is new.
        "A-MOVE-MACHINE": lambda: (dest_rate - j.rate["Z-B40"]) * hpm * (WINDOW - 2) * rng.uniform(0.2, 0.7, DRAWS),
        # A 3-day promotion weekend: per-day theo lift drawn around this property's own past promotions, with the
        # spread of the same estimator on placebo (non-event) windows, then scaled 50-100% for summer softness.
        "A-PROMO": lambda: rng.normal(f["promo_lift_per_day"], f["promo_noise_per_day"], DRAWS) * 3 * rng.uniform(0.5, 1.0, DRAWS),
        # One more technician cuts 10-30% of downtime's lost theo (an upper bound itself).
        "A-TECH-SHIFT": lambda: f["lost_theo_per_day"] * rng.uniform(0.10, 0.30, DRAWS) * (WINDOW - 7),
        # A Ridgeline sweep halves 0-50% of Ridgeline's excess downtime.
        "A-PREVENTIVE": lambda: f["ridgeline_lost_per_day"] * rng.uniform(0.0, 0.5, DRAWS) * (WINDOW - 7),
        # Same slot, new lease: the one real swap (M-1120 to M-5076) changed theo/h by about +$0.39; allow -100%..+300% of that.
        "A-REPLACE-LEASE": lambda: f["same_slot_gain_per_h"] * rng.uniform(-1, 3, DRAWS) * hpm * (WINDOW - 14),
        "A-REPLACE-BUY": lambda: f["same_slot_gain_per_h"] * rng.uniform(-1, 3, DRAWS) * hpm * (WINDOW - 21),
        # Information actions: no direct July win; valued at zero here and argued on the dashboard instead.
        "A-COMP-PILOT": lambda: np.zeros(DRAWS),
        "A-COMP-CHANGE": lambda: np.zeros(DRAWS),
        "A-SURVEY": lambda: np.zeros(DRAWS),
        "A-MOVE-BANK": lambda: (dest_rate - j.rate["Z-B40"]) * hpm * 7 * (WINDOW - 5) * rng.uniform(0.2, 0.7, DRAWS),
    }
    return S


QTY = {"A-INSPECT": [1], "A-WAYFINDING": [1], "A-MOVE-MACHINE": [1, 2, 3], "A-PROMO": [1, 2], "A-TECH-SHIFT": [1, 2, 3],
       "A-PREVENTIVE": [1], "A-REPLACE-LEASE": [5, 10], "A-REPLACE-BUY": [5, 10], "A-COMP-PILOT": [1],
       "A-COMP-CHANGE": [1], "A-SURVEY": [1], "A-MOVE-BANK": [1]}
ASSUMPTIONS = {
    "A-INSPECT": "Only M-1158 has a payout signal; 50-90% chance the inspection finds and fixes the paytable; recovers its $/day shortfall",
    "A-WAYFINDING": "Back Forty only: signs lift entries 0-10%; play tracks entries ~1:1 (walkway closure)",
    "A-MOVE-MACHINE": "Only 3 free slots in busier zones (2 Pit, 1 Hotel); 30-80% of the gain is displaced play",
    "A-PROMO": "3-day weekend; per-day lift from this property's two past promotions, noise from placebo windows, 50-100% for summer",
    "A-TECH-SHIFT": "Cuts 10-30% of downtime's lost theo (itself an upper bound)",
    "A-PREVENTIVE": "Ridgeline sweep cuts 0-50% of Ridgeline downtime",
    "A-REPLACE-LEASE": "Same slot, new title: the only real swap moved theo/h by +$0.39",
    "A-REPLACE-BUY": "As lease, with a longer lead time",
    "A-COMP-PILOT": "Information only in July (decides whether to keep the May 1 point price)",
    "A-COMP-CHANGE": "Information only; cannot run with the pilot",
    "A-SURVEY": "Information only",
    "A-MOVE-BANK": "Not feasible: no zone has 7 free slots, so it is excluded from the search",
}


def main() -> None:
    c = con()
    a = catalog(c)
    f = facts(c)
    S = samplers(f)
    draws = {k: S[k]() for k in QTY}
    types = [t for t in QTY if t != "A-MOVE-BANK"]  # infeasible: no zone has 7 free slots
    rows = []
    for k in range(0, 4):
        for combo in itertools.combinations(types, k):
            if {"A-COMP-PILOT", "A-COMP-CHANGE"} <= set(combo):
                continue
            for qs in itertools.product(*[QTY[t] for t in combo]):
                q = {t: n for t, n in zip(combo, qs) if n <= a.quantity_limit[t]}
                if len(q) != len(combo):
                    continue
                cost = sum(n * a.cost1[t] for t, n in q.items())
                if cost > BUDGET:
                    continue
                # Moves and replacements can't target the same machines: at most 10 Back Forty machines in total
                if q.get("A-MOVE-MACHINE", 0) + q.get("A-REPLACE-LEASE", 0) + q.get("A-REPLACE-BUY", 0) > 10:
                    continue
                ben = sum(n * draws[t] for t, n in q.items()) if q else np.zeros(DRAWS)
                net = ben - cost
                rows.append({"plan": q, "cost": round(cost, 2), "keep": round(BUDGET - cost, 2),
                             "exp_benefit": float(ben.mean()), "exp_net": float(net.mean()),
                             "p_gain": float((net > 0).mean()), "p05": float(np.quantile(net, 0.05)), "p95": float(np.quantile(net, 0.95))})
    df = pd.DataFrame(rows).sort_values("exp_net", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    gm = {"A-REPLACE-LEASE": 10}
    gm_ben = 10 * draws["A-REPLACE-LEASE"]
    gm_cost = 10 * a.cost1["A-REPLACE-LEASE"]
    gm_res = {"plan": gm, "cost": gm_cost, "exp_net": float((gm_ben - gm_cost).mean()), "p_gain": float((gm_ben - gm_cost > 0).mean()),
              "p05": float(np.quantile(gm_ben - gm_cost, 0.05)), "p95": float(np.quantile(gm_ben - gm_cost, 0.95)),
              "rank": int((df.exp_net > (gm_ben - gm_cost).mean()).sum() + 1)}
    per_action = {t: {"cost1": float(a.cost1[t]), "lead_days": int(a.lead_days[t]), "limit": int(a.quantity_limit[t]),
                      "exp_benefit1": float(draws[t].mean()), "p05": float(np.quantile(draws[t], .05)),
                      "p95": float(np.quantile(draws[t], .95)), "assumption": ASSUMPTIONS[t]} for t in QTY}
    save("plan", {"n_plans": len(df), "top": df.head(25).to_dict("records"), "gm_plan": gm_res, "per_action": per_action,
                  "facts": {k: v for k, v in f.items() if k != "june"} | {"june_zone": f["june"].reset_index().to_dict("records")},
                  "all": df[["cost", "exp_net", "p_gain"]].round(2).to_dict("list")})
    print(len(df), "legal plans")
    print(df.head(8)[["plan", "cost", "exp_net", "p_gain", "p05"]].to_string())
    print("GM", gm_res)
    print({t: round(v["exp_benefit1"]) for t, v in per_action.items()})
    print(f["promos"])


if __name__ == "__main__":
    main()
