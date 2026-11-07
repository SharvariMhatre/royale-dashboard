"""Generate docs/writeup.md, docs/evidence.md and docs/judge_qa.md from app_data/findings/team.json and app_data/team/all_claims.parquet.
Every number comes from those files. Run after src/integrate_team.py: python -I src/make_docs.py"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "app_data" / "findings" / "team.json").read_text())
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

usd = lambda x: f"{'-' if x < 0 else ''}${abs(x):,.0f}"
pct = lambda x, d=0: f"{x * 100:.{d}f}%"

V, DN, LF = T["verdicts"], T["downtime"], T["leak_clues"]
gm = {r["machine_id"]: r for r in T["gm10_rows"]}
zones = {z["zone_name"]: z for z in T["zones"]}
top = V["gm10_top_zone"]
clo = {r["period"][2:].strip(): r["b40_vs_rest"] for r in T["b40_closure"]}
before, during, after = clo.values()  # file order is before, during, after the closure (period labels start 1, 2, 3)
slot = T["same_slot"][0]
insp = T["inspect"][0]
hold = re.search(r"Hold ([\d.]+)% vs ([\d.]+)% expected", insp["reason"])
mv = max(T["moves"], key=lambda m: m["adjusted_change_pct"])
mets = {m["model_name"]: m for m in T["model"]["metrics"]}
best = min(mets.values(), key=lambda m: m["mae_usd"])
base = next(m for k, m in mets.items() if k.startswith("baseline"))
parts = ", ".join(f"{n} {k.lower()}" for k, n in sorted(V["gm10"].items(), key=lambda kv: -kv[1]))
lt = T["luck_tests_gm10"]
gp = T["gm_plan"]

# ---------------------------------------------------------------- write-up (max 400 words)
MIN = json.loads((ROOT / "app_data" / "findings" / "minimum.json").read_text())
musd = lambda x: f"${abs(x) / 1e6:.1f}M"
kusd = lambda x: f"${abs(x) / 1e3:.1f}k"
D, PL, Q4, Q5 = T["demand"], T["players"], MIN["q4"], MIN["q5"]
r5 = Q5["ratio_by_month"]
wf = list(T["weekday_forecast"].items())          # busiest first
assert mv["adjusted_change_pct"] > 1.0            # "more than doubled" must be true
ZONE = "the floor rate for the same games"        # zone_index compares a zone with the floor for the SAME games

W = f"""# The Gilded Ace: should we replace the 10 lowest machines?

## Problem
The GM wants to replace the 10 lowest-earning machines (Jan 1 to Jun 30, 2025). Low earnings can come from luck, location or a leak. We tested all three.

## Q1: which machines are truly underperforming?
- {V['gm10_truly_bad']} of the GM's {V['gm10_n']} are truly bad: {parts}.
- {V['gm10_in_b40']} sit in {top}, which earns {pct(zones[top]['zone_index_vs_floor'])} of {ZONE}. During the walkway closure it earned {pct(during)} of the rest of the floor, against {pct(before)} before and {pct(after)} after.
- The casino already replaced one machine in slot {slot['location']} on {slot['date']}, and the replacement landed on the list too: replacing doesn't fix a bad spot.
- {mv['machine_id']} more than doubled its earnings per available hour after moving from {mv['from_zone']} to {mv['to_zone']} (+{pct(mv['adjusted_change_pct'])} vs unmoved machines). Only {len(T['moves'])} machines moved.
- {insp['machine_id']} is an inspect lead (hold {hold.group(1)}% against {hold.group(2)}% expected), a lead to check, not an accusation.
- Tests: 10,000 fair replays per machine for luck (a supported explanation for {lt['Supported']} of the 10, unlikely for {lt['Unlikely']}, not supported for {lt['Not supported']}), and each machine against the same game elsewhere.

