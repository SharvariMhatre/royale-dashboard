"""Skin: paper (C. Editorial Case File). Warm paper, ink, one rubric red; Fraunces for display, Source Serif 4 for prose.
Same token names as every skin; roles here: CREAM = paper (page), SURFACE = card/chart panel, NAVY/TEXT = ink,
TEAL = TEAL_DARK = rubric red (accent at every size), SEAFOAM = table header / answer box / hero kicker, NAVY_RAISED = hover row.
The hero stays an ink panel (hero_floor() draws SEAFOAM/CREAM line art for a dark ground)."""
# ---- semantic colour tokens
NAVY = "#1E1A15"          # ink: headings, body text, ink panels (hero, meter fill)
NAVY_RAISED = "#E2D8C2"   # hover / active row
TEAL = "#9B2C1F"          # rubric red: accent, nav marker, section numerals, links
TEAL_DARK = "#9B2C1F"     # same rubric: 4.5:1 on paper, card and sidebar tab
SEAFOAM = "#E2D8C2"       # table header, answer box, art labels on the ink hero
CREAM = "#F3ECDD"         # paper (page background)
SURFACE = "#FBF7EC"       # cards and chart panels
TEXT = NAVY
MUTED = "#5B5246"         # captions
BORDER = "#CDBFA3"
GRID = "#E2D8C2"          # chart gridlines

# ---- extra tokens (unchanged from default: pastel fills and art highlights already work on paper)
AMBER_SOFT = "#F5D9A0"
SLATE_SOFT = "#E2E8F0"
DANGER = "#B42318"
HIGHLIGHT = "#E69F00"
HIGHLIGHT_SOFT = "#F5C26B"

S1, S2, S3, S4 = 4, 8, 16, 24

# ---- Okabe-Ito, orange and sky darkened a touch so every mark keeps >= 3:1 on SURFACE; black stays black (paper is light)
OKABE_ITO = ["#0072B2", "#B87700", "#007F5F", "#D55E00", "#2A86C4", "#000000"]
CHART_MARK = NAVY  # single-series bar fill (T.bars color=): the ink, as before

CHIPS = {
    "Inspect": (AMBER_SOFT, NAVY), "Short exposure": (SEAFOAM, NAVY), "Bad spot": ("#CFE3F3", NAVY),
    "Unlucky": (SLATE_SOFT, NAVY), "Healthy": ("#CDEBDD", NAVY), "Broken": ("#F4C7C0", NAVY), "Truly bad": ("#E8A59B", NAVY),
}
VERDICT_COLOR = {"Inspect": OKABE_ITO[3], "Bad spot": OKABE_ITO[1], "Short exposure": OKABE_ITO[0], "Unlucky": OKABE_ITO[4],
                 "Broken": OKABE_ITO[5], "Truly bad": OKABE_ITO[5], "Healthy": OKABE_ITO[2]}

