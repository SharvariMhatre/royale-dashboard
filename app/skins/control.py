"""Skin: control (Pit-Boss Control Room, mid-tone). Light skin: sage wall, pale instrument panels, mono figures, amber lamps.
Token NAMES match default.py; ROLES differ and are written next to each value. Same contract, CSS replaces the default CSS."""
# ---- semantic colour tokens
NAVY = "#101820"          # ink: body text, headline numbers, chart strokes/labels, bar fills (near-black, not navy here)
NAVY_RAISED = "#B9C5BD"   # hover / active row in the sidebar, popup option hover, meter track
TEAL = "#A64F00"          # amber (darkened): lamps, nav marker, large text, fills only
TEAL_DARK = "#6E3600"     # dark amber: small text links, eyebrow labels
SEAFOAM = "#2A3838"       # DARK slate: table header fill, art strokes/fills on light panels (chip stacks, hero floor)
CREAM = "#C5CDC2"         # page background (the "wall")
SURFACE = "#E9EDE4"       # cards
TEXT = NAVY
MUTED = "#34423F"         # captions
BORDER = "#7F8F88"
GRID = "#AEB9B1"          # chart gridlines

# ---- extra tokens
AMBER_SOFT = "#F5D9A0"    # "maybe" icon fill, Inspect chip, answer box
SLATE_SOFT = "#E2E8F0"    # "no" icon fill, Unlucky chip
DANGER = "#B42318"        # over-budget bar and chips
HIGHLIGHT = "#A86A00"     # hero art: highlighted zone (Back Forty) stroke and fill
HIGHLIGHT_SOFT = "#965700"  # hero art: highlighted label (text on the light hero) and marker stroke

S1, S2, S3, S4 = 4, 8, 16, 24

# ---- Okabe-Ito with lightness nudged so marks hold 3:1 on the pale chart panel
OKABE_ITO = ["#0072B2", "#A86A00", "#007F5F", "#C24E00", "#2A7DB8", "#000000"]
CHART_MARK = OKABE_ITO[0]  # single-series bar fill: blue (4.4:1 on SURFACE) instead of the near-black ink

# ---- verdict chips: (background, text). Today's pastel fills; text is always shown.
CHIPS = {
    "Inspect": (AMBER_SOFT, NAVY), "Short exposure": ("#A8DADC", NAVY), "Bad spot": ("#CFE3F3", NAVY),
    "Unlucky": (SLATE_SOFT, NAVY), "Healthy": ("#CDEBDD", NAVY), "Broken": ("#F4C7C0", NAVY), "Truly bad": ("#E8A59B", NAVY),
}
FONT = "'IBM Plex Sans', 'Segoe UI', system-ui, -apple-system, sans-serif"
ALTAIR_FONT = "IBM Plex Sans"

# ---- local (not part of the seam)
MONO = "'IBM Plex Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace"
PANEL = "#F4F6F0"         # chart panel: keeps chart marks at 3:1
LIGHT = "#F2F4EE"         # text on the dark table header
FOCUS = "#003F7F"
SIDEBAR = "#A9B6AE"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"], button, input, select, textarea {{ font-family: {FONT}; }}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {{ background: {CREAM}; color: {TEXT}; }}
.block-container {{ padding: {S3}px {S4}px {S4}px; max-width: 1280px; }}
@media (max-width: 640px) {{ .block-container {{ padding: {S3}px {S3}px; }} }}
h1 {{ color: {NAVY}; font-size: 1.75rem; font-weight: 700; margin: 0 0 {S2}px; padding: 0; }}
h2 {{ color: {NAVY}; font-size: 1.3rem; font-weight: 600; margin: {S4}px 0 {S2}px; padding: 0; }}
h3 {{ color: {NAVY}; font-size: 1.1rem; font-weight: 600; margin: {S3}px 0 {S2}px; padding: 0; }}
.stApp h1, .stApp h2, .stApp h3 {{ font-family: {FONT}; }}
p, li, td, th, label, span {{ font-variant-numeric: tabular-nums; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; opacity: 1 !important; font-size: 0.85rem; }}
a, a:visited {{ color: {TEAL_DARK}; text-decoration: underline; text-underline-offset: 2px; }}
*:focus-visible {{ outline: 3px solid {FOCUS} !important; outline-offset: 2px; }}

