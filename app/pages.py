"""Page bodies. Headline numbers come from app_data/findings/minimum.json; filtered tables are recomputed live."""
import pandas as pd
import streamlit as st
import re
import html

import altair as alt
import budget
import theme as T
from common import ALL, evidence, findings, load, machine_day, machine_totals, show, snap_months, source, team, tfind, usd

SCRIPT = "src/minimum.py"
PAGE_OBJ = {}  # filled by streamlit_app.py with st.Page objects


LABEL_WORDS = {
    "Unlucky": "Draws normal play for its game, but paid out more than expected. Likely luck; keep it.",
    "Game setting": "Keeps pace with its game, but that game earns little by design (high payout rate or small bets).",
    "Location": "Its zone earns well below the typical zone, so the weakness belongs to the zone, not the machine.",
    "Truly bad lead": "Earns well below identical games and the zone is not weak. Candidate to replace; verify first.",
    "Broken lead": "Unavailable too much of the time; inspect or repair before judging.",
    "Too little data": "Under 30 days on the floor; too early to judge.",
    "Mixed": "No single cause fits; not enough evidence.",
}
EVIDENCE = {"A-MOVE-MACHINE": "Machine Details", "A-MOVE-BANK": "Machine Details", "A-REPLACE-LEASE": "Machine Details",
            "A-REPLACE-BUY": "Machine Details", "A-INSPECT": "Machine Details", "A-TECH-SHIFT": "Demand & Downtime",
            "A-PREVENTIVE": "Demand & Downtime", "A-WAYFINDING": "Demand & Downtime", "A-COMP-PILOT": "Players & Comps",
            "A-COMP-CHANGE": "Players & Comps", "A-PROMO": "Demand & Downtime", "A-SURVEY": "Demand & Downtime",
            "A-HOLD": "Machine Details"}


def _pending(*keys):
    bad = [k for k in keys if findings(k) is None]
    if bad:
        st.warning("Pending: headline numbers are not available yet.")
    return bool(bad)


