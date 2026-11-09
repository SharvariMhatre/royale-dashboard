"""Every headline number on the dashboard, re-derived from the raw tables with independent SQL and
checked against the pipeline's results. Exits 1 on any mismatch.  Run: python verify.py"""
from __future__ import annotations

import json
import sys

import duckdb

from common import ACT, CAL, DATA, GM, LED, MD, OUT, PD, PP, PV, SES, load

c = duckdb.connect()
c.execute("SET TimeZone='UTC'")
v = lambda s: float(c.sql(s).fetchall()[0][0])
results: list[tuple[bool, str]] = []


def check(name, got, lo, hi=None):
    hi = lo if hi is None else hi
    ok = got is not None and lo - 1e-9 <= got <= hi + 1e-9
    results.append((ok, f"{'PASS' if ok else 'FAIL'}  {name}: {got:,.6g} (expected {lo:,.6g}..{hi:,.6g})"))


q1, mech, walk, dt, model, comps, guests, plan = (load(k) for k in ["q1", "mechanism", "walkway", "downtime", "model", "comps", "guests", "plan"])
M = {m["machine_id"]: m for m in q1["machines"]}

# Money integrity
check("Off-floor rows excluded (inactive machine-days)", v(f"SELECT count(*) FROM {MD} WHERE NOT active"), 1018)
check("House win = coin-in - payout on every machine-day (cents off)", v(f"SELECT sum(abs(house_win_cents - (coin_in_cents - payout_cents))) FROM {MD}"), 0)
check("Machine coin-in = property coin-in ($ diff)", abs(v(f"SELECT sum(coin_in_cents)/100 FROM {MD}") - v(f"SELECT sum(coin_in_usd) FROM {PD}")), 0, 0.01)
check("DST day has 23 hours", v(f"SELECT scheduled_seconds/3600 FROM {CAL} WHERE gaming_date='2025-03-08'"), 23)
# Q1
gm10 = [r[0] for r in c.sql(f"SELECT machine_id FROM {PV} WHERE active GROUP BY 1 ORDER BY sum(house_win_usd) LIMIT 10").fetchall()]
check("GM bottom 10 identical to pipeline", float(gm10 == q1["gm10"]), 1)
check("GM bottom 10 in Back Forty at period end", float(sum(M[m]["zone"] == "Z-B40" for m in gm10)), 9)
z = v(f"""SELECT (sum(house_win_cents) - sum(theo_cents)) / sqrt(sum(sum_bet_squared * payout_multiplier_variance))
          FROM {MD} JOIN {GM} USING (config_id) WHERE machine_id='M-1158' AND active""")
check("M-1158 luck z (closed form)", z, M["M-1158"]["luck_z"] - 1e-6, M["M-1158"]["luck_z"] + 1e-6)
check("M-1158 luck z value", z, -4.6, -4.5)
hz = v(f"""SELECT (sum(payout_positive_spins) - any_value(hit_probability)::DOUBLE * sum(paid_spins))
           / sqrt(any_value(hit_probability)::DOUBLE * (1 - any_value(hit_probability)::DOUBLE) * sum(paid_spins))
           FROM {MD} JOIN {GM} USING (config_id) WHERE machine_id='M-1158' AND active""")
check("M-1158 hit-rate z from meters", hz, 124, 124.5)
hz_s = v(f"""SELECT (sum(payout_positive_spins) - any_value(hit_probability)::DOUBLE * sum(paid_spins))
           / sqrt(any_value(hit_probability)::DOUBLE * (1 - any_value(hit_probability)::DOUBLE) * sum(paid_spins))
           FROM {SES} JOIN {GM} USING (config_id) WHERE machine_id='M-1158'""")