FONT = "'Source Serif 4', Georgia, 'Times New Roman', serif"
ALTAIR_FONT = "Source Serif 4"
DISPLAY = "Fraunces, Georgia, 'Times New Roman', serif"
TAB = "#E7DDC8"           # sidebar background (a paper tab)
FOCUS = "#1F4E8C"         # focus ring: 6.2:1 or better on paper, card and tab
# paper grain: tiny SVG noise at 4% opacity, on the page background only (never behind a chart or table)
GRAIN = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E"
         "%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix "
         "values='0 0 0 0 .3 0 0 0 0 .25 0 0 0 0 .15 0 0 0 .6 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' "
         "filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E\")")

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], p, li, td, th, label, button, input, select, textarea, [data-baseweb] {{ font-family: {FONT}; }}
body .stApp {{ background-color: {CREAM}; background-image: {GRAIN}; color: {TEXT}; font-variant-numeric: tabular-nums lining-nums; }}
body [data-testid="stAppViewContainer"] {{ background: transparent; }}
body [data-testid="stHeader"] {{ background: {CREAM}; }}
.block-container {{ padding: {S3}px {S4}px {S4}px; max-width: 1280px; position: relative; }}
.block-container::before {{ content: ""; position: absolute; left: {S2}px; top: 0; bottom: 0; border-left: 1px solid {BORDER}; }}
@media (max-width: 640px) {{ .block-container {{ padding: {S3}px; }} .block-container::before {{ display: none; }} }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stWidgetLabel"] p {{ color: {NAVY}; line-height: 1.55; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{ font-family: {DISPLAY}; color: {NAVY}; font-variant-numeric: lining-nums; }}
h1 {{ font-size: 1.9rem; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 {S2}px; padding: 0; }}
h2 {{ font-size: 1.3rem; font-weight: 600; margin: {S4}px 0 {S2}px; padding: 0; }}
h3 {{ font-size: 1.1rem; font-weight: 600; margin: {S3}px 0 {S2}px; padding: 0; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; opacity: 1 !important; font-size: 0.85rem; }}
a, a:visited {{ color: {TEAL_DARK}; text-decoration: underline; text-underline-offset: 2px; }}
:focus-visible, [data-testid="stSidebar"] :focus-visible {{ outline: 3px solid {FOCUS}; outline-offset: 2px; }}

/* sidebar: a paper tab with ink text. The config.toml sidebar theme is dark, so its widgets are restyled below. */
body [data-testid="stSidebar"], body [data-testid="stSidebarContent"], body [data-testid="stSidebarHeader"] {{ background-color: {TAB}; color: {NAVY}; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color: {NAVY}; }}
[data-testid="stSidebar"] .sb-title {{ font-family: {DISPLAY}; color: {NAVY}; font-weight: 700; font-size: 1.15rem; margin: 0 0 {S2}px; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}
[data-testid="stSidebarHeader"] button, [data-testid="stSidebarHeader"] button *, [data-testid="stSidebarCollapseButton"] * {{ color: {NAVY} !important; fill: currentColor; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 2px; border-left: 4px solid transparent; }}
[data-testid="stSidebarNavLink"]:hover {{ background: {NAVY_RAISED}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: {SURFACE}; border-left: 4px solid {TEAL}; font-weight: 600; }}
[data-testid="stSidebarNavLink"] span {{ color: {NAVY}; }}
/* the logo SVG is drawn for a dark sidebar (cream square, cream title): invert lightness, keep hue */
[data-testid="stSidebarLogo"] {{ height: 44px; max-width: 100%; filter: invert(1) hue-rotate(180deg); }}
.sb-foot {{ color: {MUTED}; font-size: 0.78rem; line-height: 1.4; margin-top: {S4}px; }}
/* radio: Streamlit 1.67 draws a pale disc for the dark sidebar theme; outline it, fill rubric when chosen (inner dot stays white) */
[data-testid="stRadioOption"] > div > div:first-child {{ background-color: {SURFACE}; border-color: {MUTED}; }}
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {{ background-color: {TEAL}; border-color: {TEAL}; }}

/* zone pills (st.pills): square paper tabs, ink fill when chosen */
body button[role="radio"] {{ background-color: {SURFACE}; border: 1px solid {MUTED}; border-radius: 2px; color: {NAVY}; }}
body button[role="radio"] * {{ color: inherit !important; }}
body button[role="radio"][aria-checked="true"] {{ background-color: {NAVY} !important; color: {CREAM} !important; border-color: {NAVY} !important; }}

/* inputs and popups (react-aria in 1.67, not BaseWeb): flat card fill, ink text, visible 3:1 outline */
[data-testid="stSelectbox"] [role="group"], [data-testid="stTextInput"] [role="group"], [data-testid="stMultiSelect"] div[role="group"], [data-testid="stDateInput"] > div > div {{ background-color: {SURFACE}; border: 1px solid {MUTED}; border-radius: 2px; }}
body input, body [data-testid="stSelectbox"] button, body [data-testid="stSelectbox"] svg {{ color: {NAVY}; -webkit-text-fill-color: {NAVY}; }}
[data-testid="stSelectboxVirtualDropdown"], [role="listbox"] {{ background-color: {SURFACE}; color: {NAVY}; border: 1px solid {MUTED}; border-radius: 2px; }}
[data-testid="stMultiSelect"] [data-tag] {{ background-color: {SEAFOAM} !important; color: {NAVY} !important; border: 1px solid {MUTED}; border-radius: 2px; }}
[data-testid="stDateInput"] [role="group"], [data-testid="stDateInput"] .react-aria-DateField {{ background: transparent !important; border: 0 !important; }}
body [data-testid="stDateInput"] button, body [data-testid="stDateInputCalendar"] button, body [data-testid="stDateInputCalendar"] td [role="button"] {{ color: {NAVY} !important; }}
[data-testid="stDateInputCalendar"] {{ background-color: {SURFACE}; border: 1px solid {MUTED}; border-radius: 2px; }}
body [data-testid="stDateInputCalendar"] th {{ color: {MUTED}; }}
body [data-testid="stDateInputCalendar"] td [data-selected] {{ background-color: {SEAFOAM} !important; color: {NAVY} !important; }}
body [data-testid="stDateInputCalendar"] td [data-selection-start], body [data-testid="stDateInputCalendar"] td [data-selection-end] {{ background-color: {TEAL} !important; color: {CREAM} !important; }}
body [data-testid="stDateInputCalendar"] td [data-selection-start]::after, body [data-testid="stDateInputCalendar"] td [data-selection-end]::after {{ background-color: {TEAL} !important; }}
body [data-testid="stDateInputCalendar"] [data-disabled] {{ color: {MUTED}; opacity: .6; }}
[role="option"] {{ background-color: {SURFACE}; color: {NAVY}; }}
[role="option"]:hover, [role="option"][data-focused="true"], [role="option"][aria-selected="true"] {{ background-color: {NAVY_RAISED}; }}

/* st.header / st.subheader inside pages */
[data-testid="stHeading"] h2, [data-testid="stHeadingWithActionElements"] h2 {{ font-size: 1.45rem !important; font-weight: 700; line-height: 1.3; margin-top: {S4}px; }}
[data-testid="stHeading"] h3, [data-testid="stHeadingWithActionElements"] h3 {{ font-size: 1.15rem !important; font-weight: 600; }}
[data-testid="stHeading"] a, [data-testid="stHeadingWithActionElements"] a {{ display: none; }}

/* KPI cards and charts: flat panels, hairline border, no shadow, no texture */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 2px; padding: {S3}px; box-shadow: none; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.85rem; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] > div {{ overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] {{ color: {NAVY}; font-weight: 600; font-variant-numeric: tabular-nums lining-nums; }}
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {{ background: {SURFACE}; box-shadow: inset 0 0 0 1px {BORDER}; border-radius: 2px; }}

/* phone: KPI cards sit two per row instead of one tall stack */
@media (max-width: 640px) {{
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {{ min-width: calc(50% - {S2}px) !important; flex: 1 1 calc(50% - {S2}px) !important; }}
  [data-testid="stMetricValue"] {{ font-size: 1.5rem; }}
}}

/* panels */
.answer {{ background: {SEAFOAM}; border-left: 4px solid {TEAL}; border-radius: 0 2px 2px 0; padding: {S3}px; margin: {S3}px 0; color: {NAVY}; }}
.answer p {{ margin: 0 0 {S2}px; }} .answer p:last-child {{ margin: 0; }}
.note {{ background: {SEAFOAM}33; border: 1px solid {BORDER}; border-left: 4px solid {TEAL_DARK}; border-radius: 0 2px 2px 0;
        padding: {S2}px {S3}px; margin: {S2}px 0; color: {NAVY}; font-size: 0.95rem; }}
.takeaway {{ color: {NAVY}; font-weight: 600; margin: {S3}px 0 {S1}px; }}

/* tables (st.table): body face at 14px+, paper-tone header, wrapped text, scroll sideways on small screens */
[data-testid="stTable"] {{ overflow-x: auto; border-radius: 2px; }}
[data-testid="stTable"] table {{ border: 1px solid {BORDER}; border-radius: 2px; border-collapse: separate; border-spacing: 0; background: {SURFACE}; width: 100%; }}
[data-testid="stTable"] th {{ background: {SEAFOAM}; color: {NAVY}; font-weight: 600; font-size: .9rem; text-align: left; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; }}
[data-testid="stTable"] td {{ color: {NAVY}; font-size: .9rem; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; vertical-align: top;
        white-space: normal; min-width: 72px; max-width: 520px; }}
[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 2px; background: {SURFACE}; }}
[data-testid="stExpander"] details, [data-testid="stExpander"] summary {{ border: 0; border-radius: 2px; }}

/* verdict chips become stamps: square corners, ink border, a slight tilt (never inside a table, never on a phone) */
.chip {{ white-space: nowrap; display: inline-block; padding: 2px {S2}px; border-radius: 2px; font-size: 0.85rem; font-weight: 600;
        letter-spacing: .02em; border: 1.5px solid {NAVY}; transform: rotate(-1.5deg); }}
[data-testid="stTable"] .chip, td .chip {{ transform: none; }}
@media (max-width: 640px) {{ .chip {{ transform: none; }} }}

/* ===== brand, page header, hero, cards, map, checklist, meter ===== */
.ph {{ margin: {S2}px 0 {S3}px; }}
.ph .eyebrow {{ color: {TEAL_DARK}; font-size: .95rem; font-weight: 600; font-variant-caps: small-caps; letter-spacing: .1em; margin-bottom: {S1}px; }}
.ph h1 {{ font-size: 2.1rem; font-weight: 700; letter-spacing: -0.015em; margin: 0; line-height: 1.15; }}
.ph .q {{ color: {MUTED}; font-size: 1.1rem; font-style: italic; margin: {S1}px 0 {S2}px; }}
.pills {{ display: flex; flex-wrap: wrap; gap: {S2}px; }}
.pill {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 2px; padding: 3px 12px; font-size: .85rem; color: {NAVY}; }}
.pill b {{ color: {TEAL_DARK}; font-weight: 600; margin-right: 4px; }}