def _overview_min(sel):
    if _pending("q1", "q6"):
        return
    q1, _ = load("min_q1.parquet")
    q6, _ = load("min_q6.parquet")
    if q1 is None or q6 is None:
        return
    f = findings("q1")
    z, f3 = f["zone_story"], findings("q3")
    lb = f["labels_bottom10"]
    others = ", ".join(f"{v} {'looks' if v == 1 else 'look'} {k.lower()}" for k, v in lb.items() if k != "Location")
    T.info(f"**Answer in brief.** Of the GM's 10 lowest machines, {lb.get('Location', 0)} sit in a weak zone ({z['zone']} earns "
            f"{z['theo_gap_vs_same_games_elsewhere_min']:.0%}-{z['theo_gap_vs_same_games_elsewhere_max']:.0%} less than the same games "
            f"elsewhere){', and ' + others if others else ''}, so the list mostly shows where machines sit, not how they perform. "
            f"Downtime is small (at most {usd(f3['lost_theo_usd_upper_bound'])} of expected win, {f3['downtime_share_of_scheduled']:.2%} of scheduled hours), "
            f"so it is unlikely to explain the list; you have $100,000 across at most 3 action types, and keeping the money is allowed.")
    st.markdown("**The GM's list:** the 10 machines with the lowest total house win, Jan 1 to Jun 30, 2025. "
                "House win alone ignores luck, time on the floor and location, so each row is checked below.")
    live = machine_day(sel)
    b = q1[q1.gm_bottom10].copy()
    full_scope = sel["preset"].startswith("Full") and sel["bank"] == ALL
    if live is not None:
        t = machine_totals(live)[["machine_id", "house_win_usd", "luck_residual_usd", "availability", "theo_per_avail_hour"]]
        b = b[["machine_id", "zone_id", "config_id", "days_on_floor", "zone_index", "config_index", "occupancy_vs_zone", "label",
               "label_reason"]].merge(t, on="machine_id", how="left")
    show(b, {"machine_id": ("Machine", "text"), "zone_id": ("Zone", "text"), "config_id": ("Game type", "text"),
             "days_on_floor": ("Days on floor (all 6 months)", "int"), "house_win_usd": ("Casino win, selected period", "usd_nf"),
             "luck_residual_usd": ("Win vs expected (luck), selected period", "usd_nf"),
             "availability": ("Time available, selected period", "pct_nf"),
             "theo_per_avail_hour": ("Expected win per hour available, selected period", "usd_nf"),
             "zone_index": ("Zone earnings vs typical zone", "pct"), "config_index": ("Earnings vs same game elsewhere", "pct"),
             "occupancy_vs_zone": ("Seats used vs zone", "pct"), "label": ("Likely cause", "text"), "label_reason": ("Why", "text")})
    if not full_scope:
        T.info("Money, availability and theo columns follow your filters. Labels, indices and reasons are full-period "
                "(Jan-Jun, whole floor) and are not recomputed for this selection.")
    source("min_q1.parquet + min_machine_day.parquet", SCRIPT, "labels: Full (Jan-Jun); money columns: " + sel["preset"])
    st.markdown(f"**{z['zone']} machines earn {z['theo_gap_vs_same_games_elsewhere_min']:.0%}-"
                f"{z['theo_gap_vs_same_games_elsewhere_max']:.0%} less than the same games in other zones, and {z['zone']} has "
                f"about {z['occupancy_in_zone']:.0%} seat occupancy vs about {z['occupancy_elsewhere']:.0%} elsewhere: "
                f"the zone, not the machines.**")
    st.caption("Theo per available hour, same game compared across zones (ratio of sums); occupancy = occupied / available hours. "
               "Full period. Source: findings/minimum.json (q1.zone_story).")
    counts = f["labels_bottom10"]
    st.subheader("What the labels say about the GM's 10: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    with st.expander("What each label means (plain words)"):
        for k, v in LABEL_WORDS.items():
            st.markdown(f"- **{k}**: {v}")
    st.caption("Minimum version: simple rules (thresholds in findings/minimum.json). Richer verdicts with intervals replace "
               "these when they arrive. The zone is not yet separated from game type or position.")



def _details_min(sel):
    q1, _ = load("min_q1.parquet")
    md = machine_day(sel)
    if q1 is None or md is None or _pending("q1"):
        return
    ids = list(q1.machine_id)
    default = ids[0]
    mid = st.selectbox("Machine (GM's list first)", ids, index=ids.index(default))
    r = q1[q1.machine_id == mid].iloc[0]
    st.subheader(f"{mid}: {r.label}. {r.label_reason}")
    c = st.columns(4)
    c[0].metric("Casino win (all 6 months)", usd(r.house_win_usd))
    c[1].metric("Win vs expected, i.e. luck (all 6 months)", usd(r.luck_residual_usd))
    c[2].metric("Time available (all 6 months)", f"{r.availability:.1%}")
    c[3].metric("Days on floor", f"{int(r.days_on_floor)}")
    if r.also_strong:
        st.warning(f"Primary cause: {r.label}. Also strong: {r.also_strong}.")
    st.markdown("**Competing explanations tested** (full period)")
    st.table(pd.DataFrame([
        ["Luck", f"casino win {usd(r.luck_residual_usd)} vs expected win", "Supported" if r.luck_residual_usd < -0.1 * r.theo_usd else "Not the main cause"],
        ["Downtime", f"availability {r.availability:.1%}", "Not supported" if r.availability >= 0.9 else "Supported"],
        ["Location", f"zone {r.zone_id} earns {r.zone_index:.0%} of the typical zone", "Supported" if r.zone_index < 0.85 else "Not supported"],
        ["Game / config", f"{r.config_id}: machine earns {r.config_index:.0%} of same-config peers per available hour", "Supported" if r.config_index < 0.8 else "Not supported"],
        ["Moved?", "moved during the period" if r.moved_flag else "stayed in one place", "n/a" if not r.moved_flag else "Check before/after"],
        ["Players avoid it?", f"occupancy {r.occupancy_vs_zone:.0%} of zone median", "Not supported" if r.occupancy_vs_zone >= 0.85 else "Supported"],
    ], columns=["Explanation", "Evidence", "Result"]))
    m = md[md.machine_id == mid]
    if len(m):
        w = m.assign(week=pd.to_datetime(m.gaming_date).dt.to_period("W-SUN").dt.start_time).groupby("week")[["house_win_usd", "theo_usd"]].sum()
        st.caption("Weekly casino win vs expected win (dollars per week), selected period")
        T.line(w.rename(columns={"house_win_usd": "Casino win ($)", "theo_usd": "Expected win ($)"}), "week", ["Casino win ($)", "Expected win ($)"], "Week starting", "Dollars per week")
    else:
        T.info("Not on floor in this period.")
    st.caption("Verdict wording is minimum-version rules; 'not enough evidence' (Mixed) is an allowed answer. Peer comparison "
               "uses same-config machines (leave-one-out median); no confidence interval yet.")
    source("min_q1.parquet + min_machine_day.parquet", SCRIPT, "labels: Full (Jan-Jun); chart: " + sel["preset"])


def _demand_min(sel):
    if _pending("q2", "q3"):
        return
    w, _ = load("min_q2.parquet")
    d3 = machine_day(sel)
    if w is None or d3 is None:
        return
    f2, f3 = findings("q2"), findings("q3")
    st.header(f"Floor coin-in {f2['change_pct']:+.1f}% (last 4 vs first 4 full weeks); entries {f2['entries_change_pct']:+.1f}%")
    st.caption(f"Cause not yet tested: {f2['explanation_status']}.")
    ws = pd.to_datetime(w.week_start)
    ww = w[(w.n_days == 7) & (ws >= pd.Timestamp(sel["start"])) & (ws + pd.Timedelta(days=6) <= pd.Timestamp(sel["end"]))]
    if ww.empty:
        T.info("No complete Monday-Sunday week fits inside this range; widen it to see the weekly trend.")
    else:
        T.line(ww.set_index("week_start")[["coin_in_usd"]].rename(columns={"coin_in_usd": "Weekly coin-in ($)"}), "week_start", ["Weekly coin-in ($)"], "Week starting", "Money wagered per week ($)")
        show(ww, {"week_start": ("Week starting", "date"), "coin_in_usd": ("Money wagered", "usd"), "theo_usd": ("Expected casino win", "usd"),
                  "occupied_machine_hours": ("Machine-hours in use", "int"), "entries": ("Door entries counted", "int"),
                  "counter_coverage_share": ("Door counters online", "pct"), "events": ("Events", "text"), "holidays": ("Holidays", "text")})
    st.caption("Whole floor (bank filter does not apply). Only complete Monday-Sunday weeks inside the range are shown. "
               "Entries are door counts, not unique visitors; missing counter hours are excluded (see coverage).")
    source("min_q2.parquet", SCRIPT, "weekly, floor-wide, " + sel["preset"])
    st.divider()
    d = d3.copy()
    d["downtime_hours"] = (d.scheduled_hours - d.available_hours).clip(lower=0)
    g = d.groupby("machine_id")
    d["lost"] = d.downtime_hours * d.machine_id.map(g.theo_usd.sum() / g.available_hours.sum())
    d["week"] = pd.to_datetime(d.gaming_date).dt.to_period("W-SUN").dt.start_time
    st.header(f"Downtime cost about {usd(d.lost.sum())} of expected win ({d.downtime_hours.sum():,.0f} hours) in this selection")
    st.caption("Upper bound: downtime hours x the machine's own theo per available hour; guests may play elsewhere. "
               f"Full-period figure: ${f3['lost_theo_usd_upper_bound']:,.0f} lost theo, {f3['downtime_share_of_scheduled']:.2%} of scheduled hours.")
    p = d.pivot_table(index="week", columns="manufacturer", values="lost", aggfunc="sum").fillna(0)
    T.bars(p, "week", list(p.columns), "Week starting", "Expected win lost to downtime ($)")
    show(d.groupby("manufacturer")[["downtime_hours", "lost"]].sum().reset_index(),
         {"manufacturer": ("Manufacturer", "text"), "downtime_hours": ("Hours down", "int"), "lost": ("Expected win lost", "usd")})
    source("min_machine_day.parquet", SCRIPT, f"{sel['preset']}, bank: {sel['bank']}")


def _players_min(sel):
    if _pending("q4", "q5"):
        return
    t, _ = load("min_q4.parquet")
    c, _ = load("min_q5.parquet")
    if t is None or c is None:
        return
    ms = snap_months(sel)
    f4, f5 = findings("q4"), findings("q5")
    sub = lambda x: x[x.month.isin(ms) & ((x.tier == sel["tier"]) | (sel["tier"] == ALL))]
    t, c = sub(t), sub(c)
    st.header(f"Tracked players wagered {usd(t.wagered_usd.sum())}, got back {usd(t.paid_back_usd.sum())}, net {usd(t.net_usd.sum())}")
    st.caption("Player net = payout minus wager (opposite sign of house win). Carded play only. Groups of 10+ players. "
               f"Full-period concentration: the top 10% of {f4['tracked_players']:,} tracked players hold {f4['top10pct_share_of_theo']:.0%} of theo.")
    agg = t.groupby("month")[["wagered_usd", "paid_back_usd", "net_usd", "theo_usd"]].sum()
    T.bars(agg.reset_index(), "month", "net_usd", "Month", "Player net, wins minus losses ($)", color=T.NAVY)
    show(t, {"month": ("Month", "month"), "tier": ("Loyalty tier", "text"), "players": ("Players", "int"), "wagered_usd": ("Wagered", "usd"),
             "paid_back_usd": ("Paid back", "usd"), "net_usd": ("Players' net", "usd"), "theo_usd": ("Expected casino win", "usd")})
    source("min_q4.parquet", SCRIPT, f"months {ms[0]}..{ms[-1]}, tier {sel['tier']}")
    st.divider()
    cm = c.groupby("month")[["comp_cost_usd", "theo_usd"]].sum()
    cm["Comp cost / theo"] = cm.comp_cost_usd / cm.theo_usd.where(cm.theo_usd > 0)
    first, last = f5["ratio_by_month"]["2025-01"], f5["ratio_by_month"]["2025-06"]
    st.header(f"Comps cost {usd(c.comp_cost_usd.sum())} here; comp cost / theo went {first:.2%} (Jan) to {last:.2%} (Jun)")
    st.caption("Comp cost is cost to the house, already inside POS cost of goods: counted once. Reinvestment = comp cost / theo. "
               "Why it changed is not yet tested.")
    T.line(cm, "month", ["Comp cost / theo"], "Month", "Comp cost / expected win", fmt=".1%")
    show(c, {"month": ("Month", "month"), "tier": ("Loyalty tier", "text"), "players": ("Players", "int"), "comp_cost_usd": ("Comp cost to casino", "usd"),
             "comp_face_value_usd": ("Comp menu value (not cash)", "usd"), "theo_usd": ("Expected casino win", "usd"),
             "comp_cost_to_theo_ratio": ("Comp cost / expected win", "pct2"), "comps_redeemed": ("Comps redeemed", "int"),
             "points_earned": ("Points earned", "int"), "points_redeemed": ("Points redeemed", "int")})
    source("min_q5.parquet", SCRIPT, f"months {ms[0]}..{ms[-1]}, tier {sel['tier']}")


def _model_min(sel):
    if _pending("model", "q6"):
        return
    m, _ = load("min_model.parquet")
    q6, _ = load("min_q6.parquet")
    if m is None or q6 is None:
        return
    f = findings("model")
    verdict = "beats" if f["beats_baseline"] else "does not beat"
    st.header(f"Weekday-average forecast {verdict} the constant baseline: average miss {usd(f['mae_model_usd'])} vs {usd(f['mae_baseline_usd'])} per day (MAE)")
    st.caption(f"Model: {f['model']}. Baseline: {f['baseline']}. Both frozen on {f['train']}; tested on {f['test']} ({f['test_days']} days). "
               f"Fixed dates, unaffected by the sidebar filters. Decision it informs: {f['decision_affected']}. No later-published data used.")
    lk = f["leak_check"]
    st.markdown(f"**Leak check:** the weekday means use {lk['train_rows']} training days ending {lk['train_last_date']}; "
                f"{lk['test_rows_in_training']} May-Jun days were used to build them.")
    wm = pd.DataFrame({"mean_train": f["weekday_means_train_usd"], "mean_test": f["weekday_means_test_for_comparison_usd"]})
    wm = wm.reindex(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]).rename_axis("day").reset_index()
    show(wm, {"day": ("Weekday", "text"), "mean_train": ("Average daily wagering, Jan-Apr (the model's input)", "usd"),
              "mean_test": ("Average daily wagering, May-Jun (comparison only, not used)", "usd")})
    t = m[m.split == "test"][["gaming_date", "actual_usd", "pred_model_usd", "pred_baseline_usd"]].rename(columns={
        "actual_usd": "Actual", "pred_model_usd": "Weekday model", "pred_baseline_usd": "Constant baseline (Jan-Apr average)"})
    long = t.melt("gaming_date", var_name="Line", value_name="Dollars")
    names = ["Actual", "Weekday model", "Constant baseline (Jan-Apr average)"]
    chart = alt.Chart(long).mark_line().encode(
        x=alt.X("gaming_date:T", title="Day (May-Jun 2025)"), y=alt.Y("Dollars:Q", title="Daily money wagered ($)"),
        color=alt.Color("Line:N", scale=alt.Scale(domain=names, range=[T.NAVY, T.OKABE_ITO[0], T.OKABE_ITO[1]]), legend=alt.Legend(title="Legend", orient="top")),
        strokeDash=alt.StrokeDash("Line:N", scale=alt.Scale(domain=names, range=[[1, 0], [6, 3], [2, 2]]), legend=None))
    T.altair(chart)
    source("min_model.parquet", SCRIPT, "test May-Jun 2025, floor daily coin-in $")
    st.divider()
    st.subheader("Action catalogue with budget cost (guide formula)")
    show(q6, {"name": ("Action", "text"), "unit": ("Priced per", "text"), "quantity_limit": ("Most allowed", "int"),
              "lead_days": ("Days to start", "int"), "operating_days": ("Days running in 30", "int"),
              "cost_per_unit_usd": ("Cost per unit", "usd"), "max_cost_usd": ("Cost at the limit", "usd"),
              "incompatibility_group": ("Cannot combine with others in group", "text")})
    st.caption("Lease example: $2,500 + 16 days x $55 = $3,380 per machine. Build a plan on the Overview page. "
               "Expected benefit, uncertainty and measurement plan arrive with the team's budget file.")
    source("min_q6.parquet", SCRIPT, "30 days from 2025-07-01")


