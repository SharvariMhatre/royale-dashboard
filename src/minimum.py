"""Self-sufficient minimum: builds app_data/min_*.parquet + findings/minimum.json
from prepared_daily_view, property_day, player_period, calendar_day, action_catalog.
Run with the project venv: python -I src/minimum.py   (data repo expected at ../dashboard-royale)"""
import json
from datetime import datetime, timezone
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT.parent / "dashboard-royale" / "data"
OUT = ROOT / "app_data"
V, PD, PP = (str(D / "1_prepared_views" / f"{t}.parquet") for t in ("prepared_daily_view", "property_day", "player_period"))
CAL, CAT = (str(D / "2_machine_decision" / f"{t}.parquet") for t in ("calendar_day", "action_catalog"))
SCRIPT = "src/minimum.py"
F = {}  # findings -> minimum.json


def q(sql):
    return duckdb.sql(sql).df()


def save(df, name):
    df.to_parquet(OUT / name, index=False)
    (OUT / (name + "._meta.json")).write_text(json.dumps({
        "schema_version": "min-1", "data_release": "0.9.0-draft",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "producer": "Sharvari (minimum)"}))

# ---------------- Q1 ----------------
MIN_DAYS, AVAIL_LOW = 30, 0.90          # simple rules, stated on the page
CFG_OK, CFG_LOW, ZONE_LOW, OCC_OK, CFG_BY_DESIGN = 0.90, 0.80, 0.85, 0.85, 0.85
LUCK_BIG = 0.20  # Unlucky/Luck needs luck residual below -20% of theo


def loo_median(m, col, keys, min_n):
    """Leave-one-out median of `col` among rows sharing `keys`; NaN when fewer than min_n peers."""
    out = []
    for i, r in m.iterrows():
        g = m[(m[keys] == r[keys]) & (m.index != i)][col]
        out.append(g.median() if len(g) >= min_n else np.nan)
    return pd.Series(out, index=m.index)


