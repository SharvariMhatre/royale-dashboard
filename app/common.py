"""Shared helpers: period/bank/guest filters, safe file loader, standard page header."""
import json
from datetime import date, datetime
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


import sys
sys.path.insert(0, str(ROOT / "src"))
import importlib  # noqa: E402
import validate_contracts as _vc  # noqa: E402

importlib.reload(_vc)  # Streamlit Cloud can keep a stale copy of this module in sys.modules across deploys
_STEMS, _check, _meta_path = _vc.CONTRACT_STEMS, _vc.check, _vc.meta_path


def load(name: str):
    """Return (DataFrame, None) or (None, reason). A missing/broken/empty file is 'pending'."""
    p = APP_DATA / name
    if not p.exists():
        return None, f"{name} not available yet"
    if p.stem in _STEMS or name == "claims.csv":  # team files must pass the contract before any page uses them
        errs, _ = _check(p)
        if errs:
            return None, f"{name} failed validation ({errs[0]})"
    try:
        df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    except Exception as e:  # corrupt file must not crash a judge's page
        return None, f"{name} could not be read ({type(e).__name__})"
    return (df, None) if len(df) else (None, f"{name} is empty")


def data_version(name: str = "") -> str:
    meta = _meta_path(APP_DATA / name) if name else None
    if not meta and name and (APP_DATA / name).exists() and name.startswith("team/"):
        return f"exported from Databricks (workspace.casino), file dated {datetime.fromtimestamp((APP_DATA / name).stat().st_mtime):%b} "                f"{datetime.fromtimestamp((APP_DATA / name).stat().st_mtime).day}"
    if meta:
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
            st.info(f"Pending: {why}. Showing the minimum version where one exists.")


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


def footer(files: list[str]):
    """Page footer: version of each team file in use, and a warning when its _meta sidecar is missing."""
    lines = []
    for f in files:
        p = APP_DATA / f
        if p.exists() and p.stem in _STEMS:
            errs, warns = _check(p)
            lines += [f"Warning: {w}" for w in warns] if not errs else []
    if lines:
        st.divider()
        for ln in lines:
            st.caption(ln)


# ---------- manager-friendly formatting ----------
def usd(x) -> str:
    """-$3,905 (never $-3,905)."""
    return "" if pd.isna(x) else f"{'-' if x < 0 else ''}${abs(x):,.0f}"


def _fmt(s: pd.Series, kind: str) -> pd.Series:
    f = {"usd": usd, "pct": lambda x: f"{x:.0%}", "pct1": lambda x: f"{x:.1%}", "int": lambda x: f"{int(x):,}",
         "num": lambda x: f"{x:,.1f}", "pct2": lambda x: f"{x:.2%}", "month": lambda x: f"{pd.Timestamp(str(x) + '-01'):%b %Y}", "yesno": lambda x: "Yes" if x else "No",
         "date": lambda x: f"{pd.Timestamp(x):%b} {pd.Timestamp(x).day}", "text": str}[kind]
    return s.map(lambda x: "" if (x is None or (not isinstance(x, (list, str)) and pd.isna(x))) else f(x))


def show(df: pd.DataFrame, spec: dict):
    """Display a table for a manager: spec = {column: (plain-English name, kind)}; kinds: usd pct pct1 int num yesno date text."""
    out = pd.DataFrame({lab: _fmt(df[c], k) for c, (lab, k) in spec.items() if c in df.columns})
    st.dataframe(out, hide_index=True, width="stretch")


# ---------- team files, team findings, evidence ----------
def team(name: str):
    """Validated team table or None (a failed/missing file is 'pending': callers fall back to the minimum version)."""
    d = load(f"team/{name}.parquet")[0]
    if d is None:
        return None
    d = d.copy()
    for c in d.columns:  # Databricks DECIMAL arrives as Decimal objects; dates as python dates: normalise for pandas/altair
        if d[c].dtype == object and d[c].notna().any():
            x = d[c].dropna().iloc[0]
            if type(x).__name__ == "Decimal":
                d[c] = d[c].astype(float)
            elif type(x).__name__ == "date":
                d[c] = pd.to_datetime(d[c])
    return d


def tfind(key: str):
    try:
        return json.loads((APP_DATA / "findings" / "team.json").read_text())[key]
    except Exception:
        return None


def evidence(questions: list[str], machine: str | None = None, title: str = "Evidence: claims behind this page"):
    """Expander listing the team's claims for these questions (alternative tested + limitation shown). Machine claims first."""
    c = team("all_claims")
    if c is None:
        return
    c = c[c.question.isin(questions)].copy()
    if machine:
        hit = c.apply(lambda r: machine in f"{r.claim} {r.result}", axis=1)
        c = pd.concat([c[hit], c[~hit]])
    with st.expander(f"{title} ({len(c)})"):
        show(c, {"claim_id": ("ID", "text"), "claim": ("Claim", "text"), "result": ("Result", "text"),
                 "alternative_tested": ("Alternative explanation tested", "text"), "limitation": ("Limitation", "text"),
                 "confidence": ("Confidence", "text"), "evidence_table": ("Evidence table", "text"), "source": ("From", "text")})