def _catalogue_builder(q6):
    st.caption("30 days from July 1. Up to 3 action types. Cost per action = quantity x (unit cost + daily cost x "
               "max(0, 30 - lead days)). Benefits are NOT estimated in the minimum version; keeping money is a valid answer.")
    acts = q6[~q6.is_keep_money].set_index("action_type_id")
    pick = st.multiselect("Action types (max 3)", list(acts.index), format_func=lambda a: acts.loc[a, "name"], max_selections=3)
    rows = []
    for a in pick:
        r = acts.loc[a]
        qty = st.number_input(f"Quantity: {r['name']} ({r['unit']}, limit {int(r.quantity_limit)})", 1, int(r.quantity_limit), 1, key=a)
        rows.append({"Action": r["name"], "Quantity": qty, "Lead days": int(r.lead_days), "Operating days": int(r.operating_days),
                     "Cost $": qty * r.cost_per_unit_usd, "Group": r.incompatibility_group, "Evidence on page": EVIDENCE[a]})
    if rows:
        df = pd.DataFrame(rows)
        total = df["Cost $"].sum()
        show(df.assign(c=df["Cost $"]), {"Action": ("Action", "text"), "Quantity": ("Quantity", "int"), "Lead days": ("Days to start", "int"),
             "Operating days": ("Days running in 30", "int"), "c": ("Cost", "usd"), "Evidence on page": ("Evidence", "text")})
        if {"A-COMP-PILOT", "A-COMP-CHANGE"} <= set(pick):
            st.error("Incompatible: a comp pilot cannot run together with the floor-wide comp change.")
        if sum(1 for a in pick if acts.loc[a, "incompatibility_group"] == "same_machine") > 1:
            st.warning("Moves/replacements must target different machines (not checked here: targets are not chosen yet).")
        left = 100000 - total
        (st.error if left < 0 else st.success)(f"Spent ${total:,.0f}; remaining ${left:,.0f}" + (" (OVER BUDGET)" if left < 0 else ""))
        st.markdown("**Evidence for each line:**")
        for a in pick:
            tgt = EVIDENCE[a]
            if tgt in PAGE_OBJ:
                st.page_link(PAGE_OBJ[tgt], label=f"{acts.loc[a, 'name']}: see {tgt}")
            else:
                st.write(f"{acts.loc[a, 'name']}: see {tgt}")
    else:
        st.success("Keep the money: $100,000 remaining, no action slot used.")
    source("min_q6.parquet", SCRIPT, "catalogue prices; 30 days from 2025-07-01")



# =====================================================================================
# Team-file versions of the pages. Each falls back to the minimum version above when a
# team file is missing or fails validation.
# =====================================================================================
EVID_Q = {"A-MOVE-MACHINE": ["Q1"], "A-MOVE-BANK": ["Q1"], "A-REPLACE-LEASE": ["Q1"], "A-REPLACE-BUY": ["Q1"], "A-INSPECT": ["Q1"],
          "A-TECH-SHIFT": ["Q3"], "A-PREVENTIVE": ["Q3"], "A-WAYFINDING": ["Q2"], "A-PROMO": ["Q2", "Model"], "A-SURVEY": ["Q2"],
          "A-COMP-PILOT": ["Q5"], "A-COMP-CHANGE": ["Q5"]}
TEAM_SRC = "Databricks export (app_data/team)"


def luck_result(p) -> str:
    """Luck as an explanation: >=20% Supported, 1-20% Unlikely, <1% Not supported (share of fair replays that did worse than reality)."""
    return "Supported" if p >= 0.20 else ("Unlikely" if p >= 0.01 else "Not supported")


def _full_weeks(daily: pd.DataFrame, start, end) -> pd.DataFrame:
    """Keep only complete Monday-Sunday weeks (7 distinct days) that sit fully inside [start, end]."""
    d = daily.copy()
    d["week_start"] = pd.to_datetime(d.gaming_date).dt.to_period("W-SUN").dt.start_time
    n = d.groupby("week_start").gaming_date.nunique()
    ok = n[(n == 7)].index
    ok = [w for w in ok if w >= pd.Timestamp(start) and w + pd.Timedelta(days=6) <= pd.Timestamp(end)]
    return d[d.week_start.isin(ok)]


def overview(sel):
    v, tv = team("p2_verdicts"), tfind("verdicts")
    if v is None or tv is None:
        st.warning("Team verdict file is pending; showing the minimum version of the Decision Room.")
        _overview_min(sel)
    else:
        dn = tfind("downtime") or {}
        zn = {z["zone_name"]: z for z in (tfind("zones") or [])}
        top = tv["gm10_top_zone"]
        parts = ", ".join(f"{n} {k.lower()}" for k, n in sorted(tv["gm10"].items(), key=lambda kv: -kv[1]))
        zi = zn.get(top, {}).get("zone_index_vs_floor")
        s2 = f"{tv['gm10_in_b40']} of the {tv['gm10_n']} sit in **{top}**" + (f", which earns {zi:.0%} of the floor rate for the same games" if zi is not None else "")
        if dn:
            s2 += f". Downtime explains little ({dn['share_of_scheduled']:.2%} of scheduled hours)"
        headline = ("Don't replace the 10. Fix the spot." if tv["gm10_truly_bad"] == 0
                    else f"Replace {tv['gm10_truly_bad']} of the 10, not all of them.")
        T.hero("Answer in brief", headline,
               [f"**{tv['gm10_truly_bad']} of the GM's {tv['gm10_n']} are truly bad machines:** {parts}.", s2 + "."],
               [(f"{tv['gm10_truly_bad']} of {tv['gm10_n']}", "truly bad machines on the GM's list"),
                (f"{tv['gm10_in_b40']} of {tv['gm10_n']}", f"sit in {top}"),
                (f"{zi:.0%}" if zi is not None else "n/a", f"{top} rate vs floor, same games"),
                (f"{dn['share_of_scheduled']:.2%}" if dn else "n/a", "of scheduled hours lost to downtime")])

        g = v[v.in_manager_bottom10].sort_values("manager_rank").copy()
        full_scope = sel["preset"].startswith("Full") and sel["bank"] == ALL
        T.section("01", "The GM's 10, re-examined",
                  "The 10 lowest machines by total casino win, Jan 1 to Jun 30, 2025. A low total can come from luck, location or a leak; "
                  "each card shows the team's verdict after testing all three. **Click a card to open its case file.**")
        T.gm_cards([{"rank": int(r.manager_rank), "id": r.machine_id, "zone": r.zone_name, "verdict": r.verdict, "why": str(r.reason),
                     "luck": f"{r.luck_score:.1%}", "days": int(r.days_on_floor)} for r in g.itertuples()])
        st.caption("Luck pct = luck percentile: share of 10,000 fair replays per machine (run in Databricks, Spark) that did worse than reality; "
                   "under 5% means unusually bad luck. Verdicts are for the full period (Jan-Jun).")
        for p in tfind("same_slot") or []:
            T.info(f"**Same slot counted twice.** {p['retired']} was retired on {p['date']} and {p['installed']} was installed that day in the "
                   f"same slot ({p['location']}). Both are on the GM's list: the casino already replaced one machine there, and the replacement "
                   "landed on the list too. Replacing doesn't fix a bad spot.")

        live = machine_day(sel)
        if live is not None:
            t = machine_totals(live)[["machine_id", "house_win_usd", "availability"]].rename(
                columns={"house_win_usd": "win_sel", "availability": "avail_sel"})
            g = g.merge(t, on="machine_id", how="left")
        else:
            g["win_sel"], g["avail_sel"] = g.house_win_usd, g.availability_pct
        g["luck_test"] = g.luck_score.map(luck_result)
        with st.expander("Full evidence table for the GM's 10 (money follows your period and bank filters)", expanded=not full_scope):
            show(g, {"manager_rank": ("GM rank", "int"), "machine_id": ("Machine", "text"), "zone_name": ("Zone", "text"),
                     "days_on_floor": ("Days on floor (all 6 months)", "int"), "win_sel": ("Casino win, selected period", "usd_nf"),
                     "avail_sel": ("Time available, selected period", "pct_nf"), "verdict": ("Verdict (full period)", "verdict"),
                     "luck_score": ("Luck percentile", "pct1"), "luck_test": ("Luck as the explanation", "text"),
                     "reason": ("Why", "text"), "confidence": ("Confidence", "text")}, wrap=True)
            st.caption("Luck as the explanation: Supported at 20% or more, Unlikely at 1-20%, Not supported below 1%.")
            if not full_scope:
                T.info("Money and availability follow your filters. Verdicts, luck chances and reasons are for the full period "
                       "(Jan-Jun, whole floor), the only scope the team precomputed; they are not recomputed for this selection.")
            source("team/p2_verdicts.parquet + min_machine_day.parquet", "Bharath's notebook (p2) + " + SCRIPT,
                   "verdicts: Full (Jan-Jun); money columns: " + sel["preset"])
        with st.expander("What each verdict means (plain words)"):
            for k, w in VERDICT_WORDS.items():
                st.markdown(f"- **{k}**: {w}")

        vv = v if sel["bank"] == ALL else v[v.bank_id == sel["bank"]]
        T.section("02", "The floor map: where the problem sits",
                  f"All {len(v)} machines at their floor positions. Shape and colour show the verdict; **ringed** machines are the GM's 10; "
                  "the dashed box is Back Forty." + ("" if sel["bank"] == ALL else f" Bank **{sel['bank']}** is highlighted."))
        _floor_map(v, sel["bank"])
        cnt = vv.verdict.value_counts().rename_axis("Verdict").reset_index(name="Machines")
        if len(cnt):
            kc = dict(zip(cnt.Verdict, cnt.Machines))
            T.takeaway(f"{kc.get('Healthy', 0)} of {len(vv)} machines are Healthy and {kc.get('Bad spot', 0)} are Bad spot; none are Truly bad or Broken."
                       if not kc.get("Truly bad") and not kc.get("Broken") else f"{kc.get('Healthy', 0)} of {len(vv)} machines are Healthy.")
            cnt["order"] = cnt.Verdict.map({k: i for i, k in enumerate(T.VERDICT_ORDER)})
            T.altair(alt.Chart(cnt).mark_bar().encode(
                y=alt.Y("Verdict:N", sort=[k for k in T.VERDICT_ORDER if k in kc], title=None),
                x=alt.X("Machines:Q", title="Machines"),
                color=alt.Color("Verdict:N", scale=alt.Scale(domain=list(T.VERDICT_COLOR), range=list(T.VERDICT_COLOR.values())), legend=None),
                tooltip=["Verdict", "Machines"]) + alt.Chart(cnt).mark_text(align="left", dx=4, color=T.NAVY, fontWeight=600).encode(
                y=alt.Y("Verdict:N", sort=[k for k in T.VERDICT_ORDER if k in kc]), x="Machines:Q", text="Machines:Q"), height=220)
        st.caption("Verdict counts follow the bank filter; the period filter does not apply (full-period verdicts).")
        if sel["bank"] != ALL:
            with st.expander(f"Machines in bank {sel['bank']} ({len(vv)})", expanded=True):
                show(vv.sort_values("house_win_usd"), {"machine_id": ("Machine", "text"), "zone_name": ("Zone", "text"), "verdict": ("Verdict", "verdict"),
                     "house_win_usd": ("Casino win, full period", "usd"), "luck_score": ("Luck percentile", "pct"),
                     "in_manager_bottom10": ("In the GM's 10", "yesno")})
        _zone_evidence()
    evidence(["Q1"], title="Evidence: Q1 claims behind the verdicts")
    budget_section(sel)