/* sidebar: light sage with dark ink */
[data-testid="stSidebar"] {{ background: {SIDEBAR}; color: {NAVY}; }}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p, [data-testid="stSidebar"] button {{ color: {NAVY}; }}
[data-testid="stSidebar"] .sb-title {{ color: {NAVY}; font-weight: 600; font-size: 1.1rem; margin: 0 0 {S2}px; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"] {{ background: {SURFACE}; border-color: {BORDER}; }}
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] [data-baseweb="input"] input {{ color: {NAVY}; }}
/* the st.logo SVG is cream-on-dark and fixed: invert it so it reads on the light sidebar */
[data-testid="stSidebarLogo"] {{ filter: invert(1) hue-rotate(180deg) brightness(.8); height: 44px; max-width: 100%; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 4px; border-left: 4px solid transparent; }}
[data-testid="stSidebarNavLink"]:hover {{ background: {NAVY_RAISED}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: {NAVY_RAISED}; border-left: 4px solid {TEAL}; font-weight: 600; }}
[data-testid="stSidebarNavLink"] span {{ color: {NAVY}; }}

/* popups (dropdown, date picker) */
[data-baseweb="popover"] > div {{ border: 1px solid {BORDER}; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"], [data-baseweb="calendar"] {{ background: {SURFACE}; color: {NAVY}; }}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {{ background: {NAVY_RAISED}; }}

/* st.header / st.subheader inside pages */
[data-testid="stHeading"] h2, [data-testid="stHeadingWithActionElements"] h2 {{ font-size: 1.45rem !important; font-weight: 700; line-height: 1.3; margin-top: {S4}px; }}
[data-testid="stHeading"] h3, [data-testid="stHeadingWithActionElements"] h3 {{ font-size: 1.15rem !important; font-weight: 600; }}
[data-testid="stHeading"] a, [data-testid="stHeadingWithActionElements"] a {{ display: none; }}

/* KPI cards: pale instrument panels with an amber lamp (decoration only, never a status) */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 4px; padding: {S2}px {S3}px; box-shadow: none; position: relative; }}
[data-testid="stMetric"]::after {{ content: ""; position: absolute; top: {S2}px; right: {S2}px; width: 8px; height: 8px; border-radius: 50%;
        background: {TEAL}; animation: lamp 2.4s ease-in-out infinite; }}
@keyframes lamp {{ 0%, 100% {{ box-shadow: 0 0 0 0 {TEAL}00; }} 50% {{ box-shadow: 0 0 0 4px {TEAL}44; }} }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-family: {MONO}; font-size: 0.82rem; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricLabel"] {{ padding-right: {S3}px; }}
[data-testid="stMetricValue"] > div {{ overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] {{ color: {NAVY}; font-family: {MONO}; font-weight: 600; font-size: 1.75rem; font-variant-numeric: tabular-nums; }}

/* KPI cards in one row share the tallest height */
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) {{ align-items: stretch; }}
[data-testid="stColumn"]:has([data-testid="stMetric"]) > [data-testid="stVerticalBlock"], [data-testid="stColumn"]:has([data-testid="stMetric"]) [data-testid="stElementContainer"],
[data-testid="stColumn"] [data-testid="stMetric"] {{ height: 100%; }}

/* phone: KPI cards sit two per row instead of one tall stack */
@media (max-width: 640px) {{
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {{ min-width: calc(50% - {S2}px) !important; flex: 1 1 calc(50% - {S2}px) !important; }}
  [data-testid="stMetricValue"] {{ font-size: 1.2rem; }}
  [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{ white-space: normal !important; overflow-wrap: anywhere; }}
  [data-testid="stTable"] td {{ min-width: 128px !important; }}
}}

/* charts sit in a flat pale panel (this is what keeps the marks at 3:1) */
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 4px; padding: {S2}px; }}

/* panels */
.answer {{ background: {AMBER_SOFT}; border: 1px solid {BORDER}; border-left: 6px solid {TEAL}; border-radius: 4px; padding: {S3}px; margin: {S3}px 0; color: {NAVY}; }}
.answer p {{ margin: 0 0 {S2}px; }} .answer p:last-child {{ margin: 0; }}
.note {{ background: {PANEL}; border: 1px solid {BORDER}; border-left: 4px solid {TEAL_DARK}; border-radius: 4px;
        padding: {S2}px {S3}px; margin: {S2}px 0; color: {NAVY}; font-size: 0.95rem; }}
