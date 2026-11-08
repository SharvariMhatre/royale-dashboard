"""Ocean Depths design system. Every colour hex value in the app lives here; pages use the tokens and helpers.

Contrast contract (checked in tests/test_theme.py): body text >= 4.5:1 on every surface it sits on; TEAL is for large text,
borders and fills only; TEAL_DARK is used for small text links and anything needing 4.5:1 on cream. Meaning is never carried
by colour alone: verdict chips always show their text, and multi-series charts also change line dash or use direct labels."""
import html
import re

import altair as alt
import pandas as pd
import streamlit as st

# ---- semantic colour tokens
NAVY = "#1A2332"          # sidebar, page titles, headline numbers, body text
NAVY_RAISED = "#2A3A52"   # sidebar hover / active row
TEAL = "#2D8B8B"          # accent: active-nav marker, key highlights, large text and fills only
TEAL_DARK = "#1F6F6F"     # small text links, focus ring, anything that needs 4.5:1 on cream
SEAFOAM = "#A8DADC"       # subtle fills, table header, answer box
CREAM = "#F1FAEE"         # page background
SURFACE = "#FFFFFF"       # cards
TEXT = NAVY
MUTED = "#4A5568"         # captions
BORDER = "#D5E3E1"
GRID = "#E3EEEC"          # chart gridlines, lighter than BORDER

# ---- spacing scale (px): 4 / 8 / 16 / 24
S1, S2, S3, S4 = 4, 8, 16, 24

# ---- Okabe-Ito (colour-blind safe) for multi-category charts. The reddish purple and yellow entries are left out
# (no purple in this design; yellow fails contrast on cream).
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#000000"]

# ---- verdict chips: (background, text). Text is always shown, so colour never carries the meaning alone.
CHIPS = {
    "Inspect": ("#F5D9A0", NAVY), "Short exposure": (SEAFOAM, NAVY), "Bad spot": ("#CFE3F3", NAVY),
    "Unlucky": ("#E2E8F0", NAVY), "Healthy": ("#CDEBDD", NAVY), "Broken": ("#F4C7C0", NAVY), "Truly bad": ("#E8A59B", NAVY),
}
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"], button, input, select, textarea {{ font-family: {FONT}; }}
.stApp {{ background: {CREAM}; color: {TEXT}; }}
.block-container {{ padding: {S4}px {S4}px {S4}px; max-width: 1280px; }}
@media (max-width: 640px) {{ .block-container {{ padding: {S3}px {S3}px; }} }}
h1 {{ color: {NAVY}; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 {S2}px; padding: 0; }}
h2 {{ color: {NAVY}; font-size: 1.3rem; font-weight: 600; margin: {S4}px 0 {S2}px; padding: 0; }}
h3 {{ color: {NAVY}; font-size: 1.1rem; font-weight: 600; margin: {S3}px 0 {S2}px; padding: 0; }}
p, li, td, th, label, span {{ font-variant-numeric: tabular-nums; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; opacity: 1 !important; font-size: 0.85rem; }}
a, a:visited {{ color: {TEAL_DARK}; text-decoration: underline; text-underline-offset: 2px; }}
:focus-visible {{ outline: 3px solid {TEAL_DARK}; outline-offset: 2px; }}
[data-testid="stSidebar"] :focus-visible {{ outline-color: {SEAFOAM}; }}

/* sidebar: navy with cream text */
[data-testid="stSidebar"] {{ background: {NAVY}; }}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color: {CREAM}; }}
[data-testid="stSidebar"] .sb-title {{ color: {CREAM}; font-weight: 600; font-size: 1.1rem; margin: 0 0 {S2}px; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 6px; border-left: 4px solid transparent; }}
[data-testid="stSidebarNavLink"]:hover {{ background: {NAVY_RAISED}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: {NAVY_RAISED}; border-left: 4px solid {TEAL}; font-weight: 600; }}
[data-testid="stSidebarNavLink"] span {{ color: {CREAM}; }}