VERDICT_WORDS = {
    "Bad spot": "Normal for its game, but its zone earns much less than other zones. The location is the problem.",
    "Short exposure": "Few days on the floor (installed or retired during the period), so its total is low for that reason alone.",
    "Inspect": "Its payout is far from the game's math beyond what luck explains. A lead to verify the machine, not an accusation.",
    "Unlucky": "Normal play for its game; the win came in below expectation by chance.",
    "Healthy": "Earning in line with its peers.",
    "Broken": "Unavailable too much of the time.",
    "Truly bad": "Earns well below identical games even after accounting for luck, exposure and location.",
}


def _floor_map(v: pd.DataFrame, bank: str):
    d = v.copy()
    d["gm10"] = d.in_manager_bottom10.map({True: "Yes", False: "No"})
    d["focus"] = True if bank == ALL else (d.bank_id == bank)
    zones = sorted(d.zone_name.unique())
    zoom = st.pills("Zoom to a zone", ["Whole floor"] + zones, default="Whole floor", key="map_zoom") or "Whole floor"
    view = d if zoom == "Whole floor" else d[d.zone_name == zoom]
    pad_x, pad_y = (6, 10) if zoom == "Whole floor" else (4, 6)
    dom = [k for k in T.VERDICT_ORDER if k in set(d.verdict)]
    sc_x = alt.Scale(domain=[view.x.min() - pad_x, view.x.max() + pad_x], nice=False)
    sc_y = alt.Scale(domain=[view.y.max() + pad_y, view.y.min() - pad_y - 2], nice=False)  # flipped so the plan reads top-down
    tip = [alt.Tooltip("machine_id:N", title="Machine"), alt.Tooltip("zone_name:N", title="Zone"), alt.Tooltip("bank_id:N", title="Bank"),
           alt.Tooltip("verdict:N", title="Verdict"), alt.Tooltip("house_win_usd:Q", title="Casino win", format="$,.0f"),
           alt.Tooltip("luck_score:Q", title="Luck percentile", format=".1%"), alt.Tooltip("gm10:N", title="On the GM's list")]
    pick = alt.selection_point(name="pick", fields=["machine_id"], on="click", clear="dblclick", empty=False)
    zb = d[d.zone_name == "Back Forty"]
    layers = []
    if len(zb):
        box = pd.DataFrame([{"x": zb.x.min() - 3.5, "x2": zb.x.max() + 3.5, "y": zb.y.min() - 4, "y2": zb.y.max() + 3.5}])
        layers.append(alt.Chart(box).mark_rect(fill=T.SEAFOAM, fillOpacity=0.25, stroke=T.TEAL_DARK, strokeDash=[6, 4], strokeWidth=2)
                      .encode(x=alt.X("x:Q", scale=sc_x, axis=None), x2="x2", y=alt.Y("y:Q", scale=sc_y, axis=None), y2="y2"))
    big = 1 if zoom == "Whole floor" else 2.4
    pts = alt.Chart(d).mark_point(filled=True, strokeWidth=0, cursor="pointer", clip=True).encode(
        x=alt.X("x:Q", scale=sc_x, axis=None), y=alt.Y("y:Q", scale=sc_y, axis=None),
        color=alt.Color("verdict:N", title="Verdict", scale=alt.Scale(domain=dom, range=[T.VERDICT_COLOR[k] for k in dom])),
        shape=alt.Shape("verdict:N", title="Verdict", scale=alt.Scale(domain=dom, range=[T.VERDICT_SHAPE[k] for k in dom])),
        size=alt.condition(pick, alt.value(260 * big), alt.value(70 * big)),
        opacity=alt.condition("datum.focus", alt.value(0.95), alt.value(0.15)), tooltip=tip).add_params(pick)
    ring = alt.Chart(d[d.in_manager_bottom10]).mark_point(filled=False, color=T.NAVY, strokeWidth=2.2, clip=True).encode(
        x=alt.X("x:Q", scale=sc_x), y=alt.Y("y:Q", scale=sc_y), size=alt.value(360 * big), tooltip=tip)
    zl = d.groupby("zone_name").agg(x=("x", "mean"), y=("y", "min")).reset_index()
    zl["y"] = zl.y - 4.5 - (zl.zone_name == "Back Forty") * 3
    lab = alt.Chart(zl).mark_text(fontWeight=700, fontSize=12 if zoom == "Whole floor" else 15, color=T.NAVY, clip=True).encode(
        x=alt.X("x:Q", scale=sc_x), y=alt.Y("y:Q", scale=sc_y), text="zone_name:N")
    layer_list = [*layers, pts, ring, lab]
    if zoom != "Whole floor":
        idl = alt.Chart(view).mark_text(dy=-14, fontSize=10, color=T.NAVY, clip=True).encode(
            x=alt.X("x:Q", scale=sc_x), y=alt.Y("y:Q", scale=sc_y), text="machine_id:N")
        layer_list.append(idl)
    ch = alt.layer(*layer_list).configure_legend(orient="top", symbolSize=110, labelFontSize=12, titleFontSize=12).properties(height=520)
    ev = st.altair_chart(ch, theme=None, width="stretch", on_select="rerun", selection_mode="pick", key="floor_map")
    sel_ids = [p.get("machine_id") for p in ((ev or {}).get("selection", {}) or {}).get("pick", []) if p.get("machine_id")]
    if sel_ids:
        _map_card(v, sel_ids[0])
    else:
        T.info("**Click any machine** on the map to see its verdict here; double-click to clear. Use the zone buttons to zoom in.")
    st.caption("Positions from the floor plan (floor_locations x/y; current spot for each machine). Hover a machine for its numbers. "
               "source: team/p2_verdicts.parquet; script: Bharath's notebook (p2).")


def _map_card(v: pd.DataFrame, mid: str):
    r = v[v.machine_id == mid]
    if r.empty:
        return
    r = r.iloc[0]
    import art
    gm = f"GM rank #{int(r.manager_rank)} &middot; " if r.in_manager_bottom10 else ""
    T.html_block(f'<div class="zoomcard" style="--vc:{T.VERDICT_COLOR.get(r.verdict, T.TEAL)}" role="status" aria-live="polite">'
                 f'{art.slot_machine(str(r.verdict))}<div><div class="id">{html.escape(mid)} &nbsp;{T.chip(r.verdict)}</div>'
                 f'<div class="why">{html.escape(str(r.reason))}</div>'
                 f'<div class="meta">{gm}{html.escape(str(r.zone_name))} &middot; casino win {usd(r.house_win_usd)} vs expected {usd(r.theo_usd)} '
                 f'&middot; luck pct {r.luck_score:.1%}</div></div>'
                 f'<a href="machine_details?m={html.escape(mid)}" target="_self">Open case file &rarr;</a></div>')


