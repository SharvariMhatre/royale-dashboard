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

/* KPI cards */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: {S3}px; box-shadow: none; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.85rem; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
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
.chip {{ display: inline-block; padding: 2px {S2}px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; border: 1px solid {NAVY}22; }}
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
    bg, fg = CHIPS.get(verdict, (SEAFOAM, NAVY))
    return f'<span class="chip" style="background:{bg};color:{fg}">{html.escape(str(verdict))}</span>'


def chip_css(v) -> str:
    """Styler cell style for a verdict column: the text stays in the cell, the colour is only a reinforcement."""
    bg, fg = CHIPS.get(v, (None, None))
    return f"background-color: {bg}; color: {fg}; font-weight: 600;" if bg else ""


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
    d = df.reset_index() if x not in df.columns else df
    long = d.melt(x, value_vars=ys, var_name="Series", value_name="v")
    enc = dict(x=alt.X(f"{x}:{'T' if pd.api.types.is_datetime64_any_dtype(d[x]) else 'N'}", title=xtitle),
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
    d = df.reset_index() if x not in df.columns else df
    cat = alt.X(f"{x}:N", title=xtitle, sort=None) if not horizontal else alt.Y(f"{x}:N", title=xtitle, sort=None)
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