/* st.header / st.subheader inside pages: calmer, consistent sizes */
[data-testid="stHeading"] h2, [data-testid="stHeadingWithActionElements"] h2 {{ font-size: 1.45rem !important; font-weight: 700; line-height: 1.3; margin-top: {S4}px; }}
[data-testid="stHeading"] h3, [data-testid="stHeadingWithActionElements"] h3 {{ font-size: 1.15rem !important; font-weight: 600; }}
[data-testid="stHeading"] a, [data-testid="stHeadingWithActionElements"] a {{ display: none; }}

/* KPI cards */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: {S3}px; box-shadow: none; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.85rem; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] > div {{ overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] {{ color: {NAVY}; font-weight: 600; font-variant-numeric: tabular-nums; }}

/* phone: KPI cards sit two per row instead of one tall stack */
@media (max-width: 640px) {{
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {{ min-width: calc(50% - {S2}px) !important; flex: 1 1 calc(50% - {S2}px) !important; }}
  [data-testid="stMetricValue"] {{ font-size: 1.5rem; }}
}}

/* panels */
.answer {{ background: {SEAFOAM}; border-left: 4px solid {NAVY}; border-radius: 4px; padding: {S3}px; margin: {S3}px 0; color: {NAVY}; }}
.answer p {{ margin: 0 0 {S2}px; }} .answer p:last-child {{ margin: 0; }}
.note {{ background: {SEAFOAM}33; border: 1px solid {BORDER}; border-left: 4px solid {TEAL_DARK}; border-radius: 4px;
        padding: {S2}px {S3}px; margin: {S2}px 0; color: {NAVY}; font-size: 0.95rem; }}
.takeaway {{ color: {NAVY}; font-weight: 600; margin: {S3}px 0 {S1}px; }}

/* tables (st.table): seafoam header, wrapped text, scroll sideways on small screens */
[data-testid="stTable"] {{ overflow-x: auto; }}
[data-testid="stTable"] table {{ border: 1px solid {BORDER}; border-radius: 8px; border-collapse: separate; border-spacing: 0; background: {SURFACE}; width: 100%; }}
[data-testid="stTable"] th {{ background: {SEAFOAM}; color: {NAVY}; font-weight: 600; text-align: left; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; }}
[data-testid="stTable"] td {{ color: {NAVY}; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; vertical-align: top;
        white-space: normal; min-width: 72px; max-width: 520px; }}
[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 8px; background: {SURFACE}; }}

/* verdict chips */

