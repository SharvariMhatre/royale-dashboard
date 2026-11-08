"""Skin: default (Ocean Depths). Tokens + CSS exactly as the dashboard shipped before skins existed.
A skin module defines the same names; theme.py picks one at import time. Roles are written next to each token."""
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

# ---- extra tokens: colours that used to be literals in theme.py / art.py (same values)
AMBER_SOFT = "#F5D9A0"    # "maybe" icon fill, Inspect chip
SLATE_SOFT = "#E2E8F0"    # "no" icon fill, Unlucky chip
DANGER = "#B42318"        # over-budget bar and chips
HIGHLIGHT = "#E69F00"     # hero art: the highlighted zone (Back Forty)
HIGHLIGHT_SOFT = "#F5C26B"  # hero art: highlighted label and marker

# ---- spacing scale (px): 4 / 8 / 16 / 24
S1, S2, S3, S4 = 4, 8, 16, 24

# ---- Okabe-Ito (colour-blind safe) for multi-category charts. The reddish purple and yellow entries are left out
# (no purple in this design; yellow fails contrast on cream).
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#000000"]
CHART_MARK = NAVY  # single-series bar fill (T.bars color=): the ink, as before

# ---- verdict chips: (background, text). Text is always shown, so colour never carries the meaning alone.
CHIPS = {
    "Inspect": (AMBER_SOFT, NAVY), "Short exposure": (SEAFOAM, NAVY), "Bad spot": ("#CFE3F3", NAVY),
    "Unlucky": (SLATE_SOFT, NAVY), "Healthy": ("#CDEBDD", NAVY), "Broken": ("#F4C7C0", NAVY), "Truly bad": ("#E8A59B", NAVY),
}
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
ALTAIR_FONT = "Inter"  # font name used inside Altair charts

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
.checks .ic.maybe {{ background: {AMBER_SOFT}; color: {NAVY}; }}
.checks .ic.no {{ background: {SLATE_SOFT}; color: {NAVY}; }}
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
.meter .fill.over {{ background: {DANGER}; }}
.meter .lbl {{ color: {MUTED}; font-size: .85rem; }}

.chip {{ white-space: nowrap; display: inline-block; padding: 2px {S2}px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; border: 1px solid {NAVY}22; }}
"""

# ---- verdict mark colours (Okabe-Ito) used by charts, map and case cards; shapes live in theme.VERDICT_SHAPE
VERDICT_COLOR = {"Inspect": "#D55E00", "Bad spot": "#E69F00", "Short exposure": "#0072B2", "Unlucky": "#56B4E9",
                 "Broken": "#000000", "Truly bad": "#000000", "Healthy": "#009E73"}