def q1():
    # active rows only; scheduled hours from calendar_day.scheduled_seconds (23 h on 2025-03-08)
    m = q(f"""
      SELECT v.machine_id, COUNT(*) AS days_on_floor, COUNT(DISTINCT v.location_id) AS n_locations,
             SUM(v.house_win_usd)::DOUBLE house_win_usd, SUM(v.theo_usd)::DOUBLE theo_usd,
             SUM(v.luck_residual_usd)::DOUBLE luck_residual_usd, SUM(v.coin_in_usd)::DOUBLE coin_in_usd,
             SUM(v.paid_spins)::DOUBLE paid_spins, SUM(v.occupied_hours) occupied_hours,
             SUM(v.available_hours) available_hours, SUM(c.scheduled_seconds)/3600.0 scheduled_hours
      FROM '{V}' v JOIN '{CAL}' c USING (gaming_date)
      WHERE v.active AND v.location_id <> '' GROUP BY v.machine_id""")
    # modal zone and config per machine (machines can move or be re-configured)
    mode = lambda col: q(f"""SELECT machine_id, {col} FROM (SELECT machine_id, {col}, COUNT(*) n FROM '{V}'
        WHERE active AND location_id<>'' GROUP BY machine_id, {col})
        QUALIFY ROW_NUMBER() OVER (PARTITION BY machine_id ORDER BY n DESC, {col})=1""")
    m = m.merge(mode("zone_id"), on="machine_id").merge(mode("config_id"), on="machine_id")
    m = m.merge(q(f"SELECT DISTINCT config_id, configured_rtp::DOUBLE configured_rtp FROM '{V}'"), on="config_id")
    m["availability"] = m.available_hours / m.scheduled_hours
    m["theo_per_avail_hour"] = m.theo_usd / m.available_hours
    m["avg_bet_usd"] = m.coin_in_usd / m.paid_spins
    m["occupancy"] = m.occupied_hours / m.available_hours
    m["moved_flag"] = m.n_locations > 1
    # 1) zone_index: zone theo/avail-hr (ratio of sums) over the median of zone values
    zn = m.groupby("zone_id").agg(t=("theo_usd", "sum"), h=("available_hours", "sum"))
    zt = zn.t / zn.h
    m["zone_theo_per_hr"] = m.zone_id.map(zt)
    m["zone_index"] = m.zone_theo_per_hr / zt.median()
    # 2) config_index: leave-one-out median of same-config machines, fall back to zone peers if < 3
    cfg_med = loo_median(m, "theo_per_avail_hour", "config_id", 3)
    zone_med = loo_median(m, "theo_per_avail_hour", "zone_id", 1)
    m["config_peer_group"] = np.where(cfg_med.notna(), "same config", "same zone (config too rare)")
    m["config_index"] = m.theo_per_avail_hour / cfg_med.fillna(zone_med)
    m["n_config_peers"] = [int(((m.config_id == r.config_id) & (m.index != i)).sum()) for i, r in m.iterrows()]
    # 3) occupancy vs zone median (leave-one-out)
    m["occupancy_vs_zone"] = m.occupancy / loo_median(m, "occupancy", "zone_id", 1)
    # config earns low "by design": config-level theo/hr well under the floor median and (higher RTP or smaller bet)
    cf = m.groupby("config_id").agg(t=("theo_usd", "sum"), h=("available_hours", "sum"), c=("coin_in_usd", "sum"),
                                    s=("paid_spins", "sum"))
    cf_idx = (cf.t / cf.h) / m.theo_per_avail_hour.median()
    cf_bet = cf.c / cf.s
    floor_bet, floor_rtp = m.coin_in_usd.sum() / m.paid_spins.sum(), m.configured_rtp.median()
    m["config_floor_index"] = m.config_id.map(cf_idx)
    m["by_design_low"] = (m.config_floor_index < CFG_BY_DESIGN) & ((m.configured_rtp > floor_rtp) | (m.config_id.map(cf_bet) < floor_bet))
    m["rank_house_win"] = m.house_win_usd.rank(method="first").astype(int)
    m["gm_bottom10"] = m.rank_house_win <= 10

    def label(r):
        if r.days_on_floor < MIN_DAYS:
            return "Too little data", f"Only {r.days_on_floor} days on the floor."
        if r.availability < AVAIL_LOW:
            return "Broken lead", f"Only {r.availability:.0%} of scheduled hours available."
        if r.config_index >= CFG_OK and r.luck_residual_usd < -LUCK_BIG * r.theo_usd:
            return "Unlucky", (f"Earns {r.config_index:.0%} of same-config machines per available hour, "
                               f"but casino win is ${-r.luck_residual_usd:,.0f} below expected win.")
        if r.config_index >= CFG_LOW and r.by_design_low and r.occupancy_vs_zone >= OCC_OK:
            return "Game setting", (f"Keeps pace with its config ({r.config_index:.0%}), but {r.config_id} earns low by design "
                                    f"(RTP {r.configured_rtp:.0%}, avg bet ${r.avg_bet_usd:.2f}); players use it normally.")
        if r.zone_index < ZONE_LOW:
            return "Location", f"Its zone earns {r.zone_index:.0%} of the typical zone per available hour."
        if r.config_index < CFG_LOW:
            return "Truly bad lead", f"Earns {r.config_index:.0%} of same-config machines per available hour."
        return "Mixed", f"Config index {r.config_index:.0%}, zone index {r.zone_index:.0%}; no single cause."
    # second causes: any strong cause other than the primary label (shown on the evidence card)
    def also(r):
        c = []
        if r.luck_residual_usd < -LUCK_BIG * r.theo_usd and r.label != "Unlucky":
            c.append(f"Luck (-${-r.luck_residual_usd:,.0f} vs expected win)")
        if r.zone_index < ZONE_LOW and r.label != "Location":
            c.append(f"Location (zone index {r.zone_index:.0%})")
        if r.config_index < CFG_LOW and r.label != "Truly bad lead":
            c.append(f"Below same-config peers ({r.config_index:.0%})")
        if r.availability < AVAIL_LOW and r.label != "Broken lead":
            c.append(f"Downtime (availability {r.availability:.0%})")
        return "; ".join(c)
    lab = m.apply(label, axis=1, result_type="expand")
    m["label"], m["label_reason"] = lab[0], lab[1]
    m["also_strong"] = m.apply(also, axis=1)
    # zone story for the weakest zone: same games elsewhere, and seat occupancy (occupied/available hours, ratio of sums)
    wz = zt.idxmin()
    inz, out = m[m.zone_id == wz], m[m.zone_id != wz]
    gap = {}
    for cfg, g in inz.groupby("config_id"):
        o = out[out.config_id == cfg]
        if len(o):
            gap[cfg] = 1 - (g.theo_usd.sum() / g.available_hours.sum()) / (o.theo_usd.sum() / o.available_hours.sum())
    F_zone = {"zone": wz, "theo_gap_vs_same_games_elsewhere_min": round(min(gap.values()), 3),
              "theo_gap_vs_same_games_elsewhere_max": round(max(gap.values()), 3), "configs_compared": sorted(gap),
              "occupancy_in_zone": round(float(inz.occupied_hours.sum() / inz.available_hours.sum()), 3),
              "occupancy_elsewhere": round(float(out.occupied_hours.sum() / out.available_hours.sum()), 3),
              "zone_theo_per_avail_hour": round(float(zt.min()), 2),
              "other_zones_theo_per_avail_hour": [round(float(zt.drop(wz).min()), 2), round(float(zt.drop(wz).max()), 2)]}
    m["scope"] = "Full (Jan-Jun)"
    m["source_script"] = SCRIPT
    m = m.sort_values("house_win_usd").reset_index(drop=True)
    save(m, "min_q1.parquet")
    b = m[m.gm_bottom10]
    F["q1"] = {"machines_on_floor": int(len(m)), "labels_bottom10": b.label.value_counts().to_dict(),
               "labels_all": m.label.value_counts().to_dict(),
               "thresholds": {"min_days": MIN_DAYS, "availability_low": AVAIL_LOW, "config_ok": CFG_OK, "config_low": CFG_LOW,
                              "zone_low": ZONE_LOW, "luck_big": LUCK_BIG, "occupancy_ok": OCC_OK, "by_design_floor_index": CFG_BY_DESIGN},
               "bottom10_house_win_usd": round(float(b.house_win_usd.sum()), 2),
               "unlucky_label_count_all": int((m.label == "Unlucky").sum()), "luck_big_share_of_theo": LUCK_BIG,
               "zone_story": F_zone, "scope": "Full (Jan-Jun) 2025, active machine-days only"}
    return m