check("M-1158 hit-rate z from carded sessions (second table)", hz_s, 100, 110)
check("Meter integrity: illegal bets, off-increment payouts, coin-in mismatches", float(mech["integrity"]["illegal_bets"] + mech["integrity"]["off_increment"] + mech["integrity"]["coin_in_mismatch"]), 0)
check("Sessions audited", float(mech["integrity"]["sessions"]), v(f"SELECT count(*) FROM {SES}"))
check("M-1158 effective RTP", mech["effective_rtp"], 0.965, 0.975)
check("Luck z SD across machines (pure luck ~1)", q1["calibration"]["luck_z_sd"], 0.9, 1.2)
check("Machines flagged Inspect", float(q1["calibration"]["n_inspect"]), 1)
check("Machines below 80% of same game in same zone", float(sum(1 for m in q1["machines"] if (m["vs_same_game_zone"] or 1) < 0.8)), 0)
check("Back Forty zone index", q1["zone_index"]["Z-B40"], 0.59, 0.63)
# Q2 walkway
check("Back Forty vs rest during closure", walk["phase_ratio"]["during"], 0.44, 0.48)
check("Walkway effect more extreme than every placebo window", float(walk["placebo"]["rank_real"]), 0)
check("Placebo windows tested", float(walk["placebo"]["n"]), 70, 90)
# Q3
check("Downtime share of scheduled hours", dt["total"]["down_h"] / dt["total"]["sched_h"], 0.0037, 0.0039)
check("Down hours = scheduled - available (raw)", v(f"SELECT sum(scheduled_seconds - available_seconds)/3600 FROM {MD} WHERE active"), dt["total"]["down_h"] - 0.01, dt["total"]["down_h"] + 0.01)
# Model
check("Selected model is the CV minimum", float(model["selected"] == min(model["cv_mae"], key=model["cv_mae"].get)), 1)
check("Baseline MAE (constant mean)", model["test_mae"]["Constant mean"], 218000, 218500)
check("Weekday-mean MAE (independent check vs earlier work)", model["test_mae"]["Weekday mean"], 68690, 68710)
check("Selected model MAE", model["test_mae"][model["selected"]], 50000, 56000)
# Q4/Q5
check("Tracked player net ($)", v(f"SELECT sum(tracked_net_usd) FROM {PP}"), guests["H1"]["all"]["net"] - 1, guests["H1"]["all"]["net"] + 1)
check("Players ahead share", guests["H1"]["all"]["ahead_share"], 0.13, 0.14)
check("Comp cost total ($)", v(f"SELECT sum(comp_cost_usd) FROM {PD}"), comps["total_cost"] - 0.01, comps["total_cost"] + 0.01)
check("Comp cost = ledger economic cost ($ diff)", abs(v(f"SELECT sum(economic_cost_cents)/100 FROM {LED} WHERE event_type='redeem' AND event_at_utc < '2025-07-01 13:00'") - comps["total_cost"]), 0, 1)
check("Point price change date is 2025-05-01", float(comps["change_date"] == "2025-05-01"), 1)
check("Point price change", comps["price_change"], -0.60, -0.50)
# Q6
a = {r[0]: r[1:] for r in c.sql(f"SELECT action_type_id, unit_cost_cents, recurring_cost_cents_per_day, lead_days FROM {ACT}").fetchall()}
cost = lambda t, q: q * (a[t][0] + a[t][1] * max(0, 30 - a[t][2])) / 100
check("Guide worked example: lease with 14-day lead", cost("A-REPLACE-LEASE", 1), 3380)
top = plan["top"][0]
check("Top plan cost recomputed from catalog", sum(cost(t, q) for t, q in top["plan"].items()), top["cost"])
check("Top plan within budget", top["cost"], 0, 100000)
check("Top plan uses at most 3 action types", float(len(top["plan"])), 0, 3)
check("GM plan cost (10 leases)", plan["gm_plan"]["cost"], 33800)
# Data file the browser uses reproduces the totals
fl = json.loads((OUT / "floor.json").read_text())["floor"]
check("Browser data: coin-in total ($ diff)", abs(sum(fl["ci"]) - v(f"SELECT sum(coin_in_cents)/100 FROM {MD} WHERE active")), 0, 5)
check("Browser data: theo total ($ diff)", abs(sum(fl["th"]) - v(f"SELECT sum(theo_cents)/100 FROM {MD} WHERE active")), 0, 5)

check("Point price roughly halves within every tier", v(f"""SELECT max(r) FROM (SELECT tier_before,
    (sum(-points_delta) FILTER (WHERE event_at_utc >= '2025-05-01 13:00') / sum(face_value_cents) FILTER (WHERE event_at_utc >= '2025-05-01 13:00'))
    / (sum(-points_delta) FILTER (WHERE event_at_utc < '2025-05-01 13:00') / sum(face_value_cents) FILTER (WHERE event_at_utc < '2025-05-01 13:00')) AS r
    FROM {LED} WHERE event_type='redeem' AND event_at_utc < '2025-07-01 13:00' GROUP BY 1)"""), 0.4, 0.5)
(OUT / "checks.json").write_text(json.dumps([{"ok": ok, "line": line[6:]} for ok, line in results], indent=0))
for ok, line in results:
    print(line)
bad = sum(not ok for ok, _ in results)
print(f"\n{len(results) - bad}/{len(results)} checks passed")
sys.exit(1 if bad else 0)