.takeaway {{ color: {NAVY}; font-weight: 600; margin: {S3}px 0 {S1}px; }}

/* tables (st.table): flat, dark header strip, wrapped text, scroll sideways on small screens */
[data-testid="stTable"] {{ overflow-x: auto; }}
[data-testid="stTable"] table {{ border: 1px solid {BORDER}; border-radius: 4px; border-collapse: separate; border-spacing: 0; background: {SURFACE}; width: 100%; }}
[data-testid="stTable"] th {{ background: {SEAFOAM}; color: {LIGHT}; font-family: {MONO}; font-size: 0.82rem; font-weight: 600; text-align: left; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; }}
[data-testid="stTable"] td {{ color: {NAVY}; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; vertical-align: top;
        white-space: normal; min-width: 72px; max-width: 520px; }}
[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 4px; background: {SURFACE}; }}

/* ===== brand, page header, hero, cards, map, checklist, meter ===== */
.sb-foot {{ color: {MUTED}; font-size: 0.75rem; line-height: 1.4; margin-top: {S4}px; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}

.ph {{ margin: {S2}px 0 {S3}px; }}
.ph .eyebrow {{ color: {TEAL_DARK}; font-family: {MONO}; font-size: .82rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; margin-bottom: {S1}px; }}
.ph h1 {{ font-size: 1.9rem; font-weight: 700; letter-spacing: -0.01em; margin: 0; line-height: 1.15; }}
.ph .q {{ color: {MUTED}; font-size: 1.02rem; margin: {S1}px 0 {S2}px; }}
.pills {{ display: flex; flex-wrap: wrap; gap: {S2}px; }}
.pill {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 4px; padding: 2px 10px; font-family: {MONO}; font-size: .82rem; color: {NAVY}; }}
.pill b {{ color: {TEAL_DARK}; font-weight: 600; margin-right: 6px; }}
/* tick-tape under the page header: text-free scanning ticks (CSS only; the shift is one full 40px period so the loop is seamless) */
.ph::after {{ content: ""; display: block; height: 10px; margin-top: {S3}px; opacity: .55; animation: tape 8s linear infinite;
        background: linear-gradient(90deg, {NAVY} 1px, transparent 1px) 0 100% / 8px 5px repeat-x,
                    linear-gradient(90deg, {NAVY} 2px, transparent 2px) 0 100% / 40px 10px repeat-x; }}
@keyframes tape {{ to {{ background-position: 40px 100%, 40px 100%; }} }}
@media (max-width: 640px) {{ .ph::after {{ display: none; }} }}

.hero {{ background: {SURFACE}; color: {NAVY}; border: 1px solid {BORDER}; border-top: 6px solid {SEAFOAM}; border-radius: 4px;
        padding: {S4}px {S4}px {S3}px; margin: 0 0 {S4}px; position: relative; overflow: hidden; }}