# ---------------- machine-day extract (lets pages recompute any date range / bank live) ----------------
def machine_day():
    d = q(f"""SELECT v.machine_id, v.gaming_date, v.zone_id, v.bank_id, v.config_id, v.manufacturer,
              v.configured_rtp::DOUBLE configured_rtp, v.available_hours, v.occupied_hours,
              c.scheduled_seconds/3600.0 scheduled_hours, v.paid_spins::DOUBLE paid_spins,
              v.coin_in_usd::DOUBLE coin_in_usd, v.payout_usd::DOUBLE payout_usd, v.house_win_usd::DOUBLE house_win_usd,
              v.theo_usd::DOUBLE theo_usd, v.luck_residual_usd::DOUBLE luck_residual_usd
              FROM '{V}' v JOIN '{CAL}' c USING (gaming_date) WHERE v.active AND v.location_id <> ''""")
    save(d, "min_machine_day.parquet")
    return d


# ---------------- Q2 ----------------
def q2():
    w = q(f"""SELECT date_trunc('week', p.gaming_date)::DATE week_start,
        SUM(p.coin_in_usd)::DOUBLE coin_in_usd, SUM(p.theo_usd)::DOUBLE theo_usd,
        SUM(p.occupied_machine_hours) occupied_machine_hours, SUM(p.available_machine_hours) available_machine_hours,
        SUM(p.total_zone_entries_observed)::DOUBLE entries, AVG(p.counter_coverage_share) counter_coverage_share,
        COUNT(*) n_days,
        string_agg(DISTINCT NULLIF(p.events_active, ''), '; ') events,
        string_agg(DISTINCT NULLIF(c.federal_holiday, ''), '; ') holidays
        FROM '{PD}' p JOIN '{CAL}' c USING (gaming_date) GROUP BY 1 ORDER BY 1""")
    w["coin_in_per_occupied_hour"] = w.coin_in_usd / w.occupied_machine_hours
    w["scope"], w["source_script"] = "weekly, full period", SCRIPT
    save(w, "min_q2.parquet")
    full = w[w.n_days == 7]
    a, b = full.head(4), full.tail(4)
    F["q2"] = {"first4_weeks_avg_coin_in_usd": round(float(a.coin_in_usd.mean()), 2),
               "last4_weeks_avg_coin_in_usd": round(float(b.coin_in_usd.mean()), 2),
               "change_pct": round(float(b.coin_in_usd.mean() / a.coin_in_usd.mean() - 1) * 100, 1),
               "entries_change_pct": round(float(b.entries.mean() / a.entries.mean() - 1) * 100, 1),
               "scope": "average of first vs last 4 complete weeks; entries are observed counts only (see counter coverage)",
               "explanation_status": "untested in minimum version (Person 3 tests explanations)"}


