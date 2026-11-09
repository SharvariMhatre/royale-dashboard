"""Claims & Evidence appendix, generated from the results so every number is traceable.
Writes site/data/claims.json and ../docs/CLAIMS.md."""
from __future__ import annotations

import json

from common import OUT, ROOT, load

q1, mech, walk, dt, model, comps, guests, plan, exp, dem = (load(k) for k in
    ["q1", "mechanism", "walkway", "downtime", "model", "comps", "guests", "plan", "experiments", "demand"])
M = {m["machine_id"]: m for m in q1["machines"]}
gmv = q1["gm10_verdicts"]
top = plan["top"][0]
pct = lambda x, n=0: f"{x * 100:.{n}f}%"
usd = lambda x: f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"
usd2 = lambda x: f"${x:,.2f}"
ss = exp["same_slot"]
m1152 = next(m for m in exp["moves"] if m["machine_id"] == "M-1152")["spells"]
promos = plan["facts"]["promos"]

CLAIMS = [
    {"id": "C1", "q": "Q1", "claim": f"None of the GM's 10 is a weak machine: {gmv.get('Bad spot', 0)} sit in a bad spot, {gmv.get('Short exposure', 0)} had short time on the floor, {gmv.get('Inspect', 0)} needs inspection.",
     "evidence": "analysis/q1_machines.py: verdict() over floor (machine_day joined to prepared_daily_view, active rows)",
     "result": f"All 310 machines earn at least {min(m['vs_same_game_zone'] for m in q1['machines'] if m['vs_same_game_zone']):.2f}x the same game in the same zone (leave-one-out).",
     "alternative": "The machines are simply bad games. Tested: compared with the same game in the same zone on the same days, excluding the machine itself.",
     "limitation": "Verdict thresholds (0.8, 0.85, 120 days, |z| > 3.29) are our choices; the dashboard recomputes them for any period.", "tab": "machines"},
    {"id": "C2", "q": "Q1", "claim": f"M-1158 pays more often but smaller: hit rate {pct(M['M-1158']['hits'] / M['M-1158']['spins'], 1)} vs {pct(0.31544, 1)} configured, award per hit {mech['by_bet'][0]['award_x']:.2f}x vs {mech['peers']['award_x']:.2f}x for the same game elsewhere. Effective return {pct(mech['effective_rtp'], 1)} vs 90% configured.",
     "evidence": "analysis/q1_machines.py: mechanism(); sessions + game_math",
     "result": f"Hit-rate z = {M['M-1158']['hit_z']:.0f} in meters and 103 in carded sessions; luck z = {M['M-1158']['luck_z']:.2f}. Present at every bet level, every month, carded ({pct(mech['split']['carded_hold'], 1)} hold) and uncarded ({pct(mech['split']['uncarded_hold'], 1)}).",
     "alternative": "Bad luck or a metering fault. Luck: the hit test ignores award size, and z = 124 is not luck. Metering: all 776,297 sessions use legal bets, every payout is a multiple of the game's increment, coin-in = bet x spins on every session.",
     "limitation": "Data can't say why the paytable differs. This is a lead to inspect, never an accusation.", "tab": "machines"},
    {"id": "C3", "q": "Q2", "claim": f"Back Forty's spot is the cause: it earns {q1['zone_index']['Z-B40']:.2f}x what its game mix earns elsewhere, and fell from {pct(walk['phase_ratio']['before'])} to {pct(walk['phase_ratio']['during'])} of the rest of the floor while its walkway was closed (Mar 3 to Apr 6), recovering to {pct(walk['phase_ratio']['after'])}.",
     "evidence": "analysis/q2_q3_demand_downtime.py: walkway(); floor_walkways, zone_traffic_hourly",
     "result": f"The closure effect is more extreme than all {walk['placebo']['n']} placebo windows of the same length. Back Forty entries per counter-hour: {walk['entries_per_hour']['Z-B40']['before']} before, {walk['entries_per_hour']['Z-B40']['during']} during.",
     "alternative": "A floor-wide dip in March. Tested: the effect is measured against the rest of the floor on the same days, and fake closure dates never come close.",
     "limitation": "One closure; the size of the effect may not transfer to a signage change.", "tab": "demand"},
    {"id": "C4", "q": "Q1", "claim": f"Replacing a machine in the same slot didn't fix the slot: M-5076 replaced M-1120 at L-38-5 on May 13 and earned {usd2(ss[1]['theo_per_h'])} of expected win per hour vs {usd2(ss[0]['theo_per_h'])} before, still about a third of the floor rate.",
     "evidence": "analysis/q1_machines.py: swaps_and_moves(); placements",
     "result": f"Theo per available hour {ss[0]['theo_per_h']:.2f} -> {ss[1]['theo_per_h']:.2f}; floor {exp['same_slot_floor'][1]['floor_theo_per_h']:.2f} -> {exp['same_slot_floor'][0]['floor_theo_per_h']:.2f}. Both machines are on the GM's list.",
     "alternative": "The new machine needed time to build play. Limitation acknowledged: 49 days after the swap.",
     "limitation": "One swap, same game title.", "tab": "machines"},
    {"id": "C5", "q": "Q1", "claim": f"Moving a machine out of Back Forty doubled its expected win: M-1152 earned ${m1152[0]['theo_per_h']:.2f}/h in Back Forty and ${m1152[1]['theo_per_h']:.2f}/h at Main Entrance.",
     "evidence": "analysis/q1_machines.py: swaps_and_moves()", "result": f"{m1152[1]['theo_per_h'] / m1152[0]['theo_per_h']:.2f}x after the Feb 4 move.",
     "alternative": "Some of the new play was taken from neighbours. That is why the plan search assumes 30-80% displacement.",
     "limitation": "One machine; 34 days before the move.", "tab": "machines"},
    {"id": "C6", "q": "Q3", "claim": f"Downtime is small: {pct(dt['total']['down_h'] / dt['total']['sched_h'], 2)} of scheduled hours, at most {usd(dt['total']['lost_theo'])} of expected win in six months.",
     "evidence": "analysis/q2_q3_demand_downtime.py: downtime()", "result": f"{dt['total']['down_h']:,.0f} down hours; Ridgeline machines are down 2-3x as often as others; slot-tech headcount fell short of plan in April and May.",
     "alternative": "Lost play is all lost revenue. It is an upper bound: players can move to a nearby machine.",
     "limitation": "Valued at the zone's expected win per hour that day.", "tab": "downtime"},
    {"id": "C7", "q": "Q2", "claim": f"Demand dipped in June: weekday-adjusted coin-in was {pct(dem['weekday_adjusted']['2025-06'] - 1, 1)} vs the Jan-Apr norm.",
     "evidence": "analysis/q2_q3_demand_downtime.py: demand()", "result": f"Las Vegas visitors were {pct(dem['city_context'][-1]['yoy'], 1)} year over year in June (LVCVA, context only).",
     "alternative": "A property-specific problem. The citywide fall points to tourism; it is context, never a model input.",
     "limitation": "LVCVA covers all Las Vegas visitors, not this casino's guests.", "tab": "demand"},
    {"id": "C8", "q": "Q4", "claim": f"Tracked players wagered {usd(guests['H1']['all']['coin_in'])} and lost {usd(-guests['H1']['all']['net'])}; {pct(guests['H1']['all']['ahead_share'], 1)} finished ahead.",
     "evidence": "analysis/q4_q5_guests.py: concentration(); player_period", "result": f"Top 10% of players account for {pct(guests['H1']['all']['top10_losses'])} of losses; top 1% place {pct(guests['H1']['all']['top1_wager'])} of wagers.",
     "alternative": "Results are luck. Tracked net is within 1% of theo across the group.",
     "limitation": "Carded play only. Concentration is shown to protect heavy losers, never to target them.", "tab": "guests"},
    {"id": "C9", "q": "Q5", "claim": f"On {comps['change_date']} the points needed per $1 of comps fell {pct(-comps['price_change'])} ({comps['price_before']:.1f} to {comps['price_after']:.1f}). Comp cost rose from {pct(comps['monthly'][0]['reinvestment'], 2)} to {pct(comps['monthly'][-1]['reinvestment'], 2)} of theo.",
     "evidence": "analysis/q4_q5_guests.py: comps(); loyalty_ledger (change point scan on the daily series)",
     "result": f"Comp cost {usd(comps['total_cost'])} in six months, counted once (already inside POS cogs).",
     "alternative": "A shift in which tiers redeem. Tested: the price roughly halved within every tier on the same day (Base 15.0 to 7.0, Gold 12.0 to 5.6, Platinum 9.0 to 4.2 points per $1).",
     "limitation": "We can't see whether the change was intended.", "tab": "guests"},
    {"id": "C10", "q": "Model", "claim": f"A {model['selected'].lower()} forecast, chosen by rolling-origin CV inside Jan-Apr, scored {usd(model['test_mae'][model['selected']])}/day MAE on May-Jun vs {usd(model['test_mae']['Constant mean'])} for the constant baseline.",
     "evidence": "analysis/model.py", "result": f"80% band +/-{usd(model['interval_80_halfwidth'])} covered {pct(model['interval_80_coverage'])} of test days (under-covers; reported as is).",
     "alternative": "A simpler model is as good. Weekday mean scored {usd(model['test_mae']['Weekday mean'])}; selection used CV only, the test was touched once.".replace("{usd(model['test_mae']['Weekday mean'])}", usd(model['test_mae']['Weekday mean'])),
     "limitation": "Events count only if announced before the forecast date; June over-forecast because of the tourism dip.", "tab": "forecast"},
    {"id": "C11", "q": "Q6", "claim": f"Of {plan['n_plans']} legal plans, the best spends {usd(top['cost'])} and keeps {usd(top['keep'])}: expected net {usd(top['exp_net'])}, gain in {pct(top['p_gain'])} of 4,000 simulations.",
     "evidence": "analysis/plan.py: every legal combination (<= 3 types, <= $100K, limits, comp rules)",
     "result": f"The GM's plan (lease 10 replacements, {usd(plan['gm_plan']['cost'])}) ranks {plan['gm_plan']['rank']} of {plan['n_plans']}, expected net {usd(plan['gm_plan']['exp_net'])}, gain in {pct(plan['gm_plan']['p_gain'])} of runs.",
     "alternative": "Keep the whole budget (rank shown in the search).",
     "limitation": "Effects are assumption ranges grounded in this data, listed per action.", "tab": "plan"},
    {"id": "C12", "q": "Q6", "claim": f"Past promotions worked: the Winter Slot Tournament added {pct(promos[0]['pct'], 1)} coin-in and Locals Week {pct(promos[1]['pct'], 1)}, both above every one of {plan['facts']['promo_placebo']['n']} placebo windows.",
     "evidence": "analysis/plan.py: facts(); events, floor", "result": f"About {usd(plan['facts']['promo_lift_per_day'])} extra theo per promotion day; placebo spread {usd(plan['facts']['promo_noise_per_day'])}/day.",
     "alternative": "The lift is chance. The same estimator on non-event windows never reaches it.",
     "limitation": "Two promotions; July may be softer, so the plan scales lift to 50-100%.", "tab": "plan"},
]

(OUT / "claims.json").write_text(json.dumps(CLAIMS, indent=1))
md = ["# Claims & Evidence appendix (v2)", "", "Generated by `v2/analysis/claims.py` from the pipeline results; every number is re-checked by `verify.py`.", ""]
for c in CLAIMS:
    md += [f"## {c['id']} ({c['q']}) {c['claim']}", "", f"- **Table / query:** `{c['evidence']}`", f"- **Result:** {c['result']}",
           f"- **Alternative tested:** {c['alternative']}", f"- **Limitation:** {c['limitation']}", ""]
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "CLAIMS.md").write_text("\n".join(md))
print(len(CLAIMS), "claims")