.hero {{ background: {NAVY}; color: {CREAM}; border-radius: 2px; padding: {S4}px {S4}px {S3}px; margin: 0 0 {S4}px; position: relative; overflow: hidden;
        box-shadow: inset 0 0 0 4px {NAVY}, inset 0 0 0 5px {MUTED}; }}
.hero .copy {{ position: relative; z-index: 1; max-width: calc(100% - 360px); min-height: 212px; }}
.hero .hero-art {{ position: absolute; right: {S4}px; top: {S3}px; }}
.hero .hero-art rect[stroke="{TEAL}"] {{ stroke: {SEAFOAM}; stroke-opacity: .6; }}
@media (max-width: 1100px) {{ .hero .hero-art {{ display: none; }} .hero .copy {{ max-width: 100%; min-height: 0; }} }}
.hero .kicker {{ color: {SEAFOAM}; font-size: .95rem; font-weight: 600; font-variant-caps: small-caps; letter-spacing: .1em; }}
.hero h2 {{ font-family: {DISPLAY}; color: {CREAM}; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.015em; margin: {S2}px 0 {S2}px; line-height: 1.12; }}
.hero p {{ color: {CREAM}; font-size: 1.05rem; margin: 0 0 {S1}px; max-width: 860px; }}
.hero .tiles {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: {S3}px; margin-top: {S4}px; position: relative; z-index: 1; }}
.hero .tile {{ border-top: 1px solid {SEAFOAM}; padding-top: {S2}px; }}
.hero .tile .v {{ font-family: {DISPLAY}; font-size: 2rem; font-weight: 700; color: {SEAFOAM}; line-height: 1.1; font-variant-numeric: tabular-nums lining-nums; }}
.hero .tile .l {{ font-size: .88rem; color: {CREAM}; margin-top: 2px; }}
@media (max-width: 760px) {{ .hero .tiles {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .hero h2 {{ font-size: 1.6rem; }} }}

/* sections read as a case file: double rule above, rubric numeral in a ruled gutter (inline above the heading on a phone) */
.sec {{ display: flex; align-items: baseline; gap: {S3}px; margin: {S4 + S2}px 0 {S2}px; padding-top: {S3}px; border-top: 3px double {BORDER}; }}
.sec .n {{ font-family: {DISPLAY}; color: {TEAL}; font-weight: 700; font-size: 1.5rem; line-height: 1.2; min-width: 2.4rem; text-align: right;
          padding-right: {S3}px; border-right: 1px solid {BORDER}; font-variant-numeric: lining-nums; }}
.sec h2 {{ margin: 0 !important; }}
@media (max-width: 640px) {{ .sec {{ flex-direction: column; gap: 0; }} .sec .n {{ border-right: 0; padding-right: 0; text-align: left; min-width: 0; }} }}
.sec-sub {{ color: {MUTED}; margin: 0 0 {S3}px; font-size: .98rem; }}
.sec-sub b {{ color: {NAVY}; }}

.gm-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: {S3}px; margin: {S2}px 0 {S2}px; }}
a.gm, a.gm:visited {{ display: block; background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 2px;
     padding: {S3}px; color: {NAVY}; text-decoration: none; transition: border-color .12s ease; }}
