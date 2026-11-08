"""Skin: A. Noir Marquee (dark). Near-black plum, brass type, a hero framed by a chasing-bulb marquee.
Same token NAMES as default, different ROLES: CREAM = page background, SURFACE = card/chart panel, NAVY/TEXT = light ink,
SEAFOAM = table header / answer-box fill (dark), TEAL = brass for large text and fills, TEAL_DARK = lighter brass for small
text and links. Spec: design/DIRECTIONS.md section A. Evidence areas (charts, tables, metrics) stay flat: no glow, no animation."""
# ---- semantic colour tokens
NAVY = "#F3EADB"          # ink: headline, body text, single-series chart marks (light on dark)
NAVY_RAISED = "#2A2133"   # hover / active row, sidebar active row, tag and step-button fills
TEAL = "#D9A441"          # brass: nav marker, large text and fills only
TEAL_DARK = "#EBC37A"     # light brass: small text links, eyebrows
SEAFOAM = "#2A2133"       # table header fill, answer box fill, art labels (dark; art on the hero is re-inked in CSS)
CREAM = "#0F0C14"         # page background
SURFACE = "#1B1624"       # cards and chart panels
TEXT = NAVY
MUTED = "#B9AEA2"         # captions
BORDER = "#3B3248"
GRID = "#2A2333"          # chart gridlines, quieter than BORDER
EDGE = "#7A6E8C"          # component boundaries (inputs, bar track, pills): 3.74:1 on SURFACE, 4.10:1 on CREAM (WCAG 1.4.11); BORDER stays for hairlines

# ---- extra tokens
AMBER_SOFT = "#F5D9A0"    # pastel kept: "maybe" icon fill, Inspect chip
SLATE_SOFT = "#E2E8F0"    # pastel kept: "no" icon fill, Unlucky chip
DANGER = "#E5484D"        # over-budget bar (nudged from #B42318: 4.2:1 on SURFACE instead of 2.4:1); the words "Over budget" stay
HIGHLIGHT = "#E69F00"
HIGHLIGHT_SOFT = "#F5C26B"

S1, S2, S3, S4 = 4, 8, 16, 24