# ---------------- Q3 ----------------
def q3(d):
    d = d.copy()
    d["downtime_hours"] = (d.scheduled_hours - d.available_hours).clip(lower=0)
    # lost theo = downtime x the machine's OWN theo per available hour (upper bound: guests may move elsewhere)
    g = d.groupby("machine_id")
    own = g.theo_usd.sum() / g.available_hours.sum()
    d["lost_theo_usd"] = d.downtime_hours * d.machine_id.map(own)
    d["week_start"] = pd.to_datetime(d.gaming_date).dt.to_period("W-SUN").dt.start_time.dt.date
    w = d.groupby(["week_start", "manufacturer"], as_index=False).agg(
        downtime_hours=("downtime_hours", "sum"), lost_theo_usd=("lost_theo_usd", "sum"), scheduled_hours=("scheduled_hours", "sum"))
    w["scope"], w["source_script"] = "week x manufacturer, full period (upper bound)", SCRIPT
    save(w, "min_q3.parquet")
    tot = d.downtime_hours.sum()
    F["q3"] = {"downtime_hours": round(float(tot), 1), "downtime_share_of_scheduled": round(float(tot / d.scheduled_hours.sum()), 4),
               "lost_theo_usd_upper_bound": round(float(d.lost_theo_usd.sum()), 2),
               "by_manufacturer_lost_theo_usd": {k: round(float(v), 2) for k, v in d.groupby("manufacturer").lost_theo_usd.sum().items()},
               "worst_week": str(w.groupby("week_start").lost_theo_usd.sum().idxmax()),
               "scope": "Full period, active machine-days; upper bound because guests may play elsewhere"}


# ---------------- Q4 / Q5 ----------------
def q4q5():
    t = q(f"""SELECT opening_tier AS tier, period_month AS month, COUNT(DISTINCT player_id) players,
        SUM(tracked_coin_in_usd)::DOUBLE wagered_usd, SUM(tracked_payout_usd)::DOUBLE paid_back_usd,
        SUM(tracked_net_usd)::DOUBLE net_usd, SUM(theo_usd)::DOUBLE theo_usd
        FROM '{PP}' GROUP BY ALL ORDER BY 1,2""")
    t = t[t.players >= 10].copy()  # groups of 10+ only
    t["scope"], t["source_script"] = "tier x month (carded play only)", SCRIPT
    save(t, "min_q4.parquet")
    # concentration: players ranked by whole-period theo; share of total theo held by the top 10% of players
    p = q(f"SELECT player_id, SUM(theo_usd)::DOUBLE theo, SUM(tracked_net_usd)::DOUBLE net FROM '{PP}' GROUP BY 1")
    s = p.sort_values("theo", ascending=False)
    k = max(1, int(round(len(s) * 0.10)))
    top = s.head(k)
    conc = pd.DataFrame([{"group": "all tracked players", "players": len(s), "top10pct_players": k,
                          "top10pct_share_of_theo": top.theo.sum() / s.theo.sum(), "top10pct_net_usd": top.net.sum(),
                          "all_net_usd": s.net.sum(), "scope": "Full period, ranked by theo", "source_script": SCRIPT}])
    save(conc, "min_q4_conc.parquet")
    F["q4"] = {"tracked_wagered_usd": round(float(t.wagered_usd.sum()), 2), "paid_back_usd": round(float(t.paid_back_usd.sum()), 2),
               "player_net_usd": round(float(t.net_usd.sum()), 2), "theo_usd": round(float(t.theo_usd.sum()), 2),
               "top10pct_share_of_theo": round(float(conc.top10pct_share_of_theo[0]), 4), "tracked_players": int(len(s)),
               "scope": "Full period, carded play only; player net is the opposite sign of house win"}
    c = q(f"""SELECT period_month AS month, opening_tier AS tier, SUM(comp_cost_usd)::DOUBLE comp_cost_usd,
        SUM(comp_face_value_usd)::DOUBLE comp_face_value_usd, SUM(theo_usd)::DOUBLE theo_usd,
        SUM(comps_redeemed) comps_redeemed, SUM(points_earned) points_earned, SUM(points_redeemed) points_redeemed,
        COUNT(DISTINCT player_id) players FROM '{PP}' GROUP BY ALL ORDER BY 1,2""")
    c = c[c.players >= 10].copy()
    c["comp_cost_to_theo_ratio"] = (c.comp_cost_usd / c.theo_usd.where(c.theo_usd > 0))  # undefined when theo is 0
    c["scope"], c["source_script"] = "month x tier (carded play only)", SCRIPT
    save(c, "min_q5.parquet")
    mo = c.groupby("month").agg(cc=("comp_cost_usd", "sum"), th=("theo_usd", "sum"))
    F["q5"] = {"comp_cost_usd": round(float(mo.cc.sum()), 2), "comp_cost_to_theo_overall": round(float(mo.cc.sum() / mo.th.sum()), 4),
               "ratio_by_month": {k: round(float(v), 4) for k, v in (mo.cc / mo.th).items()},
               "scope": "Full period, tracked players; comp cost is cost to house (already inside POS cogs, not subtracted twice)"}