.hero .copy {{ position: relative; z-index: 1; max-width: calc(100% - 360px); min-height: 212px; }}
.hero .hero-art {{ position: absolute; right: {S4}px; top: {S3}px; }}
.hero-art path[stroke-dasharray] {{ stroke: {NAVY}; }}
.hero-art text, .chips-art text, .slot-art text {{ font-family: {FONT}; }}
@media (max-width: 1100px) {{ .hero .hero-art {{ display: none; }} .hero .copy {{ max-width: 100%; min-height: 0; }} }}
.hero .kicker {{ color: {TEAL_DARK}; font-family: {MONO}; font-size: .82rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; }}
.hero h2 {{ color: {NAVY}; font-size: 2rem; font-weight: 700; letter-spacing: -0.01em; margin: {S2}px 0 {S2}px; line-height: 1.12; }}
.hero p {{ color: {NAVY}; font-size: 1.02rem; margin: 0 0 {S1}px; max-width: 860px; }}
.hero .tiles {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: {S3}px; margin-top: {S4}px; position: relative; z-index: 1; }}
.hero .tile {{ background: {PANEL}; border: 1px solid {BORDER}; border-top: 3px solid {TEAL}; border-radius: 4px; padding: {S2}px {S3}px; }}
.hero .tile .v {{ font-family: {MONO}; font-size: 1.8rem; font-weight: 600; color: {NAVY}; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.hero .tile .l {{ font-size: .85rem; color: {MUTED}; margin-top: 2px; }}
@media (max-width: 760px) {{ .hero .tiles {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .hero h2 {{ font-size: 1.5rem; }} .hero .tile .v {{ font-size: 1.4rem; }} }}

.sec {{ display: flex; align-items: baseline; gap: {S2}px; margin: {S4}px 0 {S2}px; padding-bottom: {S1}px; border-bottom: 1px solid {BORDER}; }}
.sec .n {{ font-family: {MONO}; color: {TEAL_DARK}; font-weight: 600; font-size: .9rem; }}
.sec h2 {{ margin: 0 !important; }}
.sec-sub {{ color: {MUTED}; margin: 0 0 {S3}px; font-size: .95rem; }}
.sec-sub b {{ color: {NAVY}; }}

.gm-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: {S3}px; margin: {S2}px 0 {S2}px; }}
a.gm, a.gm:visited {{ display: block; background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 4px;
     padding: {S3}px; color: {NAVY}; text-decoration: none; transition: transform .12s ease, border-color .12s ease; }}
a.gm:hover {{ transform: translateY(-2px); border-color: {TEAL}; }}
a.gm .top {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 6px; }}
a.gm .rank {{ white-space: nowrap; }}
a.gm .chip {{ font-size: .82rem; padding: 2px 8px; }}
a.gm .rank {{ font-family: {MONO}; font-size: .82rem; color: {MUTED}; font-weight: 600; letter-spacing: .04em; }}
a.gm .id {{ font-family: {MONO}; font-size: 1.3rem; font-weight: 600; margin: {S1}px 0 2px; }}
a.gm .zone {{ font-size: .85rem; color: {MUTED}; margin-bottom: {S2}px; }}
a.gm .why {{ font-size: .85rem; line-height: 1.35; margin: {S2}px 0; min-height: 3.4em; }}
a.gm .meta {{ display: flex; gap: {S3}px; font-family: {MONO}; font-size: .82rem; color: {MUTED}; border-top: 1px solid {BORDER}; padding-top: {S2}px; }}
a.gm .meta b {{ color: {NAVY}; }}
a.gm .go {{ font-size: .82rem; color: {TEAL_DARK}; font-weight: 600; margin-top: {S2}px; }}
@media (max-width: 1200px) {{ .gm-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
@media (max-width: 760px) {{ .gm-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 460px) {{ .gm-grid {{ grid-template-columns: 1fr; }} }}
.legend-row {{ display: flex; flex-wrap: wrap; gap: {S3}px; font-size: .85rem; color: {NAVY}; margin: {S1}px 0 {S2}px; }}

.case {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 4px; padding: {S4}px; position: relative; }}
.case .id {{ font-family: {MONO}; font-size: 1.8rem; font-weight: 600; margin: 0; line-height: 1.1; }}
.case .sub {{ color: {MUTED}; margin: {S1}px 0 {S3}px; font-size: .9rem; }}
.case .why {{ font-size: 1rem; margin: {S3}px 0 0; padding-top: {S3}px; border-top: 1px solid {BORDER}; }}
.case .slot-art {{ position: absolute; right: {S3}px; top: {S3}px; }}
.case .id, .case .sub {{ padding-right: 92px; }}
.checks {{ list-style: none; padding: 0; margin: {S2}px 0; }}
.checks li {{ display: grid; grid-template-columns: 30px 1fr auto; gap: {S2}px; align-items: start; padding: {S2}px 0; border-bottom: 1px solid {BORDER}; }}
.checks li:last-child {{ border-bottom: 0; }}
.checks .ic {{ width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: .9rem; }}
.checks .ic.yes {{ background: {TEAL_DARK}; color: {SURFACE}; }}
.checks .ic.maybe {{ background: {AMBER_SOFT}; color: {NAVY}; border: 1px solid {BORDER}; }}
.checks .ic.no {{ background: {SLATE_SOFT}; color: {NAVY}; border: 1px solid {BORDER}; }}
.checks .t {{ font-weight: 600; }} .checks .e {{ color: {MUTED}; font-size: .88rem; }}
.checks .r {{ font-family: {MONO}; font-size: .82rem; font-weight: 600; white-space: nowrap; padding-top: 3px; }}

.meter {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 4px; padding: {S3}px {S4}px; margin: {S2}px 0 {S3}px; }}
.meter-flex {{ display: flex; gap: {S4}px; align-items: center; }}
.meter-main {{ flex: 1; min-width: 0; }}
@media (max-width: 640px) {{ .meter-flex {{ flex-direction: column; align-items: stretch; }} .chips-art {{ align-self: center; }} }}
.zoomcard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 4px; padding: {S3}px; margin: {S2}px 0;
             display: grid; grid-template-columns: auto 1fr auto; gap: {S3}px; align-items: center; }}