# Okabe-Ito on dark: blue lightened, black becomes the ink colour
OKABE_ITO = ["#3B9BE0", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#F3EADB"]
CHART_MARK = OKABE_ITO[0]  # single-series bar fill: blue (5.9:1 on SURFACE) instead of the cream ink, which made slabs

# ---- skin-only constants (not part of the seam)
INK = "#14101A"           # text on the pastel chips
SIDEBAR = "#07050A"
FOCUS = "#FFD27A"
RUBY, BRASS = "#FF4D8D", "#D9A441"  # marquee bulbs: decoration only, never text or meaning
DISPLAY = "'Bodoni Moda', Georgia, serif"

CHIPS = {  # (background, text); pastel fills as before, dark text
    "Inspect": (AMBER_SOFT, INK), "Short exposure": ("#A8DADC", INK), "Bad spot": ("#CFE3F3", INK),
    "Unlucky": (SLATE_SOFT, INK), "Healthy": ("#CDEBDD", INK), "Broken": ("#F4C7C0", INK), "Truly bad": ("#E8A59B", INK),
}
FONT = "'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
ALTAIR_FONT = "DM Sans"

VERDICT_COLOR = {"Inspect": "#D55E00", "Bad spot": "#E69F00", "Short exposure": "#3B9BE0", "Unlucky": "#56B4E9",
                 "Broken": "#F3EADB", "Truly bad": "#F3EADB", "Healthy": "#009E73"}  # shapes in theme.VERDICT_SHAPE still differ


def _ring():
    """Hero marquee: 8 background layers (ruby + brass bulb per edge); keyframes slide each edge one pitch (28px) around the frame."""
    dot = lambda c, ax, o: f"radial-gradient(circle at {o}px 3px, {c} 0 2.4px, transparent 2.9px)" if ax == "x" else \
        f"radial-gradient(circle at 3px {o}px, {c} 0 2.4px, transparent 2.9px)"
    edges = [("x", "28px 6px", "0 0", "28px 0", "repeat-x"), ("y", "6px 28px", "100% 0", "100% 28px", "repeat-y"),
             ("x", "28px 6px", "0 100%", "-28px 100%", "repeat-x"), ("y", "6px 28px", "0 0", "0 -28px", "repeat-y")]
    rows = [(dot(c, ax, o), s, f, t, r) for ax, s, f, t, r in edges for c, o in ((RUBY, 7), (BRASS, 21))]
    j = lambda i: ", ".join(r[i] for r in rows)
    return (f"background-image: {j(0)}; background-size: {j(1)}; background-position: {j(2)}; background-repeat: {j(4)};",
            f"@keyframes chase {{ from {{ background-position: {j(2)}; }} to {{ background-position: {j(3)}; }} }}")


_RING, _CHASE = _ring()
_RULE = (f"background-image: radial-gradient(circle at 7px 3px, {RUBY} 0 2.4px, transparent 2.9px), "
         f"radial-gradient(circle at 21px 3px, {BRASS} 0 2.4px, transparent 2.9px); background-size: 28px 6px; background-repeat: repeat-x;")

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:wght@600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
:root {{ color-scheme: dark; }}
html, body, .stApp, [data-testid="stAppViewContainer"], button, input, select, textarea, [data-baseweb="popover"], li {{ font-family: {FONT}; }}
.stApp {{ background: {CREAM}; color: {TEXT}; }}
::selection {{ background: {TEAL}; color: {INK}; }}
::placeholder {{ color: {MUTED}; opacity: 1; }}
hr {{ border-color: {BORDER}; }}
.block-container {{ padding: {S4}px {S4}px {S4}px; max-width: 1280px; }}
@media (max-width: 640px) {{ .block-container {{ padding: {S3}px {S3}px; }} }}
.stApp h1, .stApp h2, .stApp h3 {{ font-family: {DISPLAY}; padding: 0; }}
.stApp h1 {{ color: {NAVY}; font-size: 1.75rem; font-weight: 700; margin: 0 0 {S2}px; }}
.stApp h2 {{ color: {TEAL}; font-size: 1.3rem; font-weight: 600; margin: {S4}px 0 {S2}px; }}
.stApp h3 {{ color: {NAVY}; font-size: 1.1rem; font-weight: 600; margin: {S3}px 0 {S2}px; }}
p, li, td, th, label, span {{ font-variant-numeric: tabular-nums; }}
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p:not([class]),
[data-testid="stMarkdownContainer"] li {{ color: {NAVY}; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; opacity: 1 !important; font-size: 0.85rem; }}
a, a:visited {{ color: {TEAL_DARK}; text-decoration: underline; text-underline-offset: 2px; }}
code, pre {{ background: {SEAFOAM} !important; color: {TEAL_DARK} !important; }}
:focus-visible {{ outline: 3px solid {FOCUS}; outline-offset: 2px; }}

/* top bar (toolbar icons were dark on light) */
[data-testid="stHeader"] {{ background: {CREAM}; }}
[data-testid="stHeader"] button, [data-testid="stHeader"] span, [data-testid="stHeader"] a, [data-testid="stStatusWidget"] {{ color: {NAVY} !important; }}

/* sidebar: darker than the page, cream text, brass nav marker */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{ background: {SIDEBAR}; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color: {NAVY}; }}
[data-testid="stSidebar"] .sb-title {{ color: {NAVY}; font-weight: 600; font-size: 1.1rem; margin: 0 0 {S2}px; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 6px; border-left: 4px solid transparent; }}
[data-testid="stSidebarNavLink"]:hover {{ background: {NAVY_RAISED}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: {NAVY_RAISED}; border-left: 4px solid {TEAL}; font-weight: 600; }}
[data-testid="stSidebarNavLink"] span {{ color: {NAVY}; }}
/* the st.logo SVG (cream mark, cream title) already reads on this dark sidebar: no filter needed */

/* st.header / st.subheader inside pages */
[data-testid="stHeading"] h2, [data-testid="stHeadingWithActionElements"] h2 {{ font-size: 1.45rem !important; font-weight: 700; line-height: 1.3; margin-top: {S4}px; }}
[data-testid="stHeading"] h3, [data-testid="stHeadingWithActionElements"] h3 {{ font-size: 1.15rem !important; font-weight: 600; }}
[data-testid="stHeading"] a, [data-testid="stHeadingWithActionElements"] a {{ display: none; }}