## Q2 to Q5
- **Demand:** coin-in changed {D['change_pct']:+.1f}% from the first to the last 4 full weeks.
- **Downtime:** {pct(DN['share_of_scheduled'], 2)} of scheduled hours, at most {usd(DN['lost_theo_usd'])} of expected win. It does not explain the list.
- **Players:** tracked players lost {musd(PL['net_usd'])} against {musd(Q4['theo_usd'])} expected. The top 10% hold {pct(Q4['top10pct_share_of_theo'])} of expected losses.
- **Comps:** {kusd(Q5['comp_cost_usd'])}, rising from {pct(r5['2025-01'], 2)} to {pct(r5['2025-06'], 2)} of theo, Jan to Jun.

## Model
Weekday plus events misses daily coin-in by {usd(best['mae_usd'])} on May and June, against {usd(base['mae_usd'])} for a constant baseline (train Jan to Apr, test May to Jun). It changes where staffing goes: {wf[0][0]} ({musd(wf[0][1])}) and {wf[1][0]} ({musd(wf[1][1])}) are forecast busiest, so an extra technician shift goes there, and the forecast is the baseline for measuring a promotion weekend's lift.

## Q6: $100,000 plan
PENDING: team decision at 6 PM. For comparison, the GM's own plan (replace 10 machines) costs {usd(gp['cost_usd'])} with an estimated {usd(gp['expected_benefit_usd'])} benefit.

## How we would measure it
Each funded action gets one metric, a baseline or control, and a 30-day check. Final measures follow the plan decision.
"""
n = len(re.sub(r"[#*\-]+", " ", W).split())
assert n <= 400, f"write-up has {n} words"
assert "—" not in W
(DOCS / "writeup.md").write_text(W, encoding="utf8")
print(f"docs/writeup.md: {n} words (limit 400)")

# ---------------------------------------------------------------- evidence appendix
c = pd.read_parquet(ROOT / "app_data" / "team" / "all_claims.parquet")
order = {q: i for i, q in enumerate(["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Model", "Pipeline"])}
c = c.assign(o=c.question.map(order).fillna(99)).sort_values(["o", "claim_id"])
E = ["# Claims and Evidence appendix", "",
     f"{len(c)} claims from the three analysts. Each lists the table behind it, the result, the alternative explanation we tested and the limitation. "
     "Source: `app_data/team/all_claims.parquet` (merge of `p1_claims`, `p2_claims`, `p3_claims`), generated by `src/make_docs.py`. "
     "Data release 0.9.0-draft; the data is synthetic. Anomalies are leads to inspect, never accusations.", ""]
for q, g in c.groupby("question", sort=False):
    E += [f"## {q}", ""]
    for r in g.itertuples():
        E += [f"### {r.claim_id}: {r.claim}", "", f"- **Evidence table:** {r.evidence_table}", f"- **Result:** {r.result}",
              f"- **Alternative tested:** {r.alternative_tested}", f"- **Limitation:** {r.limitation}",
              f"- **Confidence:** {r.confidence} (from {r.source})", ""]
# ---- checks performed (computed from the data files, not typed)
import numpy as np

ls = pd.read_parquet(ROOT / "app_data" / "team" / "p2_luck_scores.parquet").luck_score.dropna()
k4 = np.isclose(ls * 10000, np.round(ls * 10000))
k3 = np.isclose(ls * 1000, np.round(ls * 1000))
MIN = json.loads((ROOT / "app_data" / "findings" / "minimum.json").read_text())
mw = next(m for m in T["model"]["metrics"] if m["model_name"] == "weekday_average")
E += ["## Checks performed", "",
      f"- **Luck percentile basis (10,000 replays).** `p2_luck_scores` was built from 10,000 fair replays per machine in Databricks. Verified in Databricks by the "
      f"analyst and replicated here on the exported table: {int((k4 & ~k3).sum())} of {len(ls)} luck scores need four decimal places and all {int(k4.sum())} are multiples of 1/10,000, "
      f"which cannot happen with 1,000 replays. Limitation: this shows the precision is at least 1/10,000; it does not show how the replays were drawn. "
      f"The exported `p2_luck_sims` is a 500-per-machine sample used only for the Machine Details chart.",
      f"- **Independent forecast check.** A weekday-average forecast built separately in the dashboard code misses by {usd(MIN['model']['mae_model_usd'])} a day on May and June; "
      f"the team's `weekday_average` row says {usd(mw['mae_usd'])}.",
      f"- **Comp cost totals.** The team's `p1_comps` totals {usd(T['comps']['comp_cost_usd'])}; the dashboard's own build from the player table totals {usd(MIN['q5']['comp_cost_usd'])}.", ""]
(DOCS / "evidence.md").write_text("\n".join(E), encoding="utf8")
print(f"docs/evidence.md: {len(c)} claims")

# ---------------------------------------------------------------- judge Q&A
r1181 = gm["M-1181"]
peer = re.search(r"\((\d+)% of peers\)", r1181["reason"]).group(1)
J = f"""# Likely judge questions