.zoomcard .id {{ font-family: {MONO}; font-weight: 600; font-size: 1.35rem; }}
.zoomcard .why {{ font-size: .92rem; }} .zoomcard .meta {{ color: {MUTED}; font-size: .85rem; margin-top: 2px; }}
.zoomcard a {{ font-weight: 600; white-space: nowrap; }}
@media (max-width: 640px) {{ .zoomcard {{ grid-template-columns: 1fr; }} }}
.meter .row {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: {S2}px; }}
.meter .big {{ font-family: {MONO}; font-size: 1.7rem; font-weight: 600; }}
.meter .bar {{ height: 14px; background: {NAVY_RAISED}; border: 1px solid {BORDER}; border-radius: 2px; margin: {S2}px 0; overflow: hidden; }}
.meter .fill {{ height: 100%; background: {NAVY}; }}
.meter .fill.over {{ background: {DANGER}; }}
.meter .lbl {{ color: {MUTED}; font-size: .85rem; }}

.chip {{ white-space: nowrap; display: inline-block; padding: 2px {S2}px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; border: 1px solid {NAVY}44; }}

/* select popup lives in body (react-aria), outside the app container */
[data-testid="stSelectboxVirtualDropdown"], [data-testid="stMultiSelectDropdown"], [role="listbox"] {{ background: {SURFACE} !important; color: {NAVY}; }}
[data-testid="stSelectboxVirtualDropdown"], [data-testid="stMultiSelectDropdown"] {{ border: 1px solid {BORDER}; border-radius: 4px; }}
[role="listbox"] [role="option"], [role="listbox"] [role="option"] * {{ color: {NAVY} !important; }}
[role="listbox"] [role="option"] > div {{ background: transparent !important; border-radius: 3px; }}
[role="listbox"] [role="option"]:hover > div, [role="listbox"] [role="option"][data-focused] > div, [role="listbox"] [role="option"][data-focus-visible] > div,
[role="listbox"] [role="option"][data-hovered] > div {{ background: {NAVY_RAISED} !important; }}
[role="listbox"] [role="option"][aria-selected="true"] > div {{ font-weight: 700; box-shadow: inset 3px 0 0 {TEAL}; }}

/* date input field and its calendar popup (also in body) */
[data-testid="stDateInputField"] {{ background: {SURFACE} !important; border: 1px solid {BORDER}; border-radius: 4px; }}
[data-testid="stDateInputField"] input, [data-testid="stDateInputField"] span {{ color: {NAVY} !important; -webkit-text-fill-color: {NAVY}; }}
[data-testid="stDateInputCalendarButton"] svg {{ color: {NAVY}; }}
[data-testid="stDateInputCalendar"] {{ background: {SURFACE} !important; border: 1px solid {BORDER}; border-radius: 4px; }}
[data-testid="stDateInputCalendar"], [data-testid="stDateInputCalendar"] * {{ color: {NAVY} !important; }}
[data-testid="stDateInputCalendar"] [role="button"] {{ background: transparent !important; border-radius: 3px; }}
[data-testid="stDateInputCalendar"] [role="button"]:hover:not([data-disabled]) {{ background: {NAVY_RAISED} !important; }}
[data-testid="stDateInputCalendar"] [data-selected] {{ background: {AMBER_SOFT} !important; }}
[data-testid="stDateInputCalendar"] [data-selection-start], [data-testid="stDateInputCalendar"] [data-selection-end] {{ background: {NAVY} !important; color: {SURFACE} !important; font-weight: 700; }}
[data-testid="stDateInputCalendar"] [data-selection-start] *, [data-testid="stDateInputCalendar"] [data-selection-end] * {{ color: {SURFACE} !important; }}
[data-testid="stDateInputCalendar"] [data-selection-start]::after, [data-testid="stDateInputCalendar"] [data-selection-end]::after {{ background: {NAVY} !important; }}
[data-testid="stDateInputCalendar"] [data-outside-month], [data-testid="stDateInputCalendar"] [data-disabled] {{ color: {MUTED} !important; opacity: .6; }}

