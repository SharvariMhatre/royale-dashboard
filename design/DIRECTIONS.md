# Phase 1: three skin directions (for Checkpoint 2)

Status: **proposal, nothing built.** Written 2026-11-07 against HEAD `8901dd9`. Replaceable: say "change X" and I rewrite only that brief.

## What does not change (all three)
- **Zero copy changes.** No new visible words. Every decorative element below is CSS (pseudo-elements, gradients, keyframes) or inline SVG with `aria-hidden`, and contains no text. If a brief ever needs a word, I ask first.
- Same token names as today (`NAVY, TEAL, CREAM, SURFACE, MUTED, SEAFOAM, TEXT, BORDER, GRID, TEAL_DARK, NAVY_RAISED, CHIPS, OKABE_ITO, VERDICT_COLOR`). In a skin the *name* stays but the *role* is written next to it (e.g. in Noir, `CREAM` = page background, `NAVY` = headline/body text colour, so it is light). `test_theme.py` will loop contrast pairs per skin.
- Colour is never the only carrier of meaning: verdict text, shapes, dash patterns and direct labels stay as they are. Okabe-Ito hues keep their identity; only lightness is nudged where a background needs it (listed per skin).
- `prefers-reduced-motion: reduce` turns every animation off and shows the static end state.
- No iframe, no new Python dependency, fonts via `@import` in the existing `<style>` (same mechanism as today's Inter).
- Sidebar stays expanded-capable and unchanged in structure: period, bank and guest-group filters are the judge paths and must stay obvious.

## At a glance
| | A. Noir Marquee | B. Pit-Boss Control Room | C. Editorial Case File |
|---|---|---|---|
| Tone | dark, cinematic | mid-tone, operational | light paper, narrative |
| Display / body type | Bodoni Moda / DM Sans | IBM Plex Mono / IBM Plex Sans | Fraunces / Source Serif 4 |
| Palette logic | near-black plum + brass, ruby neon as decoration | sage-grey frame, pale instrument panels, amber lamps | warm paper, ink, one rubric red |
| Density | airy, large type | dense, small panels, 8px rhythm | generous measure, long-form |
| Signature moment | marquee-bulb chase around the Overview hero | status lamps on every KPI plus a text-free scanning tick-tape under the page header | numbered margin rule and stamp-style verdict chips; sections read as a case file |
| Where evidence stays calm | charts and tables sit on flat `#1B1624` panels; no animation near them | charts sit in flat pale panels; tape only above the header | charts sit on paper; no texture behind data |
| Main risk | BaseWeb popups and inputs are light from `config.toml` | many `data-testid` rules and dense UI at 390px | webfont load shifts layout; serif numerals |

## Contrast method
WCAG 2.x relative-luminance formula, computed by a script (`contrast.py`, scratchpad; every pair below is a computed value, not an estimate). Thresholds: text 4.5:1, large text and UI marks 3:1. These are palette-level numbers; real rendered pairs get re-checked with axe in Phase 4 (**unverified until built**).

---

## A. Noir Marquee (the one dark skin)

**Idea.** Casino at night: near-black plum, brass type, a hero framed by a chasing-bulb marquee. Evidence areas are flat and quiet.

**Tokens (role → value)**
| Role | Token | Value |
|---|---|---|
| Page background | `CREAM` | `#0F0C14` |
| Card / chart panel | `SURFACE` | `#1B1624` |
| Sidebar background | (sidebar bg) | `#07050A` |
| Body and heading text | `NAVY` / `TEXT` | `#F3EADB` |
| Captions | `MUTED` | `#B9AEA2` |
| Accent for large text, fills, nav marker | `TEAL` | `#D9A441` (brass) |
| Accent for small text and links | `TEAL_DARK` | `#EBC37A` |
| Table header fill | `SEAFOAM` | `#2A2133` |
| Hover / active row | `NAVY_RAISED` | `#2A2133` |
| Border / gridline | `BORDER` / `GRID` | `#3B3248` / `#2A2333` |
| Focus ring | | `#FFD27A` |
| Marquee bulbs (decorative only) | | `#FF4D8D` ruby, `#D9A441` brass |
| Chart marks (Okabe-Ito) | `OKABE_ITO` | blue `#3B9BE0` (lightened), orange `#E69F00`, green `#009E73`, vermillion `#D55E00`, sky `#56B4E9`, black → `#F3EADB` (black is invisible on dark) |
| Verdict chips | `CHIPS` | today's pastel fills kept; chip text `#14101A` |
| Verdict marks | `VERDICT_COLOR` | as chart marks; "Broken" and "Truly bad" use `#F3EADB` (shapes already differ: triangle-down, wedge) |

**Type.** Bodoni Moda 600/700 for H1/H2, hero and machine IDs (high-contrast Didone = marquee lettering); DM Sans 400/500/600 for everything else; tabular numerals on. Fallbacks: `Georgia` and `system-ui`.

**Signature moment.** Overview hero is wrapped by a 6px row of "bulbs" (a repeating radial-gradient mask) that chase around the border via an animated `background-position`; two corner flourishes are inline SVG. Reduced motion: bulbs static, all lit. The same bulb motif appears once more as a thin divider above the page header on other pages (static there).

**Where evidence stays calm.** Charts, tables, KPI cards, `st.metric` values and the model-validation block: flat surface, 1px border, no glow, no animation, no gradients. Brass appears only on the nav marker, headings, links and large numerals.

**WCAG AA plan (computed)**
| Pair | Ratio | Need |
|---|---:|---:|
| text `#F3EADB` on page `#0F0C14` | 16.25 | 4.5 |
| text on surface `#1B1624` | 14.83 | 4.5 |
| muted `#B9AEA2` on page / surface | 8.90 / 8.12 | 4.5 |
| text on sidebar `#07050A` / muted on sidebar | 17.01 / 9.31 | 4.5 |
| link `#EBC37A` on page / surface / sidebar | 11.65 / 10.63 / 12.19 | 4.5 |
| brass `#D9A441` (large, UI) on page / surface | 8.62 / 7.87 | 3 |
| focus `#FFD27A` on page / surface / sidebar | 13.62 / 12.43 / 14.25 | 3 |
| table header text on `#2A2133` | 12.91 | 4.5 |
| chart marks on `#1B1624`, lowest (vermillion) | 4.58 | 3 |
| chip text `#14101A` on chip fill, lowest | 9.19 | 4.5 |

All pass. Neon ruby is decoration only and is never a text or meaning colour.

**Mobile (390px).** Bulb ring drops to a static 3px top rule; hero art hidden (as today below 1100px); KPI cards stay two per row; Bodoni drops to 1.6rem for H2 (today's rule); sidebar collapses as Streamlit does.

**Popup / portal plan.** Highest effort of the three. `config.toml` is `base = "light"`, so BaseWeb selectboxes, the date-picker calendar, dropdown menus and tooltips would be white-on-white or light-on-light. The skin must override `[data-baseweb="popover"]`, `[data-baseweb="menu"]`, `[data-baseweb="calendar"]`, `[role="listbox"]`, `[role="option"]` (hover/selected), input and select interiors, `st.table`, `st.expander`, tooltips and the status/alert boxes. Verify with a selectbox open and the date picker open, at 1440 and 390. Selector stability: Streamlit gives no promise; version is pinned at 1.67.0. The "winner becomes default" step would also want a matching `config.toml` (needs your approval by name).

**Main risk.** A missed light popup or input makes a filter unreadable, and filters are a judge path. Mitigation: popup checklist is a gate in Phase 3, and A is the only skin that has it.

**Reduced motion.** Bulbs static; no hover transforms.

---

## B. Pit-Boss Control Room (mid-tone)

**Idea.** The floor manager's console: sage-grey frame, pale instrument panels, monospaced figures, amber status lamps. Dense, useful, a little industrial.

**Tokens**
| Role | Token | Value |
|---|---|---|
| Page background (the "wall") | `CREAM` | `#C5CDC2` |
| Card | `SURFACE` | `#E9EDE4` |
| Chart panel (charts only; keeps marks at 3:1) | | `#F4F6F0` |
| Sidebar background | | `#A9B6AE` |
| Text | `NAVY` / `TEXT` | `#101820` |
| Captions | `MUTED` | `#34423F` |
| Accent, large / lamps / nav marker | `TEAL` | `#A64F00` (amber, darkened) |
| Accent, small text and links | `TEAL_DARK` | `#6E3600` |
| Table header fill / text | `SEAFOAM` | `#2A3838` / `#F2F4EE` |
| Hover / active row | `NAVY_RAISED` | `#B9C5BD` |
| Border / gridline | `BORDER` / `GRID` | `#7F8F88` / `#AEB9B1` |
| Focus ring | | `#003F7F` |
| Chart marks (Okabe-Ito) | `OKABE_ITO` | blue `#0072B2`, orange `#A86A00`, green `#007F5F`, vermillion `#C24E00`, sky `#2A7DB8`, black `#000000` |
| Verdict chips | `CHIPS` | today's pastel fills; chip text `#101820` |

**Type.** IBM Plex Mono 500/600 for numerals, KPI values, IDs, table figures and small caps labels; IBM Plex Sans 400/600 for prose and headings. Tabular figures are native to Plex Mono. Fallbacks: `ui-monospace`, `system-ui`.

**Signature moment.** (1) A 10px text-free "tick-tape" under the page header: a repeating-linear-gradient of tick marks that scrolls slowly (CSS `background-position` animation). (2) Each `st.metric` card gets a small status lamp (an 8px circle in the card's corner, amber, with a soft pulse). Both are `::before` / `::after` pseudo-elements: no text, decoration only. No ticker with words, to honour zero copy change. Reduced motion: tape static, lamps steady.

**Where evidence stays calm.** All charts sit in the pale `#F4F6F0` panel (this is also what makes the marks pass 3:1). Tables are flat with a dark header strip. Lamps and tape live only on the header and KPI cards, never inside a chart or table.

**WCAG AA plan (computed)**
| Pair | Ratio | Need |
|---|---:|---:|
| text `#101820` on page / surface | 10.98 / 15.08 | 4.5 |
| muted `#34423F` on page / surface / sidebar | 6.45 / 8.86 / 5.00 | 4.5 |
| text on sidebar `#A9B6AE` | 8.51 | 4.5 |
| link `#6E3600` on page / surface / sidebar | 5.88 / 8.08 / 4.56 | 4.5 |
| amber `#A64F00` (large, UI) on page / surface | 3.45 / 4.73 | 3 |
| focus `#003F7F` on page / surface / sidebar | 6.39 / 8.77 / 4.95 | 3 |
| table header text `#F2F4EE` on `#2A3838` | 11.01 | 4.5 |
| chart marks on panel `#F4F6F0`, lowest (orange, sky) | 4.08 | 3 |
| chip text `#101820` on chip fill, lowest | 8.77 | 4.5 |

All pass **provided charts sit on the panel**. Marks measured directly on the page colour fail 3:1 for orange, vermillion and sky (2.73 to 2.94), so the panel is a rule, not an option. The sidebar link pair is the thinnest margin (4.56).

**Mobile (390px).** The densest skin, so it has the most work: panels stack, KPI cards two per row, tape hidden below 640px (saves vertical space), mono size floors at 13px, table scroll-x as today.

**Popup / portal plan.** Light skin, so BaseWeb popups are already light; restyle only for coherence (border `#7F8F88`, panel fill `#E9EDE4`, hover `#B9C5BD`) and verify with a dropdown and date picker open. Lower risk than A.

**Main risk.** Density plus mono type can read as cluttered and hurts the "clear question-to-decision path" criterion; the verdict chips and answer boxes must stay the visual anchors. Also the amber lamp must not look like a data status (it is decoration; there is no "good/bad" lamp state).

**Reduced motion.** Tape and lamps static.

---

## C. Editorial Case File (light paper)

**Idea.** A printed case file: warm paper, ink, one rubric red. The page reads top to bottom as question, evidence, decision, which supports the judges' "trace one recommendation to its evidence" path.

**Tokens**
| Role | Token | Value |
|---|---|---|
| Page background (paper) | `CREAM` | `#F3ECDD` |
| Card / chart panel | `SURFACE` | `#FBF7EC` |
| Sidebar background (a paper tab) | | `#E7DDC8` |
| Text (ink) | `NAVY` / `TEXT` | `#1E1A15` |
| Captions | `MUTED` | `#5B5246` |
| Accent, all sizes (rubric red) | `TEAL` / `TEAL_DARK` | `#9B2C1F` |
| Table header fill | `SEAFOAM` | `#E2D8C2` |
| Hover / active row | `NAVY_RAISED` | `#E2D8C2` |
| Border / gridline | `BORDER` / `GRID` | `#CDBFA3` / `#E2D8C2` |
| Focus ring | | `#1F4E8C` |
| Chart marks (Okabe-Ito) | `OKABE_ITO` | blue `#0072B2`, orange `#B87700`, green `#007F5F`, vermillion `#D55E00`, sky `#2A86C4`, black `#000000` |
| Verdict chips | `CHIPS` | today's pastel fills; chip text `#1E1A15` |

**Type.** Fraunces 600/700 (soft-serif display) for H1/H2, hero and IDs; Source Serif 4 400/600 for prose; small-caps eyebrow labels in Source Serif. Tabular lining numerals are requested (`font-variant-numeric: tabular-nums lining-nums`); whether both fonts honour this is **UNKNOWN until built** (check in Phase 3). Fallbacks: `Georgia`.

**Signature moment.** Sections are numbered in a left margin using the existing `.sec .n` numerals (no new text), with a thin double rule above each section and a faint vertical "binding" rule at the left of the content column. Verdict chips become "stamps": square-cornered, slight 1.5° rotation, ink border. Paper texture is a tiny inline SVG noise at 4% opacity on the page background only, never behind charts or tables. Reduced motion: nothing animates in this skin by default (a one-time fade on the hero is the only motion and is removed).

**Where evidence stays calm.** Charts and tables sit on flat `#FBF7EC` with hairline `#CDBFA3` borders; no texture, no rotation, no shadows. Rotated stamps are only the chips outside tables; chips inside table cells stay unrotated.

**WCAG AA plan (computed)**
| Pair | Ratio | Need |
|---|---:|---:|
| text `#1E1A15` on page / surface / sidebar | 14.71 / 16.16 / 12.83 | 4.5 |
| muted `#5B5246` on page / surface / sidebar | 6.52 / 7.16 / 5.68 | 4.5 |
| rubric `#9B2C1F` as link on page / surface / sidebar | 6.44 / 7.07 / 5.61 | 4.5 |
| focus `#1F4E8C` on page / surface / sidebar | 7.07 / 7.76 / 6.16 | 3 |
| table header text on `#E2D8C2` | 12.22 | 4.5 |
| chart marks on surface, lowest (orange) | 3.46 | 3 |
| chip text `#1E1A15` on chip fill, lowest | 8.47 | 4.5 |

All pass. Margin is thin on orange (3.46) and vermillion (3.61) marks, which are also redundantly coded by shape or dash.

**Mobile (390px).** The easiest: single column already, margin numerals move inline above the heading, stamps stop rotating, serif body floors at 16px.

**Popup / portal plan.** Light skin; restyle border, fill (`#FBF7EC`) and hover (`#E2D8C2`) of BaseWeb popover, menu, calendar for coherence; verify with dropdown and date picker open.

**Main risk.** Webfont swap shifts layout and can make long tables wider; serif at 12px in dense tables is harder to read, so tables use the body face at 14px minimum. Also C looks closest to the current default (light, calm), so it may be the least "memorable" of the three.

**Reduced motion.** Nothing animates.

---

## Recommendation (my opinion, replaceable)
Build all three as agreed. If I had to pick the default today: **C**, because it is the only skin whose structure helps the judges' four paths (numbered sections lead question → evidence → decision), it has the lowest popup risk, and the contrast margin is comfortable. **A** is the most memorable but carries the only high-risk work (dark popups on a static light `config.toml`). **B** is the best for "drill into one bank" feel, but density is a communication risk. This is a lean, not a result: Phase 4 axe/Lighthouse and the human-test kit decide.

## Decisions I need from you (Checkpoint 2)
1. Approve, change or replace each of A, B, C (say which letter and what).
2. Fonts: OK to load Bodoni Moda, DM Sans, IBM Plex Mono/Sans, Fraunces and Source Serif 4 from Google Fonts via `@import`, as Inter is loaded today? (If you want zero extra network fonts, say so and I use system stacks.)
3. A's "black → ivory" and B/C's slightly darkened Okabe-Ito hues change chart *colours* (never data or shapes). Confirm that is within "presentation only".

## Unknown / unverified
- Everything visual: nothing is built. Contrast numbers are computed from palette hexes only.
- Font tabular-numeral support (C), BaseWeb popup selector names at 1.67.0 (A), real 390px density (B).
- Whether `config.toml` must change for the winner (needs your approval by name).