def _zone_evidence():
    z, b = team("p2_zone_index"), team("p2_b40_closure_effect")
    if z is None and b is None:
        return
    T.section("03", "Why the zone, not the machines", "Two independent checks: the same games earn less in Back Forty, "
              "and Back Forty's share of play fell while its walkway was closed, then recovered.")
    c1, c2 = st.columns(2, gap="large")
    if z is not None:
        lo = z.sort_values("zone_index_vs_floor").iloc[0]
        zz = z.assign(flag=z.zone_name.eq(lo.zone_name).map({True: "Lowest", False: "Other zones"}))
        with c1:
            T.takeaway(f"{lo.zone_name} earns {lo.zone_index_vs_floor:.0%} of the floor rate for the same games, the lowest of {len(z)} zones.")
            base = alt.Chart(zz).encode(y=alt.Y("zone_name:N", sort=list(zz.sort_values("zone_index_vs_floor").zone_name), title=None))
            bars_ = base.mark_bar(height=18).encode(
                x=alt.X("zone_index_vs_floor:Q", title="Earnings vs floor rate, same games (100% = floor)", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1.3])),
                color=alt.Color("flag:N", scale=alt.Scale(domain=["Lowest", "Other zones"], range=[T.OKABE_ITO[1], T.NAVY]), legend=None),
                tooltip=[alt.Tooltip("zone_name:N", title="Zone"), alt.Tooltip("zone_index_vs_floor:Q", title="vs floor", format=".0%")])
            txt = base.mark_text(align="left", dx=4, color=T.NAVY, fontWeight=600).encode(x="zone_index_vs_floor:Q", text=alt.Text("zone_index_vs_floor:Q", format=".0%"))
            rule = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(color=T.TEAL_DARK, strokeDash=[4, 3], size=2).encode(x="x:Q")
            T.altair(bars_ + txt + rule, height=280)
            st.caption("Dashed line = the floor rate. Bar labels carry the value; the lowest zone is also named in the takeaway.")
    if b is not None:
        bb = b.copy()
        bb["Period"] = bb.period.str[2:].str.strip().str.capitalize()
        with c2:
            k = list(bb.Period)
            if len(k) == 3:
                T.takeaway(f"Back Forty earned {bb.b40_vs_rest.iloc[0]:.0%} of the rest of the floor before the walkway closure, "
                           f"{bb.b40_vs_rest.iloc[1]:.0%} during it and {bb.b40_vs_rest.iloc[2]:.0%} after.")
            enc = dict(x=alt.X("Period:N", sort=k, title=None, axis=alt.Axis(labelAngle=0)),
                       y=alt.Y("b40_vs_rest:Q", title="Back Forty vs rest of floor", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])))
            ln = alt.Chart(bb).mark_line(color=T.NAVY, strokeWidth=3, point=alt.OverlayMarkDef(size=140, filled=True, color=T.NAVY)).encode(
                **enc, tooltip=[alt.Tooltip("Period:N"), alt.Tooltip("b40_vs_rest:Q", title="vs rest", format=".0%")])
            lb = alt.Chart(bb).mark_text(dy=-16, fontSize=15, fontWeight=800, color=T.NAVY).encode(**enc, text=alt.Text("b40_vs_rest:Q", format=".0%"))
            T.altair(ln + lb, height=280)
            st.caption("Expected win per available hour in Back Forty divided by the rest of the floor, before / during / after the closure "
                       "(100% = same as the rest). A dip while access was cut points to location.")
    with st.expander("Zone and closure tables"):
        if z is not None:
            show(z, {"zone_name": ("Zone", "text"), "machines": ("Machines", "int"), "zone_index_vs_floor": ("Earnings vs floor", "pct"),
                     "theo_per_hour_usd": ("Expected win per hour", "usd"), "avg_occupancy": ("Seats used", "pct")})
        if b is not None:
            show(b, {"period": ("Period", "text"), "b40_theo_per_hour": ("Back Forty expected win per hour", "usd"),
                     "rest_theo_per_hour": ("Rest of floor", "usd"), "b40_vs_rest": ("Back Forty vs rest", "pct")})
    source("team/p2_zone_index.parquet, team/p2_b40_closure_effect.parquet", "Bharath's notebook (p2)", "Full period; closure split as published by the team")


def budget_section(sel):
    T.section("04", "The $100,000 plan", "Pick up to 3 action types from the team's proposals. Costs are recomputed with the guide formula; "
              "the meter enforces the budget. Keeping money is a valid answer.")
    q6, _ = load("min_q6.parquet")
    props, cat = None, None
    try:
        cat = budget.catalog()
        props = budget.load_proposals(cat=cat)
        props = props[props.action_type_id.notna()].reset_index(drop=True) if len(props) else None
    except Exception as e:  # never break the page over the builder
        st.caption(f"Team proposals could not be loaded ({type(e).__name__}).")
    if props is not None and len(props):
        st.caption("Options come from the team's action files, with their own benefit ranges. Ranges are the teams' estimates, not guarantees.")
        lab = lambda i: (f"{props.source[i][:2].upper()} | {cat.loc[props.action_type_id[i], 'name']} x{int(props.quantity[i])} | "
                         f"cost {usd(props.cost_recomputed_usd[i])} | benefit {usd(props.expected_benefit_usd[i])} "
                         f"({usd(props.low_estimate_usd[i])} to {usd(props.high_estimate_usd[i])})")
        pick = st.multiselect("Pick lines to fund", list(props.index), format_func=lab)
        if pick:
            chosen = props.loc[pick]
            cost = float(chosen.cost_recomputed_usd.sum())
            for e in budget.check_plan(chosen, cat):
                st.error(e)
            for r in chosen.itertuples():
                if r.issues:
                    st.warning(f"{cat.loc[r.action_type_id, 'name']}: {r.issues}")
            show(chosen.assign(name=chosen.action_type_id.map(cat["name"])),
                 {"source": ("From", "text"), "name": ("Action", "text"), "quantity": ("Quantity", "int"), "targets": ("Targets", "text"),
                  "cost_recomputed_usd": ("Cost", "usd"), "expected_benefit_usd": ("Expected benefit", "usd"),
                  "low_estimate_usd": ("Low", "usd"), "high_estimate_usd": ("High", "usd"), "confidence": ("Confidence", "text"),
                  "how_to_measure": ("How we would know it worked", "text")})
            T.meter(cost, 100000, chosen.action_type_id.nunique())
            c = st.columns(2)
            c[0].metric("Expected benefit (30 days)", usd(chosen.expected_benefit_usd.sum()))
            c[1].metric("Benefit range", f"{usd(chosen.low_estimate_usd.sum())} to {usd(chosen.high_estimate_usd.sum())}")
            st.caption("Benefit and range are simple sums of the teams' 30-day estimates (the range assumes every line lands low or high together).")
            st.markdown("**Evidence for each line** (open below; the page link goes deeper):")
            vv = team("p2_verdicts")
            for t in dict.fromkeys(chosen.action_type_id):
                nm = cat.loc[t, "name"]
                tgt = EVIDENCE.get(t, "Machine Details")
                if tgt in PAGE_OBJ:
                    st.page_link(PAGE_OBJ[tgt], label=f"{nm}: see {tgt}")
                ids = [m for tl in chosen[chosen.action_type_id == t].targets for m in re.findall(r"M-\d+", str(tl))]
                if vv is not None and ids:
                    show(vv[vv.machine_id.isin(ids)], {"machine_id": ("Target machine", "text"), "zone_name": ("Zone", "text"), "verdict": ("Verdict", "verdict"),
                         "luck_score": ("Luck percentile", "pct"), "reason": ("Why", "text")}, wrap=True)
                evidence(EVID_Q.get(t, ["Q1"]), title=f"Evidence for {nm}", expanded=True)
            pb = budget.payback(chosen)
            if pb.empty and (props.action_type_id.isin(budget.PERMANENT)).any():
                pb, note = budget.payback(props), "No permanent action picked yet: showing the team's proposed ones."
            else:
                note = ""
            if not pb.empty:
                st.markdown("**Payback after 30 days (sensitivity)** " + note)
                st.warning("Assumption beyond the guide's 30-day window, not part of the scored plan: a moved machine or an inspection keeps its "
                           "30-day benefit every month at the same size (no decay, no extra cost). Real benefits may fade or never repeat.")
                pb = pb.assign(name=pb.action_type_id.map(cat["name"]), pay=pb.months_to_pay_back.map(lambda m: "does not pay back" if pd.isna(m) else f"{m:.1f} months"),
                               n3=pb.apply(lambda r: f"{usd(r.net_3m_expected)} ({usd(r.net_3m_low)} to {usd(r.net_3m_high)})", axis=1),
                               n6=pb.apply(lambda r: f"{usd(r.net_6m_expected)} ({usd(r.net_6m_low)} to {usd(r.net_6m_high)})", axis=1))
                show(pb, {"name": ("Action", "text"), "cost_recomputed_usd": ("One-time cost", "usd"), "expected_benefit_usd": ("Benefit in first 30 days", "usd"),
                          "pay": ("Pays back after", "text"), "n3": ("Net after 3 months: expected (low to high)", "text"),
                          "n6": ("Net after 6 months: expected (low to high)", "text")})
        else:
            T.meter(0, 100000, 0)
        source("team/p1_actions, p2_actions, p3_actions + min_q6.parquet", "teams' notebooks + src/budget.py", "30 days from 2025-07-01")
    if q6 is not None:
        with st.expander("Or build your own from the catalogue (prices only, no benefit estimate)", expanded=props is None):
            _catalogue_builder(q6)


