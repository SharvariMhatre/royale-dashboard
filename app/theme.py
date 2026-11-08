"""Design system. Every colour hex value in the app lives in a skin (app/skins/<name>.py); this module loads one and exposes its
tokens (T.NAVY, T.CHIPS, ...) plus the helpers pages use. The notes below describe the default skin ("Ocean Depths").

Contrast contract (checked in tests/test_theme.py): body text >= 4.5:1 on every surface it sits on; TEAL is for large text,
borders and fills only; TEAL_DARK is used for small text links and anything needing 4.5:1 on cream. Meaning is never carried
by colour alone: verdict chips always show their text, and multi-series charts also change line dash or use direct labels."""
import html
import importlib
import re

import altair as alt
import pandas as pd
import streamlit as st

# ---- skins: tokens + CSS live in app/skins/<name>.py (same names in each). One is picked at import time:
# ?skin=<name> in the URL wins (an explicit link), then the choice remembered in session_state, then DEFAULT_SKIN.
# "default" is the original Ocean Depths look (kept as skins/default.py, reachable with ?skin=default); noir is what a bare URL shows.
SKINS = ("default", "noir", "control", "paper")
DEFAULT_SKIN = "noir"
_TOKENS = ("NAVY", "NAVY_RAISED", "TEAL", "TEAL_DARK", "SEAFOAM", "CREAM", "SURFACE", "TEXT", "MUTED", "BORDER", "GRID", "CHART_MARK",
           "AMBER_SOFT", "SLATE_SOFT", "DANGER", "HIGHLIGHT", "HIGHLIGHT_SOFT", "S1", "S2", "S3", "S4",
           "OKABE_ITO", "CHIPS", "VERDICT_COLOR", "FONT", "ALTAIR_FONT", "CSS")


def _skin_name() -> str:
    try:  # also runs outside a Streamlit run (tests/test_theme.py), where this just falls back to DEFAULT_SKIN
        q = st.query_params.get("skin")
        if q in SKINS:
            st.session_state["skin"] = q
        s = st.session_state.get("skin", DEFAULT_SKIN)
        return s if s in SKINS else DEFAULT_SKIN
    except Exception:
        return DEFAULT_SKIN


def _load(name: str):
    try:
        return importlib.reload(importlib.import_module(f"skins.{name}"))
    except ModuleNotFoundError as e:  # a skin not written yet falls back; any other import error should surface
        if e.name != f"skins.{name}":
            raise
        return _load("default")


SKIN = _skin_name()
_S = _load(SKIN)
globals().update({n: getattr(_S, n) for n in _TOKENS})
SKIN_Q = "" if SKIN == DEFAULT_SKIN else f"&skin={SKIN}"  # appended to target=_self links, which start a new session

_CHROME_HIDE = ""  # keep Streamlit's own toolbar; nothing hidden


def _ocean():
    """Altair theme used by every chart (registered once; st.altair_chart is called with theme=None)."""
    return {"config": {
        "background": "rgba(0,0,0,0)", "font": ALTAIR_FONT,
        "view": {"stroke": "transparent"},
        "axis": {"labelColor": MUTED, "titleColor": NAVY, "labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": 600,
                 "gridColor": GRID, "domainColor": BORDER, "tickColor": BORDER, "labelLimit": 160},
        "legend": {"labelColor": NAVY, "titleColor": NAVY, "labelFontSize": 12, "titleFontSize": 12, "orient": "top"},
        "title": {"color": NAVY, "font": ALTAIR_FONT, "fontSize": 14, "anchor": "start"},
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
            f'<a class="gm" href="machine_details?m={html.escape(r["id"])}{SKIN_Q}" target="_self" style="--vc:{VERDICT_COLOR.get(r["verdict"], TEAL)}" '
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