/* KPI cards and chart panels: flat surface, 1px border, no glow */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: {S3}px; box-shadow: none; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.85rem; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] > div {{ overflow: visible !important; text-overflow: clip !important; }}
[data-testid="stMetricValue"] {{ color: {NAVY}; font-weight: 600; font-variant-numeric: tabular-nums; }}
[data-testid="stVegaLiteChart"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: {S2}px; box-sizing: border-box; }}
#vg-tooltip-element {{ background: {NAVY_RAISED} !important; color: {NAVY} !important; border: 1px solid {BORDER} !important; box-shadow: none !important; }}
#vg-tooltip-element .key {{ color: {MUTED} !important; }}

/* phone: KPI cards sit two per row instead of one tall stack */
@media (max-width: 640px) {{
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {{ min-width: calc(50% - {S2}px) !important; flex: 1 1 calc(50% - {S2}px) !important; }}
  [data-testid="stMetricValue"] {{ font-size: 1.2rem; }}
  [data-testid="stMetric"] {{ padding: {S2}px; }}
}}

/* panels */
.answer {{ background: {SEAFOAM}; border-left: 4px solid {NAVY}; border-radius: 4px; padding: {S3}px; margin: {S3}px 0; color: {NAVY}; }}
.answer p {{ margin: 0 0 {S2}px; }} .answer p:last-child {{ margin: 0; }}
.note {{ background: {SEAFOAM}66; border: 1px solid {BORDER}; border-left: 4px solid {TEAL_DARK}; border-radius: 4px;
        padding: {S2}px {S3}px; margin: {S2}px 0; color: {NAVY}; font-size: 0.95rem; }}
.takeaway {{ color: {NAVY}; font-weight: 600; margin: {S3}px 0 {S1}px; }}
[data-testid="stAlert"], [data-testid="stAlertContainer"] {{ background: {SURFACE} !important; border: 1px solid {BORDER}; border-radius: 8px; }}
[data-testid="stAlert"] p, [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {{ color: {NAVY} !important; }}

/* tables (st.table): dark header, wrapped text, scroll sideways on small screens */
[data-testid="stTable"] {{ overflow-x: auto; }}
[data-testid="stTable"] table {{ border: 1px solid {BORDER}; border-radius: 8px; border-collapse: separate; border-spacing: 0; background: {SURFACE}; width: 100%; }}
[data-testid="stTable"] th {{ background: {SEAFOAM}; color: {NAVY}; font-weight: 600; text-align: left; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; }}
[data-testid="stTable"] td {{ color: {NAVY}; padding: {S2}px {S3}px; border-bottom: 1px solid {BORDER}; vertical-align: top;
        white-space: normal; min-width: 72px; max-width: 520px; }}
[data-testid="stTable"] td [data-testid="stMarkdownContainer"], [data-testid="stTable"] td [data-testid="stMarkdownContainer"] p {{ color: inherit; }}  /* chip cells carry their own ink */
[data-testid="stTable"] tbody tr:hover td {{ background: {NAVY_RAISED}; }}
button[data-variant="pills"] {{ background: {SURFACE}; border: 1px solid {EDGE}; }}
button[data-variant="pills"], button[data-variant="pills"] p {{ color: {NAVY}; }}
button[data-variant="pills"]:hover {{ border-color: {TEAL}; }}
button[data-variant="pills"][aria-checked="true"] {{ background: {NAVY_RAISED} !important; border-color: {TEAL} !important; font-weight: 600; }}
[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 8px; background: {SURFACE}; }}
[data-testid="stExpander"] details, [data-testid="stExpander"] summary {{ background: {SURFACE}; color: {NAVY}; }}
[data-testid="stExpander"] summary:hover {{ background: {NAVY_RAISED}; }}
[data-testid="stExpander"] summary span, [data-testid="stExpander"] summary p {{ color: {NAVY}; }}

/* widgets (Streamlit 1.67 uses React Aria, not BaseWeb; config.toml is base=light so inputs are re-inked here) */
[data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"], [data-testid="stNumberInput"] [data-rac], [data-testid="stDateInput"] [data-rac] {{
  background: {SURFACE}; border-color: {EDGE}; }}