def details(sel):
    v = team("p2_verdicts")
    if v is None:
        st.warning("Team verdict file is pending; showing the minimum version.")
        return _details_min(sel)
    vb = v if sel["bank"] == ALL else v[v.bank_id == sel["bank"]]
    if sel["bank"] != ALL:
        st.markdown(f"**Bank {sel['bank']}: {len(vb)} machines** (change the bank in the sidebar)")
        show(vb.sort_values("house_win_usd"), {"machine_id": ("Machine", "text"), "zone_name": ("Zone", "text"), "verdict": ("Verdict", "verdict"),
             "house_win_usd": ("Casino win, full period", "usd"), "luck_score": ("Luck percentile", "pct")})
    order = pd.concat([vb[vb.in_manager_bottom10].sort_values("manager_rank"), vb[~vb.in_manager_bottom10].sort_values("machine_id")])
    names = dict(zip(order.machine_id, order.machine_id + "  -  " + order.verdict + (np_where(order) )))
    ids = list(order.machine_id)
    want = st.query_params.get("m")
    mid = st.selectbox("Machine (the GM's 10 first)", ids, index=ids.index(want) if want in ids else 0, format_func=lambda m: names[m])
    r = v[v.machine_id == mid].iloc[0]
    peer = r.theo_per_hour_usd / r.peer_theo_per_hour_usd if r.peer_theo_per_hour_usd else float("nan")
    avail = r.availability_pct if r.availability_pct <= 1.5 else r.availability_pct / 100  # p2 file stores a fraction
    checks = [
        ("Luck", f"{r.luck_score:.1%} of fair replays over its {int(r.days_on_floor)} days on the floor did this badly or worse", luck_result(r.luck_score)),
        ("Short time on the floor", f"{int(r.days_on_floor)} of 181 days", "Supported" if r.days_on_floor < 150 else "Not supported"),
        ("Location", f"its zone earns {r.zone_index:.0%} of the floor rate for the same games", "Supported" if r.zone_index < 0.85 else "Not supported"),
        ("The machine or its game", f"earns {peer:.0%} of same-game peers per available hour", "Supported" if peer < 0.8 else "Not supported"),
        ("Downtime", f"{avail:.1%} of scheduled time available", "Supported" if avail < 0.9 else "Not supported"),
    ]
    rank = f"GM rank #{int(r.manager_rank)} &middot; " if r.in_manager_bottom10 else ""
    left, right = st.columns([5, 7], gap="large")
    with left:
        import art
        T.html_block(f'<div class="case">{art.slot_machine(str(r.verdict))}<div class="sub">{rank}{html.escape(str(r.zone_name))} &middot; bank {html.escape(str(r.bank_id))} &middot; '
                     f'{html.escape(str(r.theme))}</div><p class="id">{html.escape(mid)}</p>'
                     f'<div style="margin-top:8px">{T.chip(r.verdict)} &nbsp;<span style="color:{T.MUTED};font-size:.85rem">{html.escape(str(r.confidence).lower())} confidence</span></div>'
                     f'<p class="why">{html.escape(str(r.reason))}</p></div>')
        T.takeaway("Competing explanations tested (full period)")
        T.checklist(checks)
        st.caption("Luck: Supported at 20% or more, Unlikely at 1-20%, Not supported below 1%. Each row shows a symbol and a word, never colour alone.")
    with right:
        c = st.columns(2)
        c[0].metric("Casino win (all 6 months)", usd(r.house_win_usd))
        c[1].metric("Expected win (theo)", usd(r.theo_usd))
        c = st.columns(2)
        c[0].metric("Days on floor", f"{int(r.days_on_floor)}")
        c[1].metric("Luck percentile", f"{r.luck_score:.1%}")
    sims = team("p2_luck_sims")
    if sims is not None:
        s = sims[sims.machine_id == mid]
        if len(s):
          with right:
            T.takeaway(f"None of the 10,000 fair replays did as badly as {mid}'s actual result." if r.luck_score == 0
                       else f"Only {r.luck_score:.1%} of fair replays did as badly as {mid}'s actual result.")
            hist = alt.Chart(s).mark_bar(color=T.TEAL, opacity=0.55).encode(
                x=alt.X("sim_house_win_usd:Q", bin=alt.Bin(maxbins=30), title=f"Simulated casino win over its time on the floor ({int(r.days_on_floor)} days) ($)"),
                y=alt.Y("count()", title="Simulations (of 500)"))
            marks = pd.DataFrame({"x": [r.house_win_usd, r.theo_usd], "Line": ["Actual result", "Expected (theo)"]})
            rules = alt.Chart(marks).mark_rule(size=3).encode(
                x="x:Q", color=alt.Color("Line:N", scale=alt.Scale(domain=["Actual result", "Expected (theo)"], range=[T.OKABE_ITO[3], T.NAVY]),
                                         legend=alt.Legend(title="Legend", orient="top")),
                strokeDash=alt.StrokeDash("Line:N", scale=alt.Scale(domain=["Actual result", "Expected (theo)"], range=[[1, 0], [5, 4]]), legend=None))
            T.altair(hist + rules)
            st.caption(f"Luck percentile comes from 10,000 fair replays per machine run in Databricks (Spark); this chart shows a 500-replay sample "
                       f"for a normal copy of this machine over the same {int(r.days_on_floor)} days it was on the floor. "
                       "If the actual line sits far left of the bars, luck alone is a poor explanation.")
    mv = team("p2_move_effects")
    if mv is not None and (mv.machine_id == mid).any():
        st.markdown("**This machine was moved**")
        show(mv[mv.machine_id == mid], {"move_date": ("Moved on", "date"), "from_zone": ("From", "text"), "to_zone": ("To", "text"),
             "days_after": ("Days observed after", "int"), "theo_per_hour_before": ("Expected win per hour before", "usd"),
             "theo_per_hour_after": ("After", "usd"), "change_pct": ("Change", "pct"), "adjusted_change_pct": ("Change vs unmoved floor", "pct")})
    elif mv is not None:
        st.caption(f"Not moved. Only {len(mv)} machines moved in the period, so move evidence is thin.")
    dt = team("p1_downtime")
    if dt is not None:
        m = dt[dt.machine_id == mid]
        h = (m.scheduled_hours - m.available_hours).sum()
        st.markdown(f"**Downtime:** {h:,.0f} hours down in 6 months ({h / m.scheduled_hours.sum():.2%} of scheduled), expected win lost at most {usd(m.lost_theo_usd.sum())}.")
        mm = m[m.cause != "none"]
        if len(mm):
            show(mm.groupby("cause").agg(days=("gaming_date", "count"), lost=("lost_theo_usd", "sum")).reset_index(),
                 {"cause": ("Cause", "text"), "days": ("Days affected", "int"), "lost": ("Expected win lost", "usd")})
    md = machine_day(sel)
    if md is not None:
        mw = md[md.machine_id == mid]
        if len(mw):
            w = mw.assign(week=pd.to_datetime(mw.gaming_date).dt.to_period("W-SUN").dt.start_time).groupby("week")[["house_win_usd", "theo_usd"]].sum()
            st.caption("Weekly casino win vs expected win (dollars per week), selected period")
            T.takeaway(f"Over this selection the machine won {usd(w.house_win_usd.sum())} against {usd(w.theo_usd.sum())} expected.")
            T.line(w.rename(columns={"house_win_usd": "Casino win ($)", "theo_usd": "Expected win ($)"}), "week", ["Casino win ($)", "Expected win ($)"], "Week starting", "Dollars per week")
    st.caption("Verdict, reason and luck chance are for the full period (only scope precomputed). Downtime and the chart follow the period filter where noted.")
    source("team/p2_verdicts, p2_luck_sims, p2_move_effects, p1_downtime + min_machine_day.parquet", "Bharath/Aditi notebooks + " + SCRIPT, "Full (Jan-Jun) unless stated")
    evidence(["Q1", "Q3"], machine=mid, title=f"Evidence mentioning {mid} first, then Q1 and Q3 claims")


def np_where(df):
    return pd.Series(" (GM rank " + df.manager_rank.astype("Int64").astype(str) + ")", index=df.index).where(df.in_manager_bottom10, "").values


