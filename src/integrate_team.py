"""Build app_data/team/all_claims.parquet and app_data/findings/team.json from the exported team files.
Run after every export: python -I src/integrate_team.py. Pages read these numbers; nothing is typed by hand."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEAM = ROOT / "app_data" / "team"
OUT = ROOT / "app_data" / "findings" / "team.json"
SCRIPT = "src/integrate_team.py"


def rd(name):
    p = TEAM / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else None


def counts(s: pd.Series) -> dict:
    return {k: int(v) for k, v in s.value_counts().items()}


def main():
    F = {}
    # ---- all_claims: p1/p2/p3 merged with a source column ----
    parts = []
    for p in ("p1", "p2", "p3"):
        d = rd(f"{p}_claims")
        if d is not None:
            parts.append(d.assign(source=p))
    if parts:
        c = pd.concat(parts, ignore_index=True)
        assert c.claim_id.is_unique, "claim_id collides across p1/p2/p3"
        c.to_parquet(TEAM / "all_claims.parquet", index=False)
        F["claims"] = {"count": int(len(c)), "by_question": counts(c.question)}

    v = rd("p2_verdicts")
    if v is not None:
        gm = v[v.in_manager_bottom10]
        F["verdicts"] = {"gm10": counts(gm.verdict), "floor": counts(v.verdict), "machines": int(len(v)),
                         "gm10_truly_bad": int((gm.verdict == "Truly bad").sum()), "gm10_n": int(len(gm)),
                         "gm10_in_b40": int((gm.zone_id == gm.zone_id.mode()[0]).sum()), "gm10_top_zone": gm.zone_name.mode()[0],
                         "scope": "Full period Jan-Jun 2025 (one precomputed scope)"}
        # same-slot finding: a machine retired on a date and another installed the same date in the same location, both in the GM 10
        ret = {m: re.search(r"retired (\d{4}-\d{2}-\d{2})", r) for m, r in zip(gm.machine_id, gm.reason)}
        ins = {m: re.search(r"installed (\d{4}-\d{2}-\d{2})", r) for m, r in zip(gm.machine_id, gm.reason)}
        loc = dict(zip(gm.machine_id, gm.location_id))
        pairs = [{"retired": a, "installed": b, "date": ra.group(1), "location": loc[a]}
                 for a, ra in ret.items() if ra for b, rb in ins.items() if rb and rb.group(1) == ra.group(1) and loc[a] == loc[b]]
        F["same_slot"] = pairs
        F["gm10_rows"] = gm.sort_values("manager_rank")[["manager_rank", "machine_id", "zone_name", "location_id", "verdict", "reason", "luck_score",
                                                          "house_win_usd", "theo_usd", "days_on_floor", "luck_z"]].round(4).to_dict("records")
        F["inspect"] = [r for r in F["gm10_rows"] if r["verdict"] == "Inspect"]
        lr = lambda x: "Supported" if x >= 0.20 else ("Unlikely" if x >= 0.01 else "Not supported")   # same rule as app/pages.py luck_result
        F["luck_tests_gm10"] = counts(gm.luck_score.map(lr))
        F["luck_floor"] = {"below_1pct": int((v.luck_score < 0.01).sum()), "machines": int(len(v)), "expected_by_chance": round(len(v) * 0.01, 1)}
        # luck_score check: is it the share of simulated results at or below the actual?
        s = rd("p2_luck_sims")
        if s is not None:
            share = s.merge(v[["machine_id", "house_win_usd"]], on="machine_id").assign(
                le=lambda d: d.sim_house_win_usd <= d.house_win_usd).groupby("machine_id").le.mean()
            diff = (share - v.set_index("machine_id").luck_score).dropna().abs()
            F["luck_score_check"] = {"definition": "share of simulated six-month results at or below the machine's actual house win",
                                     "max_abs_diff_vs_file_all_machines": round(float(diff.max()), 3),
                                     "sims_per_machine": int(s.groupby("machine_id").size().median())}
        F["availability_units"] = {"p2_verdicts_max": round(float(v.availability_pct.max()), 3),
                                   "note": "p2_verdicts availability_pct is a fraction (max 1.0); p1_downtime availability_pct is 0-100"}

    d = rd("p1_downtime")
    if d is not None:
        F["downtime"] = {"lost_theo_usd": round(float(d.lost_theo_usd.sum()), 2),
                         "hours_down": round(float((d.scheduled_hours - d.available_hours).sum()), 1),
                         "share_of_scheduled": round(float(1 - d.available_hours.sum() / d.scheduled_hours.sum()), 4),
                         "lost_theo_by_cause": {k: round(float(x), 2) for k, x in d.groupby("cause").lost_theo_usd.sum().items()},
                         "scope": "Full period, active machine-days; lost_theo_usd is an upper bound (guests may play elsewhere)"}
    lc = rd("p1_leak_clues")
    if lc is not None:
        F["leak_clues"] = {"by_rule": counts(lc.rule_failed), "machines": int(lc.machine_id.nunique()), "total": int(len(lc)),
                           "note": "leads to inspect, not accusations"}
    dem = rd("p3_demand")
    if dem is not None:   # Q2: first 4 vs last 4 complete Monday-Sunday weeks, floor-wide coin-in
        day = dem.groupby("gaming_date").coin_in_usd.sum().reset_index()
        day["week_start"] = pd.to_datetime(day.gaming_date).dt.to_period("W-SUN").dt.start_time
        wk = day.groupby("week_start").agg(c=("coin_in_usd", "sum"), n=("gaming_date", "nunique"))
        wk = wk[wk.n == 7].c
        F["demand"] = {"full_weeks": int(len(wk)), "first4_avg_usd": round(float(wk.head(4).mean()), 2), "last4_avg_usd": round(float(wk.tail(4).mean()), 2),
                       "change_pct": round(float(wk.tail(4).mean() / wk.head(4).mean() - 1) * 100, 2)}
    pl = rd("p3_players")
    if pl is not None:
        F["players"] = {"wagered_usd": round(float(pl.wagered_usd.sum()), 2), "won_back_usd": round(float(pl.won_back_usd.sum()), 2),
                        "net_usd": round(float(pl.net_usd.sum()), 2)}
    mv = rd("p2_move_effects")
    if mv is not None:
        F["moves"] = mv.assign(move_date=mv.move_date.astype(str)).round(4).to_dict("records")
    ac = rd("p2_actions")
    if ac is not None:
        g = ac[ac.action.str.contains("manager", case=False)]
        if len(g):
            F["gm_plan"] = {"action": str(g.action.iloc[0]), "quantity": int(g.quantity.iloc[0]), "cost_usd": float(g.cost_usd.iloc[0]),
                            "expected_benefit_usd": float(g.expected_benefit_usd.iloc[0])}
    z, b = rd("p2_zone_index"), rd("p2_b40_closure_effect")
    if z is not None:
        F["zones"] = z.round(4).to_dict("records")
    if b is not None:
        F["b40_closure"] = b.round(4).to_dict("records")
    cn = rd("p3_concentration")
    if cn is not None:
        F["concentration"] = cn.round(4).to_dict("records")
    m, fr = rd("p3_model_metrics"), rd("p3_forecast_results")
    if m is not None and fr is not None:
        t = fr[fr.split == "test"]
        mae_m, mae_b = float((t.actual_usd - t.model_pred_usd).abs().mean()), float((t.actual_usd - t.baseline_pred_usd).abs().mean())
        match = m.iloc[(m.mae_usd - mae_m).abs().argsort().iloc[0]]
        wd = fr[fr.split == "test"].assign(day=lambda d: pd.to_datetime(d.gaming_date).dt.day_name()).groupby("day").model_pred_usd.mean().sort_values(ascending=False)
        F["weekday_forecast"] = {k: round(float(x), 2) for k, x in wd.items()}   # test-period mean of the model's daily forecast, busiest first
        F["model"] = {"metrics": m.round(2).to_dict("records"), "forecast_mae_model_usd": round(mae_m, 2),
                      "forecast_mae_baseline_usd": round(mae_b, 2), "test_days": int(len(t)),
                      "forecast_file_model_is": str(match.model_name) if abs(match.mae_usd - mae_m) < 1 else "unknown (no metrics row matches)",
                      "train": f"{fr[fr.split == 'train'].gaming_date.min():%Y-%m-%d}..{fr[fr.split == 'train'].gaming_date.max():%Y-%m-%d}",
                      "test": f"{t.gaming_date.min():%Y-%m-%d}..{t.gaming_date.max():%Y-%m-%d}"}
    cp = rd("p1_comps")
    if cp is not None:
        F["comps"] = {"comp_cost_usd": round(float(cp.comp_cost_usd.sum()), 2), "months": int(cp.month.nunique())}
    F["_meta"] = {"producer": "Sharvari (integration)", "script": SCRIPT,
                  "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(F, indent=1, default=str))
    print(json.dumps({k: F[k] for k in ("verdicts", "same_slot", "luck_score_check", "model", "claims") if k in F}, indent=1)[:2500])


if __name__ == "__main__":
    main()