# ---------------- Q6 ----------------
def q6():
    a = q(f"SELECT * FROM '{CAT}'")
    a["operating_days"] = (30 - a.lead_days).clip(lower=0)
    # guide formula per unit: (unit_cost + recurring x max(0, 30 - lead_days)) / 100 dollars
    a["cost_per_unit_usd"] = (a.unit_cost_cents + a.recurring_cost_cents_per_day * a.operating_days) / 100
    a["max_cost_usd"] = a.cost_per_unit_usd * a.quantity_limit
    a["is_keep_money"] = a.action_type_id == "A-HOLD"
    a["scope"], a["source_script"] = "30 days from 2025-07-01; catalogue prices only, no benefit estimates", SCRIPT
    keep = ["action_type_id", "name", "unit", "quantity_limit", "lead_days", "operating_days", "downtime_minutes",
            "incompatibility_group", "cost_per_unit_usd", "max_cost_usd", "is_keep_money", "scope", "source_script"]
    save(a[keep], "min_q6.parquet")
    lease = float(a.loc[a.action_type_id == "A-REPLACE-LEASE", "cost_per_unit_usd"].iloc[0])
    assert lease == 3380.0, lease  # guide example: $2,500 + 16 days x $55
    F["q6"] = {"budget_usd": 100000, "horizon": "30 days from 2025-07-01", "lease_cost_per_unit_usd": lease,
               "keep_money_valid": True, "rules": "up to 3 action types; no comp pilot with comp change; one move/replacement per machine"}


# ---------------- model placeholder ----------------
def model():
    d = q(f"SELECT gaming_date, local_weekday, coin_in_usd::DOUBLE coin_in_usd FROM '{PD}' ORDER BY 1")
    d["gaming_date"] = pd.to_datetime(d.gaming_date)
    train = d.gaming_date <= "2025-04-30"
    tr = d[train]
    assert tr.gaming_date.max() <= pd.Timestamp("2025-04-30")   # nothing from May-Jun enters the training means
    wk = tr.groupby("local_weekday").coin_in_usd.mean()   # frozen on Jan-Apr only
    wk_test = d[~train].groupby("local_weekday").coin_in_usd.mean()  # for comparison only, never used to predict
    out = pd.DataFrame({"gaming_date": d.gaming_date, "actual_usd": d.coin_in_usd,
                        "pred_model_usd": d.local_weekday.map(wk), "pred_baseline_usd": d[train].coin_in_usd.mean(),
                        "split": np.where(train, "train", "test")})
    save(out, "min_model.parquet")
    t = out[out.split == "test"]
    mae = lambda c: float((t.actual_usd - t[c]).abs().mean())
    F["model"] = {"model": "weekday mean of daily coin-in", "baseline": "constant Jan-Apr mean", "train": "2025-01-01..2025-04-30",
                  "test": "2025-05-01..2025-06-30", "mae_model_usd": round(mae("pred_model_usd"), 2),
                  "mae_baseline_usd": round(mae("pred_baseline_usd"), 2), "test_days": int(len(t)),
                  "weekday_means_train_usd": {k: round(float(v), 2) for k, v in wk.items()},
                  "weekday_means_test_for_comparison_usd": {k: round(float(v), 2) for k, v in wk_test.items()},
                  "leak_check": {"train_rows": int(len(tr)), "train_last_date": str(tr.gaming_date.max().date()),
                                 "test_rows_in_training": int((tr.gaming_date >= pd.Timestamp("2025-05-01")).sum())},
                  "beats_baseline": bool(mae("pred_model_usd") < mae("pred_baseline_usd")),
                  "decision_affected": "weekday staffing and service coverage (placeholder; Person 3's model replaces it)"}


def run_all():
    OUT.mkdir(exist_ok=True)
    (OUT / "findings").mkdir(exist_ok=True)
    m = q1()
    d = machine_day()
    q2(); q3(d); q4q5(); q6(); model()
    F["_meta"] = {"producer": "Sharvari (minimum)", "script": SCRIPT, "data_release": "0.9.0-draft",
                  "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    (OUT / "findings" / "minimum.json").write_text(json.dumps(F, indent=1, default=str))
    return m


if __name__ == "__main__":
    run_all()
    print(json.dumps({k: v for k, v in F.items() if k != "q1"}, indent=1, default=str)[:3500])