def demand(sel):
    dem, dt = team("p3_demand"), team("p1_downtime")
    if dem is None and dt is None:
        st.warning("Team demand and downtime files are pending; showing the minimum version.")
        return _demand_min(sel)
    top = st.container()
    chg, nclues = "n/a", "n/a"
    if dem is not None:
        dd = dem[(dem.gaming_date >= pd.Timestamp(sel["start"])) & (dem.gaming_date <= pd.Timestamp(sel["end"]))]
        day = dd.groupby("gaming_date").agg(coin_in_usd=("coin_in_usd", "sum"), traffic=("traffic_count", "sum"),
                                            counted=("traffic_count", lambda x: x.notna().sum()), zones=("zone_id", "count")).reset_index()
        ev = dd.dropna(subset=["event_name"]).groupby("gaming_date").event_name.agg(lambda x: "; ".join(sorted(set(x)))).reset_index()
        wk = _full_weeks(day.merge(ev, how="left", on="gaming_date"), sel["start"], sel["end"])
        if wk.empty:
            T.info("No complete Monday-Sunday week fits inside this range; widen it to see the weekly trend.")
        else:
            w = wk.groupby("week_start").agg(coin_in_usd=("coin_in_usd", "sum"), traffic=("traffic", "sum"), counted=("counted", "sum"),
                                             zones=("zones", "sum"), events=("event_name", lambda x: "; ".join(sorted(set("; ".join(x.dropna()).split("; ")) - {""})))).reset_index()
            w["coverage"] = w.counted / w.zones
            head = "Weekly coin-in"
            if len(w) >= 8:
                a, b = w.head(4).coin_in_usd.mean(), w.tail(4).coin_in_usd.mean()
                chg = f"{b / a - 1:+.1%}"
                head = f"Weekly coin-in changed {b / a - 1:+.1%} from the first 4 to the last 4 complete weeks in this range"
            st.header(head)
            T.line(w.set_index("week_start")[["coin_in_usd"]].rename(columns={"coin_in_usd": "Weekly coin-in ($)"}), "week_start", ["Weekly coin-in ($)"], "Week starting", "Money wagered per week ($)")
            with st.expander(f"Weekly numbers, with events ({len(w)} complete weeks)"):
                show(w, {"week_start": ("Week starting", "date"), "coin_in_usd": ("Money wagered", "usd"), "traffic": ("Door entries counted", "int"),
                         "coverage": ("Door counters online", "pct"), "events": ("Events that week", "text")})
            st.caption("Whole floor, all 7 zones (bank filter does not apply). Only complete Monday-Sunday weeks inside the range. "
                       "Entries are door counts, not unique visitors; a missing counter reading is offline, not zero, and is excluded (see coverage).")
        vz = team("p2_verdicts")
        zname = dict(zip(vz.zone_id, vz.zone_name)) if vz is not None else {}
        zz = dd.assign(zone_id=dd.zone_id.map(lambda z: zname.get(z, z))).groupby("zone_id").coin_in_usd.sum().sort_values()
        T.takeaway(f"{zz.idxmax()} draws the most play: {usd(zz.max())} wagered in this selection.")
        T.bars(zz.rename("Money wagered ($)").rename_axis("zone").reset_index(), "zone", "Money wagered ($)", "Zone", "Money wagered in selection ($)", height=260)
        source("team/p3_demand.parquet", "Nikita's notebook (p3)", f"{sel['preset']}, floor-wide")
        evidence(["Q2"], title="Evidence: Q2 claims on what changed in demand")
    else:
        st.warning("Team demand file is pending; showing the minimum demand view.")
    st.divider()
    if dt is None:
        return _demand_min(sel)
    x = dt[(dt.gaming_date >= pd.Timestamp(sel["start"])) & (dt.gaming_date <= pd.Timestamp(sel["end"]))]
    if sel["bank"] != ALL:
        x = x[x.bank_id == sel["bank"]]
    hrs = (x.scheduled_hours - x.available_hours).sum()
    st.header(f"Downtime cost at most {usd(x.lost_theo_usd.sum())} of expected win ({hrs:,.0f} hours down, {hrs / max(x.scheduled_hours.sum(), 1):.2%} of scheduled)")
    st.caption("Upper bound: hours down x the machine's own expected win per available hour; guests may play elsewhere. "
               f"Scope: {sel['preset']}, bank {sel['bank']}.")
    x = x.assign(month=pd.to_datetime(x.gaming_date).dt.strftime("%Y-%m"))
    pv = x.pivot_table(index="month", columns="manufacturer", values="lost_theo_usd", aggfunc="sum").fillna(0)
    pv.index = [pd.Timestamp(m + "-01").strftime("%b") for m in pv.index]
    pv.index.name = "month"
    if len(pv):
        T.bars(pv, "month", list(pv.columns), "Month", "Expected win lost to downtime ($)")
    c1, c2 = st.columns(2)
    with c1:
        show(x.groupby("manufacturer").agg(h=("available_hours", "count"), lost=("lost_theo_usd", "sum")).reset_index().assign(
            hours=x.groupby("manufacturer").apply(lambda g: (g.scheduled_hours - g.available_hours).sum(), include_groups=False).values),
             {"manufacturer": ("Manufacturer", "text"), "hours": ("Hours down", "int"), "lost": ("Expected win lost", "usd")})
    with c2:
        cz = x[x.cause != "none"].assign(cause=lambda q: q.cause.str.replace("_", " ").str.capitalize()).groupby("cause").agg(days=("gaming_date", "count"), lost=("lost_theo_usd", "sum")).reset_index()
        show(cz, {"cause": ("Cause", "text"), "days": ("Machine-days affected", "int"), "lost": ("Expected win lost", "usd")})
    lc = team("p1_leak_clues")
    if lc is not None:
        banks = dt.drop_duplicates("machine_id").set_index("machine_id").bank_id
        l = lc[(lc.gaming_date >= pd.Timestamp(sel["start"])) & (lc.gaming_date <= pd.Timestamp(sel["end"]))]
        if sel["bank"] != ALL:
            l = l[l.machine_id.map(banks) == sel["bank"]]
        nclues = f"{len(l)}"
        st.markdown(f"**Leak clues in this selection: {len(l)} on {l.machine_id.nunique()} machines.** These are leads to inspect, not accusations.")
        if len(l):
            show(l.assign(rule_failed=l.rule_failed.str.replace("_", " ").str.replace("rtp", "RTP").str.capitalize()).groupby("rule_failed").agg(n=("machine_id", "count"), m=("machine_id", "nunique")).reset_index(),
                 {"rule_failed": ("Rule that flagged it", "text"), "n": ("Flags", "int"), "m": ("Machines", "int")})
    source("team/p1_downtime.parquet, team/p1_leak_clues.parquet", "Aditi's notebook (p1)", f"{sel['preset']}, bank {sel['bank']}")
    evidence(["Q3"], title="Evidence: Q3 claims on downtime")
    with top:
        T.kpis([("Coin-in, last 4 vs first 4 full weeks", chg), ("Hours down", f"{hrs:,.0f}"),
                ("Expected win lost, upper bound", usd(x.lost_theo_usd.sum())), ("Leak clues", nclues)])


