"""Shared helpers: period/bank/guest filters, safe file loader, standard page header."""
import json
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
APP_DATA = ROOT / "app_data"
RELEASE = "0.9.0-draft"
START, END = date(2025, 1, 1), date(2025, 6, 30)
MONTHS = {m: (date(2025, m, 1), date(2025, m + 1, 1) - pd.Timedelta(days=1)) for m in range(1, 6)}
MONTHS[6] = (date(2025, 6, 1), END)
PRESETS = {"Full (Jan-Jun)": (START, END), "Jan-Mar": (START, date(2025, 3, 31)), "Apr-Jun": (date(2025, 4, 1), END)}
for m, n in zip(range(1, 7), ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]):
    PRESETS[n] = tuple(MONTHS[m])
ALL = "All"


def _filters() -> dict:
    try:
        return json.loads((APP_DATA / "filters.json").read_text())
    except Exception:
        return {"banks": [], "tiers": [], "regions": [], "age_bands": []}


def sidebar() -> dict:
    """Draw the filters once and return the selection (stored in session_state)."""
    f = _filters()
    with st.sidebar:
        st.header("Filters")
        choice = st.selectbox("Period", list(PRESETS) + ["Custom range"])
        if choice == "Custom range":
            r = st.date_input("Dates", (START, END), min_value=START, max_value=END)
            lo, hi = (r[0], r[1]) if len(r) == 2 else (START, END)
        else:
            lo, hi = PRESETS[choice]
        bank = st.selectbox("Bank", [ALL] + f["banks"])
        tier = st.selectbox("Guest group (opening tier)", [ALL] + f["tiers"])
    sel = {"preset": choice, "start": lo, "end": hi, "bank": bank, "tier": tier}
    st.session_state["sel"] = sel
    return sel


def scope_label(sel: dict) -> str:
    return sel["preset"] if sel["preset"] != "Custom range" else f"custom {sel['start']} to {sel['end']}"


def load(name: str):
    """Return (DataFrame, None) or (None, reason). A missing/broken/empty file is 'pending'."""
    p = APP_DATA / name
    if not p.exists():
        return None, f"{name} not available yet"
    try:
        df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    except Exception as e:  # corrupt file must not crash a judge's page
        return None, f"{name} could not be read ({type(e).__name__})"
    return (df, None) if len(df) else (None, f"{name} is empty")


def data_version(name: str = "") -> str:
    meta = APP_DATA / (name + "._meta.json") if name else None
    if meta and meta.exists():
        try:
            m = json.loads(meta.read_text())
            return f"{m.get('producer', '?')} v{m.get('schema_version', '?')} generated {m.get('generated_at', '?')}"
        except Exception:
            pass
    return "minimum version (built from prepared views)"


def header(title: str, takeaway: str, sel: dict, files: list[str]):
    st.title(title)
    st.caption(f"**Analysis window:** {sel['start']} to {sel['end']} ({scope_label(sel)}) · bank: {sel['bank']} · "
               f"guest group: {sel['tier']}")
    st.caption(f"**Data version:** release {RELEASE}; {data_version(files[0] if files else '')}")
    st.subheader(takeaway)
    for f in files:
        _, why = load(f)
        if why:
            st.info(f"Pending: {why}.")


# ---------- findings + live recompute helpers ----------
def findings(key: str):
    """Headline numbers live in app_data/findings/minimum.json; None => page shows pending."""
    try:
        return json.loads((APP_DATA / "findings" / "minimum.json").read_text())[key]
    except Exception:
        return None


def source(file: str, script: str, scope: str):
    st.caption(f"source: {file}, script: {script}, scope: {scope}")


def machine_day(sel: dict):
    """Active machine-days inside the selected period (+ bank). Recomputed live for any date range."""
    d, why = load("min_machine_day.parquet")
    if d is None:
        return None
    d = d[(d.gaming_date >= pd.Timestamp(sel["start"])) & (d.gaming_date <= pd.Timestamp(sel["end"]))]
    return d if sel["bank"] == ALL else d[d.bank_id == sel["bank"]]


def machine_totals(d: pd.DataFrame) -> pd.DataFrame:
    """Per machine, ratio of sums: availability = available/scheduled; theo per available hour = sum theo / sum hours."""
    g = d.groupby("machine_id").agg(days=("gaming_date", "count"), house_win_usd=("house_win_usd", "sum"),
                                    theo_usd=("theo_usd", "sum"), luck_residual_usd=("luck_residual_usd", "sum"),
                                    coin_in_usd=("coin_in_usd", "sum"), available_hours=("available_hours", "sum"),
                                    scheduled_hours=("scheduled_hours", "sum")).reset_index()
    g["availability"] = g.available_hours / g.scheduled_hours
    g["theo_per_avail_hour"] = g.theo_usd / g.available_hours.where(g.available_hours > 0)
    g["hold"] = g.house_win_usd / g.coin_in_usd.where(g.coin_in_usd > 0)
    return g


def snap_months(sel: dict):
    """Player/comp data are monthly: a custom range snaps to whole months and says so."""
    ms = [f"2025-{m:02d}" for m in range(1, 7)
          if MONTHS[m][0] <= sel["end"] and MONTHS[m][1] >= sel["start"]]
    exact = sel["preset"] != "Custom range" or (
        sel["start"].day == 1 and (pd.Timestamp(sel["end"]) + pd.Timedelta(days=1)).day == 1)
    if not exact:
        st.warning(f"Player and comp data are monthly. Your range snaps to whole months: {ms[0]} to {ms[-1]}.")
    return ms