/* ===== redesign: brand, page header, hero, cards, map, checklist, meter ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@600;700;800&display=swap');
.block-container {{ padding-top: {S3}px; }}
[data-testid="stSidebar"] [data-testid="stLogo"] {{ height: 44px; max-width: 100%; }}
.sb-foot {{ color: {SEAFOAM}; font-size: 0.75rem; line-height: 1.4; margin-top: {S4}px; opacity: .9; }}

.ph {{ margin: {S2}px 0 {S3}px; }}
.ph .eyebrow {{ color: {TEAL_DARK}; font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; margin-bottom: {S1}px; }}
.ph h1 {{ font-family: 'Inter Tight', {FONT}; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; margin: 0; line-height: 1.15; }}
.ph .q {{ color: {MUTED}; font-size: 1.05rem; margin: {S1}px 0 {S2}px; }}
.pills {{ display: flex; flex-wrap: wrap; gap: {S2}px; }}
.pill {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 999px; padding: 3px 12px; font-size: .8rem; color: {NAVY}; }}
.pill b {{ color: {TEAL_DARK}; font-weight: 600; margin-right: 4px; }}

.hero {{ background: {NAVY}; color: {CREAM}; border-radius: 12px; padding: {S4}px {S4}px {S3}px; margin: 0 0 {S4}px; position: relative; overflow: hidden; }}
.hero .copy {{ position: relative; z-index: 1; max-width: calc(100% - 360px); min-height: 212px; }}
.hero .hero-art {{ position: absolute; right: {S4}px; top: {S3}px; }}
@media (max-width: 1100px) {{ .hero .hero-art {{ display: none; }} .hero .copy {{ max-width: 100%; min-height: 0; }} }}
.hero .kicker {{ color: {SEAFOAM}; font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }}
.hero h2 {{ font-family: 'Inter Tight', {FONT}; color: {CREAM}; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; margin: {S2}px 0 {S2}px; line-height: 1.1; }}
.hero p {{ color: {CREAM}; font-size: 1.02rem; margin: 0 0 {S1}px; max-width: 860px; opacity: .95; }}
.hero .tiles {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: {S3}px; margin-top: {S4}px; position: relative; z-index: 1; }}
.hero .tile {{ border-top: 3px solid {TEAL}; padding-top: {S2}px; }}
.hero .tile .v {{ font-family: 'Inter Tight', {FONT}; font-size: 2rem; font-weight: 800; color: {SEAFOAM}; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.hero .tile .l {{ font-size: .82rem; color: {CREAM}; opacity: .9; margin-top: 2px; }}
@media (max-width: 760px) {{ .hero .tiles {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .hero h2 {{ font-size: 1.6rem; }} }}

.sec {{ display: flex; align-items: baseline; gap: {S2}px; margin: {S4}px 0 {S2}px; }}
.sec .n {{ font-family: 'Inter Tight', {FONT}; color: {TEAL_DARK}; font-weight: 800; font-size: .9rem; }}
.sec h2 {{ margin: 0 !important; }}
.sec-sub {{ color: {MUTED}; margin: 0 0 {S3}px; font-size: .95rem; }}

.gm-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: {S3}px; margin: {S2}px 0 {S2}px; }}
a.gm, a.gm:visited {{ display: block; background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 8px;
     padding: {S3}px; color: {NAVY}; text-decoration: none; transition: transform .12s ease, border-color .12s ease; }}
a.gm:hover {{ transform: translateY(-2px); border-color: {TEAL}; }}
a.gm .top {{ display: flex; justify-content: space-between; align-items: center; gap: 6px; }}
a.gm .chip {{ font-size: .75rem; padding: 2px 8px; }}
a.gm .rank {{ font-size: .75rem; color: {MUTED}; font-weight: 600; letter-spacing: .06em; }}
a.gm .id {{ font-family: 'Inter Tight', {FONT}; font-size: 1.35rem; font-weight: 800; margin: {S1}px 0 2px; }}
a.gm .zone {{ font-size: .82rem; color: {MUTED}; margin-bottom: {S2}px; }}
a.gm .why {{ font-size: .85rem; line-height: 1.35; margin: {S2}px 0; min-height: 3.4em; }}
a.gm .meta {{ display: flex; gap: {S3}px; font-size: .78rem; color: {MUTED}; border-top: 1px solid {BORDER}; padding-top: {S2}px; }}
a.gm .meta b {{ color: {NAVY}; }}
a.gm .go {{ font-size: .78rem; color: {TEAL_DARK}; font-weight: 600; margin-top: {S2}px; }}

.sec-sub b {{ color: {NAVY}; }}
@media (max-width: 1200px) {{ .gm-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
@media (max-width: 760px) {{ .gm-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 460px) {{ .gm-grid {{ grid-template-columns: 1fr; }} }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: {SEAFOAM} !important; }}
.legend-row {{ display: flex; flex-wrap: wrap; gap: {S3}px; font-size: .82rem; color: {NAVY}; margin: {S1}px 0 {S2}px; }}

.case {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; padding: {S4}px; }}
.case .id {{ font-family: 'Inter Tight', {FONT}; font-size: 2rem; font-weight: 800; margin: 0; line-height: 1.1; }}
.case .sub {{ color: {MUTED}; margin: {S1}px 0 {S3}px; font-size: .9rem; }}
.case .why {{ font-size: 1rem; margin: {S3}px 0 0; padding-top: {S3}px; border-top: 1px solid {BORDER}; }}
.checks {{ list-style: none; padding: 0; margin: {S2}px 0; }}
.checks li {{ display: grid; grid-template-columns: 30px 1fr auto; gap: {S2}px; align-items: start; padding: {S2}px 0; border-bottom: 1px solid {BORDER}; }}
.checks li:last-child {{ border-bottom: 0; }}
.checks .ic {{ width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; font-size: .9rem; }}
.checks .ic.yes {{ background: {TEAL_DARK}; color: {CREAM}; }}
.checks .ic.maybe {{ background: #F5D9A0; color: {NAVY}; }}
.checks .ic.no {{ background: #E2E8F0; color: {NAVY}; }}
.checks .t {{ font-weight: 600; }} .checks .e {{ color: {MUTED}; font-size: .88rem; }}
.checks .r {{ font-size: .8rem; font-weight: 700; white-space: nowrap; padding-top: 3px; }}

.meter {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; padding: {S3}px {S4}px; margin: {S2}px 0 {S3}px; }}
.meter-flex {{ display: flex; gap: {S4}px; align-items: center; }}
.meter-main {{ flex: 1; min-width: 0; }}
@media (max-width: 640px) {{ .meter-flex {{ flex-direction: column; align-items: stretch; }} .chips-art {{ align-self: center; }} }}
.case {{ position: relative; }}
.case .slot-art {{ position: absolute; right: {S3}px; top: {S3}px; }}
.case .id, .case .sub {{ padding-right: 92px; }}
.zoomcard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 8px; padding: {S3}px; margin: {S2}px 0;
             display: grid; grid-template-columns: auto 1fr auto; gap: {S3}px; align-items: center; }}
.zoomcard .id {{ font-family: 'Inter Tight', {FONT}; font-weight: 800; font-size: 1.4rem; }}
.zoomcard .why {{ font-size: .92rem; }} .zoomcard .meta {{ color: {MUTED}; font-size: .82rem; margin-top: 2px; }}
.zoomcard a {{ font-weight: 600; white-space: nowrap; }}
@media (max-width: 640px) {{ .zoomcard {{ grid-template-columns: 1fr; }} }}
.meter .row {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: {S2}px; }}
.meter .big {{ font-family: 'Inter Tight', {FONT}; font-size: 1.8rem; font-weight: 800; }}
.meter .bar {{ height: 14px; background: {SEAFOAM}66; border-radius: 999px; margin: {S2}px 0; overflow: hidden; }}
.meter .fill {{ height: 100%; background: {NAVY}; border-radius: 999px; }}
.meter .fill.over {{ background: #B42318; }}
.meter .lbl {{ color: {MUTED}; font-size: .85rem; }}

.chip {{ white-space: nowrap; display: inline-block; padding: 2px {S2}px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; border: 1px solid {NAVY}22; }}
"""

_CHROME_HIDE = ""  # keep Streamlit's own toolbar; nothing hidden


def _ocean():
    """Altair theme used by every chart (registered once; st.altair_chart is called with theme=None)."""
    return {"config": {
        "background": "rgba(0,0,0,0)", "font": "Inter",
        "view": {"stroke": "transparent"},
        "axis": {"labelColor": MUTED, "titleColor": NAVY, "labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": 600,
                 "gridColor": GRID, "domainColor": BORDER, "tickColor": BORDER, "labelLimit": 160},
        "legend": {"labelColor": NAVY, "titleColor": NAVY, "labelFontSize": 12, "titleFontSize": 12, "orient": "top"},
        "title": {"color": NAVY, "font": "Inter", "fontSize": 14, "anchor": "start"},
        "range": {"category": OKABE_ITO},
        "line": {"strokeWidth": 2.5}, "bar": {"cornerRadiusEnd": 2},
    }}


alt.theme.register("ocean_depths", enable=True)(_ocean)


def apply():
    """Inject fonts + CSS. Call once per run after st.set_page_config."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------- text helpers
def _inline(text: str) -> str:
    """Escape, then turn **bold** into <b>. Only our own strings go through here."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text))


def answer_box(*paragraphs: str):
    st.markdown('<div class="answer">' + "".join(f"<p>{_inline(p)}</p>" for p in paragraphs) + "</div>", unsafe_allow_html=True)


def info(msg: str):
    st.markdown(f'<div class="note" role="note">{_inline(msg)}</div>', unsafe_allow_html=True)


def takeaway(text: str):
    """One-sentence takeaway that goes above a chart."""
    st.markdown(f'<div class="takeaway">{html.escape(text)}</div>', unsafe_allow_html=True)


def chip(verdict: str) -> str:
    import art  # lazy: art imports theme tokens
    bg, fg = CHIPS.get(verdict, (SEAFOAM, NAVY))
    return f'<span class="chip" style="background:{bg};color:{fg}">{art.verdict_icon(str(verdict), fg)}{html.escape(str(verdict))}</span>'


def chip_css(v) -> str:
    """Styler cell style for a verdict column: the text stays in the cell, the colour is only a reinforcement."""
    bg, fg = CHIPS.get(v, (None, None))
    return f"background-color: {bg}; color: {fg}; font-weight: 600;" if bg else ""


def money_short(x: float) -> str:
    """$163.8M / -$15.6M / $190.7K: KPI cards stay readable without truncation (exact value goes in the help tooltip)."""
    a = abs(x)
    v = f"${a / 1e6:,.1f}M" if a >= 1e6 else (f"${a / 1e3:,.1f}K" if a >= 1e4 else f"${a:,.0f}")
    return ("-" if x < 0 else "") + v


def _months(d: pd.DataFrame, x: str) -> pd.DataFrame:
    """'2025-01' style categories read as 'Jan 2025' on axes (data order kept)."""
    if x in d.columns and d[x].dtype == object and d[x].astype(str).str.fullmatch(r"\d{4}-\d{2}").all():
        d = d.copy()
        d[x] = pd.to_datetime(d[x] + "-01").dt.strftime("%b %Y")
    return d


def kpis(items: list[tuple]):
    """Row of st.metric cards: (label, value) or (label, value, help)."""
    cols = st.columns(len(items))
    for c, it in zip(cols, items):
        c.metric(it[0], it[1], help=it[2] if len(it) > 2 else None)


# ---------------------------------------------------------------- charts
def _render(chart, height=300):
    st.altair_chart(chart.properties(height=height), theme=None, width="stretch")


def line(df: pd.DataFrame, x: str, ys: list[str], xtitle: str, ytitle: str, fmt: str = "$,.0f", height: int = 300):
    """Wide dataframe -> line chart. One series: navy. Several: Okabe-Ito plus a different dash per series (never colour alone)."""
    d = _months(df.reset_index() if x not in df.columns else df, x)
    long = d.melt(x, value_vars=ys, var_name="Series", value_name="v")
    is_t = pd.api.types.is_datetime64_any_dtype(d[x])
    enc = dict(x=alt.X(f"{x}:{'T' if is_t else 'N'}", title=xtitle, axis=alt.Axis(format="%b %d", labelAngle=0) if is_t else alt.Axis(labelAngle=0), sort=None),
               y=alt.Y("v:Q", title=ytitle, axis=alt.Axis(format=fmt, tickCount=5)),
               tooltip=[alt.Tooltip(f"{x}", title=xtitle), alt.Tooltip("Series:N"), alt.Tooltip("v:Q", title=ytitle, format=fmt)])
    if len(ys) == 1:
        ch = alt.Chart(long).mark_line(color=NAVY, point=alt.OverlayMarkDef(color=NAVY, size=30)).encode(**enc)
    else:
        dashes = [[1, 0], [6, 3], [2, 2], [8, 3, 2, 3], [1, 3], [4, 4]][: len(ys)]
        ch = alt.Chart(long).mark_line().encode(
            color=alt.Color("Series:N", scale=alt.Scale(domain=ys, range=OKABE_ITO[: len(ys)]), legend=alt.Legend(title=None)),
            strokeDash=alt.StrokeDash("Series:N", scale=alt.Scale(domain=ys, range=dashes), legend=None), **enc)
    _render(ch, height)


def bars(df: pd.DataFrame, x: str, y: str | list[str], xtitle: str, ytitle: str, fmt: str = "$,.0f", horizontal: bool = False,
         color: str = TEAL, height: int = 300):
    """Single series: one colour (teal by default, navy via color=). Several series (y is a list): stacked, Okabe-Ito, with legend."""
    d = _months(df.reset_index() if x not in df.columns else df, x)
    cat = alt.X(f"{x}:N", title=xtitle, sort=None, axis=alt.Axis(labelAngle=0, labelLimit=140)) if not horizontal else alt.Y(f"{x}:N", title=xtitle, sort=None)
    if isinstance(y, str):
        val = alt.Y("v:Q", title=ytitle, axis=alt.Axis(format=fmt, tickCount=5)) if not horizontal else alt.X("v:Q", title=ytitle, axis=alt.Axis(format=fmt, tickCount=5))
        long = d.assign(v=d[y])
        ch = alt.Chart(long).mark_bar(color=color).encode(**({"x": cat, "y": val} if not horizontal else {"y": cat, "x": val}),
                                                          tooltip=[alt.Tooltip(f"{x}:N", title=xtitle), alt.Tooltip("v:Q", title=ytitle, format=fmt)])
    else:
        long = d.melt(x, value_vars=y, var_name="Series", value_name="v")
        ch = alt.Chart(long).mark_bar().encode(
            x=cat, y=alt.Y("v:Q", title=ytitle, axis=alt.Axis(format=fmt, tickCount=5)),
            color=alt.Color("Series:N", scale=alt.Scale(domain=y, range=OKABE_ITO[: len(y)]), legend=alt.Legend(title=None)),
            tooltip=[alt.Tooltip(f"{x}:N", title=xtitle), alt.Tooltip("Series:N"), alt.Tooltip("v:Q", title=ytitle, format=fmt)])
    _render(ch, height)


def altair(chart, height: int = 300):
    """Render a hand-built Altair chart with the shared theme."""
    _render(chart, height)


# ---------------------------------------------------------------- redesign helpers
BRAND = "The Gilded Ace · Floor Doctor"
VERDICT_ORDER = ["Inspect", "Bad spot", "Short exposure", "Unlucky", "Broken", "Truly bad", "Healthy"]
# map colours (Okabe-Ito) + shapes: colour is never alone, every verdict also has its own shape and text label
VERDICT_COLOR = {"Inspect": "#D55E00", "Bad spot": "#E69F00", "Short exposure": "#0072B2", "Unlucky": "#56B4E9",
                 "Broken": "#000000", "Truly bad": "#000000", "Healthy": "#009E73"}
VERDICT_SHAPE = {"Inspect": "cross", "Bad spot": "square", "Short exposure": "triangle-up", "Unlucky": "diamond",
                 "Broken": "triangle-down", "Truly bad": "wedge", "Healthy": "circle"}


def html_block(s: str):
    st.markdown(s, unsafe_allow_html=True)


def page_header(title: str, question: str, pills: list[tuple[str, str]]):
    p = "".join(f'<span class="pill"><b>{html.escape(k)}</b>{html.escape(v)}</span>' for k, v in pills)
    html_block(f'<div class="ph"><div class="eyebrow">{html.escape(BRAND)}</div><h1>{html.escape(title)}</h1>'
               f'<p class="q">{html.escape(question)}</p><div class="pills">{p}</div></div>')


def hero(kicker: str, headline: str, lines: list[str], tiles: list[tuple[str, str]]):
    t = "".join(f'<div class="tile"><div class="v">{html.escape(v)}</div><div class="l">{html.escape(l)}</div></div>' for v, l in tiles)
    body = "".join(f"<p>{_inline(x)}</p>" for x in lines)
    import art
    html_block(f'<section class="hero" aria-label="Answer in brief">{art.hero_floor()}<div class="copy"><div class="kicker">{html.escape(kicker)}</div>'
               f'<h2>{html.escape(headline)}</h2>{body}</div><div class="tiles">{t}</div></section>')


def section(num: str, title: str, sub: str = ""):
    html_block(f'<div class="sec"><span class="n">{html.escape(num)}</span><h2>{html.escape(title)}</h2></div>'
               + (f'<p class="sec-sub">{_inline(sub)}</p>' if sub else ""))


def gm_cards(rows: list[dict]):
    """rows: rank, id, zone, verdict, why, luck, days. Each card links to that machine's case file."""
    cards = []
    for r in rows:
        why = r["why"] if len(r["why"]) <= 110 else r["why"][:107].rsplit(" ", 1)[0] + "..."
        cards.append(
            f'<a class="gm" href="machine_details?m={html.escape(r["id"])}" target="_self" style="--vc:{VERDICT_COLOR.get(r["verdict"], TEAL)}" '
            f'aria-label="GM rank {r["rank"]}, {html.escape(r["id"])}, verdict {html.escape(r["verdict"])}. Open case file.">'
            f'<div class="top"><span class="rank">GM #{r["rank"]}</span>{chip(r["verdict"])}</div>'
            f'<div class="id">{html.escape(r["id"])}</div><div class="zone">{html.escape(r["zone"])}</div>'
            f'<div class="why">{html.escape(why)}</div>'
            f'<div class="meta"><span>Luck pct <b>{r["luck"]}</b></span><span>Days <b>{r["days"]}</b></span></div>'
            f'<div class="go">Open case file &rarr;</div></a>')
    html_block('<div class="gm-grid">' + "".join(cards) + "</div>")


def checklist(items: list[tuple[str, str, str]]):
    """items: (explanation, evidence, result) with result Supported / Unlikely / Not supported. Icon + word, never colour alone."""
    ic = {"Supported": ("yes", "&#10003;"), "Unlikely": ("maybe", "~"), "Not supported": ("no", "&#10005;")}
    li = "".join(f'<li><span class="ic {ic.get(r, ("no", "?"))[0]}" aria-hidden="true">{ic.get(r, ("no", "?"))[1]}</span>'
                 f'<div><div class="t">{html.escape(t)}</div><div class="e">{html.escape(e)}</div></div>'
                 f'<span class="r">{html.escape(r)}</span></li>' for t, e, r in items)
    html_block(f'<ul class="checks" aria-label="Competing explanations tested">{li}</ul>')


def meter(spent: float, budget: float = 100000, types: int = 0):
    pct = min(spent / budget, 1) * 100 if budget else 0
    over = spent > budget
    import art
    html_block(f'<div class="meter" role="group" aria-label="Budget used"><div class="meter-flex">{art.chip_stacks(spent, budget)}<div class="meter-main"><div class="row"><span class="big">${spent:,.0f} <span class="lbl">of ${budget:,.0f} spent</span></span>'
               f'<span class="lbl">{"Over budget" if over else f"${budget - spent:,.0f} kept"} &middot; {types} of 3 action types used</span></div>'
               f'<div class="bar"><div class="fill{" over" if over else ""}" style="width:{pct:.1f}%"></div></div>'
               f'<div class="lbl">Keeping money is allowed and uses no action slot. Each chip = $10,000.</div></div></div></div>')