[data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
[data-testid="stSelectbox"] button, [data-testid="stMultiSelect"] button {{ color: {NAVY}; -webkit-text-fill-color: {NAVY}; }}
[data-testid="stSelectboxVirtualDropdown"] {{ background: {SURFACE}; border: 1px solid {BORDER}; }}
[role="listbox"], [role="option"] {{ background: {SURFACE}; color: {NAVY}; }}
[role="option"]:hover, [role="option"][data-focused="true"], [role="option"][aria-selected="true"] {{ background: {NAVY_RAISED}; }}
[data-testid="stPageLink"] a, [data-testid="stPageLink-NavLink"] {{ color: {TEAL_DARK}; }}
[data-testid="stRadioOption"] > div > div:first-child {{ background: {SURFACE} !important; border-color: {MUTED} !important; }}
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {{ background: {TEAL} !important; border-color: {TEAL} !important; }}
[data-testid="stRadioOption"] > div > div:first-child > div {{ background: {INK} !important; }}
[data-testid="stDateInputField"], [data-testid="stDateInputCalendar"] {{ background: {SURFACE}; border: 1px solid {EDGE}; }}
[data-testid="stDateInputCalendar"] [data-selected="true"] {{ color: {NAVY}; }}
[data-testid="stDateInputCalendar"] [data-selected="true"][data-selection-start="true"],[data-testid="stDateInputCalendar"] [data-selected="true"][data-selection-end="true"] {{ background: {TEAL}; color: {INK}; }}
:is([data-testid="stSelectbox"], [data-testid="stMultiSelect"]) input:focus-visible {{ outline: none; }}
:is([data-testid="stSelectbox"], [data-testid="stMultiSelect"]) [role="group"]:has(input:focus-visible) {{ outline: 3px solid {FOCUS}; outline-offset: 2px; }}
[data-testid="stMainMenuPopover"] {{ background: {SURFACE}; border: 1px solid {BORDER}; }}
[data-testid="stMainMenuPopover"] * {{ color: {NAVY}; }}
[data-testid="stMainMenuPopover"] button:hover {{ background: {NAVY_RAISED}; }}
[data-testid="stTooltipContent"] {{ background: {NAVY_RAISED}; border: 1px solid {BORDER}; color: {NAVY}; }}
[data-testid="stTooltipHoverTarget"] button, [data-testid="stTooltipHoverTarget"] svg {{ color: {MUTED}; stroke: {MUTED} !important; opacity: 1; }}
[data-tag] {{ background: {NAVY_RAISED}; color: {NAVY}; border: 1px solid {BORDER}; }}
[data-tag] svg {{ fill: {NAVY}; }}
[role="option"] span {{ color: {MUTED}; }}
[data-testid="stAlert"] {{ border-left-width: 4px; }}  /* the kind is also in the words; the stripe is a reinforcement */
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {{ border-left-color: {HIGHLIGHT}; }}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {{ border-left-color: {OKABE_ITO[2]}; }}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {{ border-left-color: {DANGER}; }}
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {{ border-left-color: {OKABE_ITO[0]}; }}

/* ===== brand, page header, hero, cards, map, checklist, meter ===== */
.block-container {{ padding-top: {S3}px; }}
[data-testid="stSidebar"] [data-testid="stLogo"] {{ height: 44px; max-width: 100%; }}
.sb-foot {{ color: {MUTED}; font-size: 0.75rem; line-height: 1.4; margin-top: {S4}px; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}

.ph {{ margin: {S2}px 0 {S3}px; }}
.ph::before {{ content: ""; display: block; height: 6px; margin-bottom: {S3}px; {_RULE} }}
.stApp:has(.hero) .ph::before {{ display: none; }}
.ph .eyebrow {{ color: {TEAL_DARK}; font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; margin-bottom: {S1}px; }}
.ph h1 {{ font-size: 2.1rem; font-weight: 700; letter-spacing: 0; margin: 0; line-height: 1.15; }}
.ph .q {{ color: {MUTED}; font-size: 1.05rem; margin: {S1}px 0 {S2}px; }}
.pills {{ display: flex; flex-wrap: wrap; gap: {S2}px; }}
.pill {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 999px; padding: 3px 12px; font-size: .8rem; color: {NAVY}; }}
.pill b {{ color: {TEAL_DARK}; font-weight: 600; margin-right: 4px; }}

/* signature: marquee bulbs chase around the Overview hero (static and fully lit under reduced motion) */
.hero {{ background: {SURFACE}; color: {NAVY}; border: 1px solid {BORDER}; border-radius: 12px; padding: {S4}px {S4}px {S3}px; margin: 0 0 {S4}px; position: relative; overflow: hidden; }}
.hero::before {{ content: ""; position: absolute; inset: 0; pointer-events: none; {_RING} animation: chase 2.4s linear 2; }}  /* 2 loops = 4.8s, then rests fully lit (28px pitch: end frame equals the static frame) */
.hero::after {{ content: ""; position: absolute; inset: 0; pointer-events: none; background-repeat: no-repeat;
  background-image: linear-gradient({TEAL}, {TEAL}), linear-gradient({TEAL}, {TEAL}), linear-gradient({TEAL}, {TEAL}), linear-gradient({TEAL}, {TEAL});
  background-size: 14px 1.5px, 1.5px 14px, 14px 1.5px, 1.5px 14px;
  background-position: 12px 12px, 12px 12px, calc(100% - 12px) calc(100% - 12px), calc(100% - 12px) calc(100% - 12px); }}
{_CHASE}
@media (max-width: 640px) {{ .hero::before {{ inset: 0 0 auto 0; height: 3px; animation: none; background-image: linear-gradient(90deg, {RUBY}, {BRASS}, {RUBY});
  background-size: 100% 3px; background-position: 0 0; background-repeat: no-repeat; }} .hero::after {{ display: none; }}
  .ph::before {{ height: 3px; background-image: linear-gradient(90deg, {RUBY}, {BRASS}, {RUBY}); background-size: 100% 3px; background-repeat: no-repeat; }} }}
.hero .copy {{ position: relative; z-index: 1; max-width: calc(100% - 360px); min-height: 212px; }}
.hero .hero-art {{ position: absolute; right: {S4}px; top: {S3}px; }}
@media (max-width: 1100px) {{ .hero .hero-art {{ display: none; }} .hero .copy {{ max-width: 100%; min-height: 0; }} }}
.hero .kicker {{ color: {TEAL_DARK}; font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }}
.hero h2 {{ color: {NAVY}; font-size: 2.2rem; font-weight: 700; letter-spacing: 0; margin: {S2}px 0 {S2}px; line-height: 1.1; }}
.hero p {{ color: {NAVY}; font-size: 1.02rem; margin: 0 0 {S1}px; max-width: 860px; }}
.hero .tiles {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: {S3}px; margin-top: {S4}px; position: relative; z-index: 1; }}
.hero .tile {{ border-top: 3px solid {TEAL}; padding-top: {S2}px; }}
.hero .tile .v {{ font-family: {DISPLAY}; font-size: 2rem; font-weight: 700; color: {TEAL}; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.hero .tile .l {{ font-size: .82rem; color: {MUTED}; margin-top: 2px; }}
@media (max-width: 760px) {{ .hero .tiles {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .hero h2 {{ font-size: 1.6rem; }} }}
/* the floor illustration was drawn for a navy hero: re-ink its dark-plum parts so they read on the dark panel */
.hero-art rect[fill="{SEAFOAM}"] {{ fill: {MUTED}; }}
.hero-art text[fill="{SEAFOAM}"] {{ fill: {MUTED}; }}
.hero-art path[stroke="{CREAM}"] {{ stroke: {NAVY}; }}
.hero-art circle {{ fill: {CREAM}; }}
.chips-art ellipse[fill="{SEAFOAM}"] {{ fill: {TEAL}; }}
.chips-art ellipse[opacity=".25"] {{ fill: #000; }}

.sec {{ display: flex; align-items: baseline; gap: {S2}px; margin: {S4}px 0 {S2}px; }}
.sec .n {{ color: {TEAL_DARK}; font-weight: 700; font-size: .9rem; }}
.sec h2 {{ margin: 0 !important; }}
.sec-sub {{ color: {MUTED}; margin: 0 0 {S3}px; font-size: .95rem; }}
.sec-sub b {{ color: {NAVY}; }}

.gm-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: {S3}px; margin: {S2}px 0 {S2}px; }}
a.gm, a.gm:visited {{ display: block; background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 8px;
     padding: {S3}px; color: {NAVY}; text-decoration: none; }}
a.gm:hover {{ border-color: {TEAL}; }}
@media (prefers-reduced-motion: no-preference) {{ a.gm {{ transition: transform .12s ease, border-color .12s ease; }} a.gm:hover {{ transform: translateY(-2px); }} }}
a.gm .top {{ display: flex; justify-content: space-between; align-items: center; gap: 6px; }}
a.gm .chip {{ font-size: .75rem; padding: 2px 8px; }}
a.gm .rank {{ font-size: .75rem; color: {MUTED}; font-weight: 600; letter-spacing: .06em; }}
a.gm .id {{ font-family: {DISPLAY}; font-size: 1.35rem; font-weight: 700; margin: {S1}px 0 2px; }}
a.gm .zone {{ font-size: .82rem; color: {MUTED}; margin-bottom: {S2}px; }}
a.gm .why {{ font-size: .85rem; line-height: 1.35; margin: {S2}px 0; min-height: 3.4em; }}
a.gm .meta {{ display: flex; gap: {S3}px; font-size: .78rem; color: {MUTED}; border-top: 1px solid {BORDER}; padding-top: {S2}px; }}
a.gm .meta b {{ color: {NAVY}; }}
a.gm .go {{ font-size: .78rem; color: {TEAL_DARK}; font-weight: 600; margin-top: {S2}px; }}
@media (max-width: 1200px) {{ .gm-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
@media (max-width: 760px) {{ .gm-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 460px) {{ .gm-grid {{ grid-template-columns: 1fr; }} }}
.legend-row {{ display: flex; flex-wrap: wrap; gap: {S3}px; font-size: .82rem; color: {NAVY}; margin: {S1}px 0 {S2}px; }}

.case {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; padding: {S4}px; position: relative; }}
.case .id {{ font-family: {DISPLAY}; font-size: 2rem; font-weight: 700; margin: 0; line-height: 1.1; }}
.case .sub {{ color: {MUTED}; margin: {S1}px 0 {S3}px; font-size: .9rem; }}
.case .why {{ font-size: 1rem; margin: {S3}px 0 0; padding-top: {S3}px; border-top: 1px solid {BORDER}; }}
.case .slot-art {{ position: absolute; right: {S3}px; top: {S3}px; }}
.case .id, .case .sub {{ padding-right: 92px; }}
.checks {{ list-style: none; padding: 0; margin: {S2}px 0; }}
.checks li {{ display: grid; grid-template-columns: 30px 1fr auto; gap: {S2}px; align-items: start; padding: {S2}px 0; border-bottom: 1px solid {BORDER}; }}
.checks li:last-child {{ border-bottom: 0; }}
.checks .ic {{ width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; font-size: .9rem; }}
.checks .ic.yes {{ background: {TEAL_DARK}; color: {INK}; }}
.checks .ic.maybe {{ background: {AMBER_SOFT}; color: {INK}; }}
.checks .ic.no {{ background: {SLATE_SOFT}; color: {INK}; }}
.checks .t {{ font-weight: 600; }} .checks .e {{ color: {MUTED}; font-size: .88rem; }}
.checks .r {{ font-size: .8rem; font-weight: 700; white-space: nowrap; padding-top: 3px; }}

.meter {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; padding: {S3}px {S4}px; margin: {S2}px 0 {S3}px; }}
.meter-flex {{ display: flex; gap: {S4}px; align-items: center; }}
.meter-main {{ flex: 1; min-width: 0; }}
@media (max-width: 640px) {{ .meter-flex {{ flex-direction: column; align-items: stretch; }} .chips-art {{ align-self: center; }} }}
.zoomcard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-left: 5px solid var(--vc); border-radius: 8px; padding: {S3}px; margin: {S2}px 0;
             display: grid; grid-template-columns: auto 1fr auto; gap: {S3}px; align-items: center; }}
.zoomcard .id {{ font-family: {DISPLAY}; font-weight: 700; font-size: 1.4rem; }}
.zoomcard .why {{ font-size: .92rem; }} .zoomcard .meta {{ color: {MUTED}; font-size: .82rem; margin-top: 2px; }}
.zoomcard a {{ font-weight: 600; white-space: nowrap; }}
@media (max-width: 640px) {{ .zoomcard {{ grid-template-columns: 1fr; }} }}
.meter .row {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: {S2}px; }}
.meter .big {{ color: {TEAL}; font-size: 1.8rem; font-weight: 700; }}
.meter .big .lbl {{ color: {MUTED}; font-size: .85rem; font-weight: 400; }}
.meter .bar {{ height: 14px; background: {BORDER}; box-shadow: 0 0 0 1px {EDGE}; border-radius: 999px; margin: {S2}px 0; overflow: hidden; }}
.meter .fill {{ height: 100%; background: {NAVY}; border-radius: 999px; }}
.meter .fill.over {{ background: {DANGER}; }}
.meter .lbl {{ color: {MUTED}; font-size: .85rem; }}

.chip {{ white-space: nowrap; display: inline-block; padding: 2px {S2}px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; border: 1px solid {NAVY}22; }}

@media (prefers-reduced-motion: reduce) {{
  .hero::before {{ animation: none !important; }}
  * {{ transition: none !important; }}
}}
"""
