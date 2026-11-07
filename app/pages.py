"""Page bodies. Headline numbers come from app_data/findings/minimum.json; filtered tables are recomputed live."""
import pandas as pd
import streamlit as st
from common import ALL, findings, load, machine_day, machine_totals, snap_months, source

BLUE, ORANGE = "#0072B2", "#E69F00"  # colourblind-safe pair
SCRIPT = "src/minimum.py"


def usd(x):
    return f"{'-' if x < 0 else ''}${abs(x):,.0f}"
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
    st.markdown("**The GM's list:** the 10 machines with the lowest total house win, Jan 1 to Jun 30, 2025. "
                "House win alone ignores luck, time on the floor and location, so each row is checked below.")
    live = machine_day(sel)
    b = q1[q1.gm_bottom10].copy()
    full_scope = sel["preset"].startswith("Full") and sel["bank"] == ALL
    if live is not None:
        t = machine_totals(live)[["machine_id", "house_win_usd", "luck_residual_usd", "availability", "theo_per_avail_hour"]]
        b = b[["machine_id", "zone_id", "config_id", "days_on_floor", "zone_index", "config_index", "occupancy_vs_zone", "label",
               "label_reason"]].merge(t, on="machine_id", how="left")
    st.dataframe(b.rename(columns={
        "house_win_usd": "House win $ (selected period)", "luck_residual_usd": "Luck residual $ (selected period)",
        "availability": "Availability (selected period)", "theo_per_avail_hour": "Theo $ per available hour (selected period)",
        "days_on_floor": "Days on floor (full period)", "zone_index": "Zone index (full)", "config_index": "Config index (full)",
        "occupancy_vs_zone": "Occupancy vs zone (full)", "label": "Label (full period)", "label_reason": "Why (full period)"}),
        hide_index=True, width="stretch")
    if not full_scope:
        st.info("Money, availability and theo columns follow your filters. Labels, indices and reasons are full-period "
                "(Jan-Jun, whole floor) and are not recomputed for this selection.")
    source("min_q1.parquet + min_machine_day.parquet", SCRIPT, "labels: Full (Jan-Jun); money columns: " + sel["preset"])
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
        st.dataframe(df.drop(columns="Group"), hide_index=True, width="stretch")
        if {"A-COMP-PILOT", "A-COMP-CHANGE"} <= set(pick):
            st.error("Incompatible: a comp pilot cannot run together with the floor-wide comp change.")
        if sum(1 for a in pick if acts.loc[a, "incompatibility_group"] == "same_machine") > 1:
            st.warning("Moves/replacements must target different machines (not checked here: targets are not chosen yet).")
        left = 100000 - total
        (st.error if left < 0 else st.success)(f"Spent ${total:,.0f}; remaining ${left:,.0f}" + (" (OVER BUDGET)" if left < 0 else ""))
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
    c[0].metric("House win (full period)", f"${r.house_win_usd:,.0f}")
    c[1].metric("Luck residual (full)", f"${r.luck_residual_usd:,.0f}")
    c[2].metric("Availability (full)", f"{r.availability:.1%}")
    c[3].metric("Days on floor", f"{int(r.days_on_floor)}")
    st.markdown("**Competing explanations tested** (full period)")
    st.table(pd.DataFrame([
        ["Luck", f"house win ${r.luck_residual_usd:,.0f} vs theo", "Supported" if r.luck_residual_usd < -0.1 * r.theo_usd else "Not the main cause"],
        ["Downtime", f"availability {r.availability:.1%}", "Not supported" if r.availability >= 0.9 else "Supported"],
        ["Location", f"zone {r.zone_id} earns {r.zone_index:.0%} of the typical zone", "Supported" if r.zone_index < 0.85 else "Not supported"],
        ["Game / config", f"{r.config_id}: machine earns {r.config_index:.0%} of same-config peers per available hour", "Supported" if r.config_index < 0.8 else "Not supported"],
        ["Moved?", "moved during the period" if r.moved_flag else "stayed in one place", "n/a" if not r.moved_flag else "Check before/after"],
        ["Players avoid it?", f"occupancy {r.occupancy_vs_zone:.0%} of zone median", "Not supported" if r.occupancy_vs_zone >= 0.85 else "Supported"],
    ], columns=["Explanation", "Evidence", "Result"]))
    m = md[md.machine_id == mid]
    if len(m):
        w = m.assign(week=pd.to_datetime(m.gaming_date).dt.to_period("W-SUN").dt.start_time).groupby("week")[["house_win_usd", "theo_usd"]].sum()
        st.caption("Weekly house win vs theo (dollars), selected period")
        st.line_chart(w.rename(columns={"house_win_usd": "House win $", "theo_usd": "Theo $"}), color=[ORANGE, BLUE])
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
    ww = w[(pd.to_datetime(w.week_start) >= pd.Timestamp(sel["start"]) - pd.Timedelta(days=6)) & (pd.to_datetime(w.week_start) <= pd.Timestamp(sel["end"]))]
    st.line_chart(ww.set_index("week_start")[["coin_in_usd"]].rename(columns={"coin_in_usd": "Weekly coin-in $"}), color=[BLUE])
    st.dataframe(ww[["week_start", "coin_in_usd", "theo_usd", "occupied_machine_hours", "entries", "counter_coverage_share", "events", "holidays"]],
                 hide_index=True, width="stretch")
    st.caption("Whole floor (bank filter does not apply). Weeks overlapping the range are shown, first/last may be partial. "
               "Entries are door counts, not unique visitors; missing counter hours are excluded (see coverage).")
    source("min_q2.parquet", SCRIPT, "weekly, floor-wide, " + sel["preset"])
    st.divider()
    d = d3.copy()
    d["downtime_hours"] = (d.scheduled_hours - d.available_hours).clip(lower=0)
    g = d.groupby("machine_id")
    d["lost"] = d.downtime_hours * d.machine_id.map(g.theo_usd.sum() / g.available_hours.sum())
    d["week"] = pd.to_datetime(d.gaming_date).dt.to_period("W-SUN").dt.start_time
    st.header(f"Downtime cost about ${d.lost.sum():,.0f} of theo ({d.downtime_hours.sum():,.0f} hours) in this selection")
    st.caption("Upper bound: downtime hours x the machine's own theo per available hour; guests may play elsewhere. "
               f"Full-period figure: ${f3['lost_theo_usd_upper_bound']:,.0f} lost theo, {f3['downtime_share_of_scheduled']:.2%} of scheduled hours.")
    p = d.pivot_table(index="week", columns="manufacturer", values="lost", aggfunc="sum").fillna(0)
    st.bar_chart(p)
    st.write(d.groupby("manufacturer")[["downtime_hours", "lost"]].sum().rename(columns={"lost": "lost theo $"}).round(0))
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
    st.header(f"Tracked players wagered ${t.wagered_usd.sum():,.0f}, got back ${t.paid_back_usd.sum():,.0f}, net {usd(t.net_usd.sum())}")
    st.caption("Player net = payout minus wager (opposite sign of house win). Carded play only. Groups of 10+ players. "
               f"Full-period concentration: the top 10% of {f4['tracked_players']:,} tracked players hold {f4['top10pct_share_of_theo']:.0%} of theo.")
    agg = t.groupby("month")[["wagered_usd", "paid_back_usd", "net_usd", "theo_usd"]].sum()
    st.bar_chart(agg[["net_usd"]].rename(columns={"net_usd": "Player net $"}), color=[ORANGE])
    st.dataframe(t, hide_index=True, width="stretch")
    source("min_q4.parquet", SCRIPT, f"months {ms[0]}..{ms[-1]}, tier {sel['tier']}")
    st.divider()
    cm = c.groupby("month")[["comp_cost_usd", "theo_usd"]].sum()
    cm["Comp cost / theo"] = cm.comp_cost_usd / cm.theo_usd.where(cm.theo_usd > 0)
    first, last = f5["ratio_by_month"]["2025-01"], f5["ratio_by_month"]["2025-06"]
    st.header(f"Comps cost ${c.comp_cost_usd.sum():,.0f} here; comp cost / theo went {first:.2%} (Jan) to {last:.2%} (Jun)")
    st.caption("Comp cost is cost to the house, already inside POS cost of goods: counted once. Reinvestment = comp cost / theo. "
               "Why it changed is not yet tested.")
    st.line_chart(cm[["Comp cost / theo"]], color=[BLUE])
    st.dataframe(c, hide_index=True, width="stretch")
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
    st.header(f"Weekday-average forecast {verdict} the constant baseline: MAE ${f['mae_model_usd']:,.0f} vs ${f['mae_baseline_usd']:,.0f} per day")
    st.caption(f"Model: {f['model']}. Baseline: {f['baseline']}. Both frozen on {f['train']}; tested on {f['test']} ({f['test_days']} days). "
               f"Fixed dates, unaffected by the sidebar filters. Decision it informs: {f['decision_affected']}. No later-published data used.")
    t = m[m.split == "test"].set_index("gaming_date")[["actual_usd", "pred_model_usd", "pred_baseline_usd"]]
    st.line_chart(t.rename(columns={"actual_usd": "Actual", "pred_model_usd": "Weekday model", "pred_baseline_usd": "Constant baseline"}),
                  color=["#000000", BLUE, ORANGE])
    source("min_model.parquet", SCRIPT, "test May-Jun 2025, floor daily coin-in $")
    st.divider()
    st.subheader("Action catalogue with budget cost (guide formula)")
    show = q6[["name", "unit", "quantity_limit", "lead_days", "operating_days", "cost_per_unit_usd", "max_cost_usd", "incompatibility_group"]]
    st.dataframe(show, hide_index=True, width="stretch")
    st.caption("Lease example: $2,500 + 16 days x $55 = $3,380 per machine. Build a plan on the Overview page. "
               "Expected benefit, uncertainty and measurement plan arrive with the team's budget file.")
    source("min_q6.parquet", SCRIPT, "30 days from 2025-07-01")
