"""Page bodies. Headline numbers come from app_data/findings/minimum.json; filtered tables are recomputed live."""
import pandas as pd
import streamlit as st
import altair as alt
from common import ALL, findings, load, machine_day, machine_totals, show, snap_months, source, usd

BLUE, ORANGE = "#0072B2", "#E69F00"  # colourblind-safe pair
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


def overview(sel):
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
    st.info(f"**Answer in brief.** Of the GM's 10 lowest machines, {lb.get('Location', 0)} sit in a weak zone ({z['zone']} earns "
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
             "days_on_floor": ("Days on floor (all 6 months)", "int"), "house_win_usd": ("Casino win, selected period", "usd"),
             "luck_residual_usd": ("Win vs expected (luck), selected period", "usd"),
             "availability": ("Time available, selected period", "pct"),
             "theo_per_avail_hour": ("Expected win per hour available, selected period", "usd"),
             "zone_index": ("Zone earnings vs typical zone", "pct"), "config_index": ("Earnings vs same game elsewhere", "pct"),
             "occupancy_vs_zone": ("Seats used vs zone", "pct"), "label": ("Likely cause", "text"), "label_reason": ("Why", "text")})
    if not full_scope:
        st.info("Money, availability and theo columns follow your filters. Labels, indices and reasons are full-period "
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

    st.divider()
    st.header("$100,000 budget builder")
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


def details(sel):
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
        st.line_chart(w.rename(columns={"house_win_usd": "Casino win ($)", "theo_usd": "Expected win ($)"}), color=[ORANGE, BLUE],
                      x_label="Week starting", y_label="Dollars per week")
    else:
        st.info("This machine has no active days in the selected period/bank.")
    st.caption("Verdict wording is minimum-version rules; 'not enough evidence' (Mixed) is an allowed answer. Peer comparison "
               "uses same-config machines (leave-one-out median); no confidence interval yet.")
    source("min_q1.parquet + min_machine_day.parquet", SCRIPT, "labels: Full (Jan-Jun); chart: " + sel["preset"])


def demand(sel):
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
        st.info("No complete Monday-Sunday week fits inside this range; widen it to see the weekly trend.")
    else:
        st.line_chart(ww.set_index("week_start")[["coin_in_usd"]].rename(columns={"coin_in_usd": "Weekly coin-in ($)"}), color=[BLUE],
                      x_label="Week starting", y_label="Money wagered per week ($)")
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
    st.bar_chart(p, x_label="Week starting", y_label="Expected win lost to downtime ($)")
    show(d.groupby("manufacturer")[["downtime_hours", "lost"]].sum().reset_index(),
         {"manufacturer": ("Manufacturer", "text"), "downtime_hours": ("Hours down", "int"), "lost": ("Expected win lost", "usd")})
    source("min_machine_day.parquet", SCRIPT, f"{sel['preset']}, bank: {sel['bank']}")


def players(sel):
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
    st.bar_chart(agg[["net_usd"]].rename(columns={"net_usd": "Player net ($)"}), color=[ORANGE], x_label="Month", y_label="Player net, wins minus losses ($)")
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
    st.line_chart(cm[["Comp cost / theo"]].rename(columns={"Comp cost / theo": "Comp cost as share of expected win"}), color=[BLUE],
                  x_label="Month", y_label="Comp cost / expected win")
    show(c, {"month": ("Month", "month"), "tier": ("Loyalty tier", "text"), "players": ("Players", "int"), "comp_cost_usd": ("Comp cost to casino", "usd"),
             "comp_face_value_usd": ("Comp menu value (not cash)", "usd"), "theo_usd": ("Expected casino win", "usd"),
             "comp_cost_to_theo_ratio": ("Comp cost / expected win", "pct2"), "comps_redeemed": ("Comps redeemed", "int"),
             "points_earned": ("Points earned", "int"), "points_redeemed": ("Points redeemed", "int")})
    source("min_q5.parquet", SCRIPT, f"months {ms[0]}..{ms[-1]}, tier {sel['tier']}")


def model_plan(sel):
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
        color=alt.Color("Line:N", scale=alt.Scale(domain=names, range=["#000000", BLUE, ORANGE]), legend=alt.Legend(title="Legend", orient="top")),
        strokeDash=alt.StrokeDash("Line:N", scale=alt.Scale(domain=names, range=[[1, 0], [6, 3], [2, 2]]), legend=None))
    st.altair_chart(chart, width="stretch")
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