**1. Why is M-1181 Bad spot when luck is Not supported?**
These are two different questions. Bad spot answers why its total is low: it earns {peer}% of same-game peers, which is normal for its game, but its zone earns {pct(zones[top]['zone_index_vs_floor'])} of {ZONE}, so its expected win is low. Luck percentile asks whether it also fell short of that low expectation: only {pct(r1181['luck_score'], 1)} of fair replays did worse, so luck alone does not explain the extra shortfall. Both can be true. The Inspect rule needs |z| > 3.29 (under 0.1% by chance). M-1181's z is {r1181['luck_z']:.2f}, well inside that, so it is not an inspect lead, while {insp['machine_id']} sits at {insp['luck_z']:.2f}. The zone stays the main driver, so the verdict is Bad spot. With 310 machines, {T['luck_floor']['below_1pct']} fall below 1% where about {T['luck_floor']['expected_by_chance']} would by chance, so one machine at {pct(r1181['luck_score'], 1)} is not enough to call a fault.

**2. How do you know it is the location and not the machines?**
Four checks point the same way. The zone earns {pct(zones[top]['zone_index_vs_floor'])} of {ZONE} (the zone index compares each game with the same game across the floor). The same games elsewhere earn more. {top} dipped to {pct(during)} of the rest of the floor while its walkway was closed ({pct(before)} before, {pct(after)} after). And {mv['machine_id']} more than doubled its earnings per available hour after moving to {mv['to_zone']} (+{pct(mv['adjusted_change_pct'])} vs unmoved machines). The limit: only {len(T['moves'])} machines moved, so the move evidence is thin and we say so.

**3. How was the model validated?**
Train {T['model']['train']}, test {T['model']['test']} ({T['model']['test_days']} days), split by time, frozen before testing. {best['model_name'].replace('_', ' ').capitalize()} misses by {usd(best['mae_usd'])} a day against {usd(base['mae_usd'])} for a constant baseline. MLflow run IDs are on the Model page. We reproduced the weekday average result independently. No later-published data was used.

**4. Why not just replace the 10 machines?**
{V['gm10_truly_bad']} of the 10 are truly bad, and {V['gm10_in_b40']} sit in the weakest zone, so new machines in the same spots would face the same zone. The GM's plan costs {usd(gp['cost_usd'])}, more than the whole budget, and the team estimates {usd(gp['expected_benefit_usd'])} benefit.

**5. Are the leak clues accusations?**
No. There are {LF['total']} clues on {LF['machines']} machines. They are rule flags to inspect, such as long outages or repeat faults. Downtime in total is {pct(DN['share_of_scheduled'], 2)} of scheduled hours, so it does not explain the bottom 10.

**6. How will you know the plan worked?**
PENDING: depends on the plan chosen at 6 PM. Each action will have one metric, a baseline or control and a 30-day check. The budget page shows how each line would be measured and a payback sensitivity beyond 30 days, labelled as an assumption.
"""
assert "—" not in J and "—" not in "\n".join(E)
(DOCS / "judge_qa.md").write_text(J, encoding="utf8")
print("docs/judge_qa.md: 6 questions")