a.gm:hover {{ border-color: {TEAL}; border-left-color: var(--vc); }}
a.gm .top {{ display: flex; justify-content: space-between; align-items: center; gap: 6px; }}
a.gm .chip {{ font-size: .78rem; padding: 2px 8px; }}
a.gm .rank {{ font-size: .78rem; color: {MUTED}; font-weight: 600; letter-spacing: .06em; }}
a.gm .id {{ font-family: {DISPLAY}; font-size: 1.35rem; font-weight: 700; margin: {S1}px 0 2px; }}
a.gm .zone {{ font-size: .85rem; color: {MUTED}; margin-bottom: {S2}px; }}
a.gm .why {{ font-size: .88rem; line-height: 1.4; margin: {S2}px 0; min-height: 3.4em; }}
a.gm .meta {{ display: flex; gap: {S3}px; font-size: .8rem; color: {MUTED}; border-top: 1px solid {BORDER}; padding-top: {S2}px; }}
a.gm .meta b {{ color: {NAVY}; }}
a.gm .go {{ font-size: .8rem; color: {TEAL_DARK}; font-weight: 600; margin-top: {S2}px; }}
@media (max-width: 1200px) {{ .gm-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
@media (max-width: 760px) {{ .gm-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 460px) {{ .gm-grid {{ grid-template-columns: 1fr; }} }}
.legend-row {{ display: flex; flex-wrap: wrap; gap: {S3}px; font-size: .85rem; color: {NAVY}; margin: {S1}px 0 {S2}px; }}

.case {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 2px; padding: {S4}px; position: relative; }}
.case .id {{ font-family: {DISPLAY}; font-size: 2rem; font-weight: 700; margin: 0; line-height: 1.1; }}
.case .sub {{ color: {MUTED}; margin: {S1}px 0 {S3}px; font-size: .92rem; }}
.case .why {{ font-size: 1.02rem; margin: {S3}px 0 0; padding-top: {S3}px; border-top: 1px solid {BORDER}; }}
.case .slot-art {{ position: absolute; right: {S3}px; top: {S3}px; }}
.case .id, .case .sub {{ padding-right: 92px; }}
.checks {{ list-style: none; padding: 0; margin: {S2}px 0; }}
.checks li {{ display: grid; grid-template-columns: 30px 1fr auto; gap: {S2}px; align-items: start; padding: {S2}px 0; border-bottom: 1px solid {BORDER}; }}
.checks li:last-child {{ border-bottom: 0; }}
.checks .ic {{ width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; font-size: .9rem; }}
.checks .ic.yes {{ background: {NAVY}; color: {CREAM}; }}
.checks .ic.maybe {{ background: {AMBER_SOFT}; color: {NAVY}; }}
.checks .ic.no {{ background: {SLATE_SOFT}; color: {NAVY}; }}
.checks .t {{ font-weight: 600; }} .checks .e {{ color: {MUTED}; font-size: .9rem; }}
.checks .r {{ font-size: .85rem; font-weight: 700; white-space: nowrap; padding-top: 3px; }}

.meter {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 2px; padding: {S3}px {S4}px; margin: {S2}px 0 {S3}px; }}
.meter-flex {{ display: flex; gap: {S4}px; align-items: center; }}
.meter-main {{ flex: 1; min-width: 0; }}
@media (max-width: 640px) {{ .meter-flex {{ flex-direction: column; align-items: stretch; }} .chips-art {{ align-self: center; }} }}
.zoomcard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 2px; padding: {S3}px; margin: {S2}px 0;
             display: grid; grid-template-columns: auto 1fr auto; gap: {S3}px; align-items: center; }}
.zoomcard .id {{ font-family: {DISPLAY}; font-weight: 700; font-size: 1.4rem; }}
.zoomcard .why {{ font-size: .95rem; }} .zoomcard .meta {{ color: {MUTED}; font-size: .85rem; margin-top: 2px; }}
.zoomcard a {{ font-weight: 600; white-space: nowrap; }}
@media (max-width: 640px) {{ .zoomcard {{ grid-template-columns: 1fr; }} }}
.meter .row {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: {S2}px; }}
.meter .big {{ font-family: {DISPLAY}; font-size: 1.8rem; font-weight: 700; font-variant-numeric: lining-nums; }}
.meter .bar {{ height: 14px; background: {SEAFOAM}; border: 1px solid {BORDER}; border-radius: 2px; margin: {S2}px 0; overflow: hidden; }}
.meter .fill {{ height: 100%; background: {NAVY}; }}
.meter .fill.over {{ background: {DANGER}; }}
.meter .lbl {{ color: {MUTED}; font-size: .88rem; }}

@media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ animation: none !important; transition: none !important; }} }}
"""