/* vega tooltip (appended to body) */
#vg-tooltip-element.vg-tooltip {{ background: {PANEL}; color: {NAVY}; border: 1px solid {NAVY}; border-radius: 4px; box-shadow: 4px 4px 0 {GRID}; font-family: {MONO}; font-size: .8rem; }}
#vg-tooltip-element.vg-tooltip td.key {{ color: {MUTED}; }}

/* expander header and native alerts were still near-white / yellow from the base theme */
[data-testid="stExpander"] summary {{ background: {SURFACE} !important; color: {NAVY}; border-radius: 4px; }}
[data-testid="stExpander"] summary:hover {{ background: {NAVY_RAISED} !important; }}
[data-testid="stAlertContainer"] {{ background: {PANEL} !important; color: {NAVY}; border: 1px solid {BORDER}; border-left: 4px solid {TEAL_DARK}; border-radius: 4px; }}

/* multiselect tags: ink on a raised sage chip with a border (the config teal gave white-on-teal) */
[data-testid="stMultiSelectTagsContainer"] span[role="group"] > span {{ background: {NAVY_RAISED} !important; border: 1px solid {NAVY}; border-radius: 4px; }}
[data-testid="stMultiSelectTagsContainer"] span[role="group"] > span, [data-testid="stMultiSelectTagsContainer"] span[role="group"] > span * {{ color: {NAVY} !important; }}
[data-testid="stMultiSelectTagsContainer"] svg {{ fill: {NAVY}; }}

/* widgets: config.toml paints them navy/teal; repaint as pale instrument wells */
[data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"], [data-testid="stMultiSelect"] [data-baseweb="select"] > div
  {{ background: {SURFACE} !important; border: 1px solid {BORDER}; border-radius: 4px; }}
[data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input {{ color: {NAVY} !important; -webkit-text-fill-color: {NAVY}; }}
[data-testid="stSelectbox"] [role="group"] > div:not(:has(input)), [data-testid="stSelectbox"] [role="group"] svg {{ color: {NAVY}; fill: {NAVY}; }}
[data-testid="stRadioOption"] > div:first-of-type > div:first-child {{ background: {SURFACE} !important; border: 2px solid {NAVY}; }}
[data-testid="stRadioOption"]:has(input:checked) > div:first-of-type > div:first-child {{ background: {NAVY} !important; }}
[data-testid="stRadioOption"]:has(input:checked) > div:first-of-type > div:first-child > div {{ background: {SURFACE} !important; }}
[data-testid="stButtonGroup"] button {{ background: {SURFACE} !important; color: {NAVY} !important; border: 1px solid {BORDER} !important; border-radius: 4px; }}
[data-testid="stButtonGroup"] button:hover {{ background: {NAVY_RAISED} !important; border-color: {NAVY} !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] {{ background: {NAVY} !important; color: {SURFACE} !important; border-color: {NAVY} !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] * {{ color: {SURFACE} !important; }}

/* reduced motion: tape and lamps stand still, hover lift off */
@media (prefers-reduced-motion: reduce) {{
  .ph::after, [data-testid="stMetric"]::after {{ animation: none; }}
  a.gm {{ transition: none; }} a.gm:hover {{ transform: none; }}
}}
"""

# ---- verdict mark colours (Okabe-Ito, same lightness nudges as OKABE_ITO); shapes live in theme.VERDICT_SHAPE
VERDICT_COLOR = {"Inspect": "#C24E00", "Bad spot": "#A86A00", "Short exposure": "#0072B2", "Unlucky": "#2A7DB8",
                 "Broken": "#000000", "Truly bad": "#000000", "Healthy": "#007F5F"}