def players(sel):
    p = team("p3_players")
    if p is None:
        st.warning("Team player file is pending; showing the minimum version.")
        return _players_min(sel)
    ms = snap_months(sel)
    top = st.container()
    kp = [("Wagered", "n/a"), ("Won back", "n/a"), ("Players' net", "n/a"), ("Comp cost", "n/a")]
    c1, c2 = st.columns(2)
    ages = c1.radio("Age band", [ALL] + sorted(p.age_band.dropna().unique()), horizontal=True)
    regs = c2.radio("Home region", [ALL] + sorted(p.home_region.dropna().unique()), horizontal=True)
    x = p[p.month.isin(ms)]
    for col, val in (("tier", sel["tier"]), ("age_band", ages), ("home_region", regs)):
        if val != ALL:
            x = x[x[col] == val]
    if x.empty:
        T.info("No guest group of 10 or more players matches these filters.")
    else:
        st.header(f"Tracked players wagered {usd(x.wagered_usd.sum())}, won back {usd(x.won_back_usd.sum())}, net {usd(x.net_usd.sum())}")
        st.caption(f"{int(x.player_count.sum()):,} player-months in groups of 10+. Net = won back minus wagered (opposite sign of casino win). "
                   "Carded play only. Individual players are never shown.")
        kp[0:3] = [("Wagered", T.money_short(x.wagered_usd.sum()), usd(x.wagered_usd.sum())), ("Won back", T.money_short(x.won_back_usd.sum()), usd(x.won_back_usd.sum())),
                   ("Players' net", T.money_short(x.net_usd.sum()), usd(x.net_usd.sum()))]
        mo = x.groupby("month").agg(w=("wagered_usd", "sum"), b=("won_back_usd", "sum"), n=("net_usd", "sum"), pc=("player_count", "sum")).reset_index()
        T.bars(mo, "month", "n", "Month", "Players' net, wins minus losses ($)", color=T.NAVY)
        show(mo, {"month": ("Month", "month"), "pc": ("Player-months", "int"), "w": ("Wagered", "usd"), "b": ("Won back", "usd"), "n": ("Players' net", "usd")})
    cn = team("p3_concentration")
    if cn is not None:
        st.subheader("How concentrated are the losses?")
        lz = pd.concat([pd.DataFrame({"top_pct": [0.0], "share_of_net_loss": [0.0]}), cn.sort_values("top_pct")]).assign(equal=lambda d: d.top_pct / 100)
        long = lz.melt("top_pct", value_vars=["share_of_net_loss", "equal"], var_name="Line", value_name="share")
        long["Line"] = long.Line.map({"share_of_net_loss": "Actual: share of all net losses", "equal": "If losses were spread evenly"})
        names = ["Actual: share of all net losses", "If losses were spread evenly"]
        ch = alt.Chart(long).mark_line(point=True).encode(
            x=alt.X("top_pct:Q", title="Top share of tracked players, ranked by loss (%)"), y=alt.Y("share:Q", title="Share of total net loss", axis=alt.Axis(format="%")),
            color=alt.Color("Line:N", scale=alt.Scale(domain=names, range=[T.OKABE_ITO[3], T.NAVY]), legend=alt.Legend(title="Legend", orient="top")),
            strokeDash=alt.StrokeDash("Line:N", scale=alt.Scale(domain=names, range=[[1, 0], [5, 4]]), legend=None))
        t10 = cn[cn.top_pct == 10].share_of_net_loss
        if len(t10):
            T.takeaway(f"The 10% of tracked players with the largest losses account for {t10.iloc[0]:.0%} of all net losses.")
        T.altair(ch)
        if len(t10):
            st.caption(f"Shares above 100% appear "
                       "because the remaining players, as a group, won money. Full period, all tracked players (filters do not apply).")
        source("team/p3_concentration.parquet", "Nikita's notebook (p3)", "Full period, all tracked players")
    source("team/p3_players.parquet", "Nikita's notebook (p3)", f"months {ms[0]}..{ms[-1]}, tier {sel['tier']}, age {ages}, region {regs}")
    evidence(["Q4"], title="Evidence: Q4 claims on player results")
    st.divider()
    cp = team("p1_comps")
    if cp is None:
        with top:
            T.kpis(kp)
        return
    cc = cp[cp.month.isin(ms)]
    if sel["tier"] != ALL:
        cc = cc[cc.tier == sel["tier"]]
    mq5, _ = load("min_q5.parquet")
    kp[3] = ("Comp cost", usd(cc.comp_cost_usd.sum()))
    with top:
        T.kpis(kp)
    st.header(f"Comps cost the casino {usd(cc.comp_cost_usd.sum())} in this selection")
    st.caption("Comp cost is cost to the house, already inside POS cost of goods: counted once. Age and region filters do not apply to comps.")
    pv = cc.pivot_table(index="month", columns="tier", values="comp_cost_usd", aggfunc="sum")
    if len(pv):
        T.bars(pv, "month", list(pv.columns), "Month", "Comp cost to the casino ($)")
    show(cc.groupby("month").agg(c=("comp_cost_usd", "sum"), e=("points_earned", "sum"), r=("points_redeemed", "sum")).reset_index(),
         {"month": ("Month", "month"), "c": ("Comp cost", "usd"), "e": ("Points earned", "int"), "r": ("Points redeemed", "int")})
    if mq5 is not None:
        q = mq5[mq5.month.isin(ms)]
        if sel["tier"] != ALL:
            q = q[q.tier == sel["tier"]]
        r = q.groupby("month")[["comp_cost_usd", "theo_usd"]].sum()
        rr = r.comp_cost_usd / r.theo_usd
        if len(rr) > 1:
            T.takeaway(f"Comp cost was {rr.iloc[0]:.2%} of expected win in {rr.index[0]} and {rr.iloc[-1]:.2%} in {rr.index[-1]}.")
        T.line((r.comp_cost_usd / r.theo_usd).rename("Comp cost / expected win").to_frame(), "month", ["Comp cost / expected win"], "Month", "Comp cost / expected win", fmt=".1%")
        st.caption("Reinvestment ratio from the minimum version's player table (comp cost / expected win); the team comps file has no expected-win column.")
    source("team/p1_comps.parquet + min_q5.parquet", "Aditi's notebook (p1) + " + SCRIPT, f"months {ms[0]}..{ms[-1]}, tier {sel['tier']}")
    evidence(["Q5"], title="Evidence: Q5 claims on comps")


def model_plan(sel):
    fr, mm, tm = team("p3_forecast_results"), team("p3_model_metrics"), tfind("model")
    if fr is None or mm is None or tm is None:
        st.warning("Team forecast files are pending; showing the minimum version.")
        return _model_min(sel)
    best = mm.sort_values("mae_usd").iloc[0]
    bmae = mm[mm.model_name.str.startswith("baseline")].mae_usd.iloc[0]
    T.kpis([("Model average miss per day", usd(best.mae_usd)), ("Constant baseline miss per day", usd(bmae)),
            ("Improvement over baseline", f"{1 - best.mae_usd / bmae:.0%}"), ("Test days (May to Jun)", f"{tm['test_days']}")])
    st.header(f"{best.model_name.replace('_', ' ').capitalize()} misses by {usd(best.mae_usd)} a day on May-June, against {usd(mm[mm.model_name.str.startswith('baseline')].mae_usd.iloc[0])} for the constant baseline")
    st.caption(f"Train {tm['train']}, test {tm['test']} ({tm['test_days']} days), split by time; models frozen before testing; no later-published data used. "
               "Fixed dates, unaffected by the sidebar filters. The forecast file's own predictions reproduce "
               f"{usd(tm['forecast_mae_model_usd'])} (model: {tm['forecast_file_model_is'].replace('_', ' ')}) and {usd(tm['forecast_mae_baseline_usd'])} (baseline).")
    show(mm.sort_values("mae_usd").assign(model_name=lambda q: q.model_name.str.replace("_", " ").str.capitalize()), {"model_name": ("Model", "text"), "mae_usd": ("Average miss per day (MAE)", "usd"), "mlflow_run_id": ("MLflow run ID", "text")})
    t = fr[fr.split == "test"][["gaming_date", "actual_usd", "model_pred_usd", "baseline_pred_usd"]].rename(columns={
        "actual_usd": "Actual", "model_pred_usd": "Model forecast", "baseline_pred_usd": "Constant baseline"})
    names = ["Actual", "Model forecast", "Constant baseline"]
    long = t.melt("gaming_date", var_name="Line", value_name="Dollars")
    chart = alt.Chart(long).mark_line().encode(
        x=alt.X("gaming_date:T", title="Day (May-Jun 2025)"), y=alt.Y("Dollars:Q", title="Daily money wagered ($)"),
        color=alt.Color("Line:N", scale=alt.Scale(domain=names, range=[T.NAVY, T.OKABE_ITO[0], T.OKABE_ITO[1]]), legend=alt.Legend(title="Legend", orient="top")),
        strokeDash=alt.StrokeDash("Line:N", scale=alt.Scale(domain=names, range=[[1, 0], [6, 3], [2, 2]]), legend=None))
    T.altair(chart)
    f = findings("model")
    if f:
        st.caption(f"Independent check: my minimum weekday-average model gives {usd(f['mae_model_usd'])}, matching the team's weekday_average row. "
                   f"Leak check: its weekday means use {f['leak_check']['train_rows']} Jan-Apr days; {f['leak_check']['test_rows_in_training']} May-Jun days enter training.")
    source("team/p3_forecast_results.parquet, team/p3_model_metrics.parquet", "Nikita's notebook (p3)", "test May-Jun 2025, floor daily coin-in $")
    evidence(["Model", "Pipeline"], title="Evidence: model and pipeline claims")
    q6, _ = load("min_q6.parquet")
    if q6 is not None:
        st.divider()
        st.subheader("Action catalogue with budget cost (guide formula)")
        show(q6, {"name": ("Action", "text"), "unit": ("Priced per", "text"), "quantity_limit": ("Most allowed", "int"),
                  "lead_days": ("Days to start", "int"), "operating_days": ("Days running in 30", "int"),
                  "cost_per_unit_usd": ("Cost per unit", "usd"), "max_cost_usd": ("Cost at the limit", "usd"),
                  "incompatibility_group": ("Cannot combine with others in group", "text")})
        st.caption("Lease example: $2,500 + 16 days x $55 = $3,380 per machine. Build a plan on the Overview page. Estimates come from the teams' action files.")
        source("min_q6.parquet", SCRIPT, "30 days from 2025-07-01")


def evidence_page(sel):
    c = team("all_claims")
    if c is None:
        st.warning("Pending: the merged claims table is not available yet.")
        return
    T.kpis([("Claims", f"{len(c)}"), ("Questions covered", f"{c.question.nunique()}"),
            ("High confidence", f"{int((c.confidence.str.lower() == 'high').sum())}")])
    qs = st.multiselect("Question", sorted(c.question.unique()), default=sorted(c.question.unique()))
    src = st.multiselect("From", sorted(c.source.unique()), default=sorted(c.source.unique()))
    x = c[c.question.isin(qs) & c.source.isin(src)]
    st.subheader(f"{len(x)} claims. Each lists the alternative explanation that was tested and its limitation.")
    show(x, {"claim_id": ("ID", "text"), "question": ("Question", "text"), "claim": ("Claim", "text"), "result": ("Result", "text"),
             "alternative_tested": ("Alternative explanation tested", "text"), "limitation": ("Limitation", "text"),
             "confidence": ("Confidence", "text"), "evidence_table": ("Evidence table", "text"), "source": ("From", "text")}, wrap=True)
    source("team/all_claims.parquet", "src/integrate_team.py (merge of p1/p2/p3_claims)", "all questions")
