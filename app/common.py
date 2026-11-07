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
