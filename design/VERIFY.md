# Verification report (Phase 4)

Run 2026-11-08 on branch `feature/ui-improvement`, HEAD `8901dd9`, all changes **uncommitted**. Python 3.12 `.venv`, Streamlit 1.67.0.
Status words: **PASSED** = I ran it and saw it pass. **UNVERIFIED** = not run or not seen. **OPEN** = a known defect.

## 1. Scope guard: PASSED
- `git diff --name-only` (tracked): `app/art.py`, `app/pages.py`, `app/theme.py` only. New files: `app/skins/{default,noir,control,paper}.py`, `tests/test_skins.py`, `design/*`, `HANDOFF.md`.
- `app/pages.py` change is one line: the `machine_details?m=` link appends `{T.SKIN_Q}` (empty for the default skin). `app/art.py`: 8 literal hexes became tokens with the same values. `app/theme.py`: tokens and CSS moved to `skins/default.py`, plus the skin loader.
- `src/`, `app_data/`, `app/common.py`, `app/streamlit_app.py`, `.streamlit/config.toml`, `requirements.txt` untouched.
- Each worktree's `app/` differs from the main tree only in its own skin file (`diff -rq`, empty for all three).

## 2. Default skin identical to before: PASSED
- `theme.CSS` equals `design/baseline/css.txt` (equal after normalising the baseline file's CRLF; the 147-char length difference was line endings only).
- All 21 tokens in `design/baseline/tokens.json` equal the current values.
- AppTest numbers: `numbers.json` regenerated under the seam is byte-identical to the baseline.

## 3. Parity for every skin: PASSED
`tests/test_skins.py` runs each page under `default`, `noir`, `control`, `paper` and compares metrics, tables, headers, captions, widgets, alerts and tag-stripped markdown with `design/baseline/numbers.json` (the injected CSS entry is skipped). Zero exceptions on all 24 page-runs. Each skin's own CSS was confirmed active (first markdown entry shows its font imports).
**Limit:** AppTest does not see Altair/Vega content or the floor map. Chart data is covered only by the scope guard (pages.py, common.py, src/ unchanged apart from the one link).

## 4. Tests
| Script | Result |
|---|---|
| `tests/test_budget.py` | exit 0 |
| `tests/test_validate_contracts.py` | exit 0 |
| `tests/test_theme.py` (default tokens) | exit 0 |
| `tests/test_skins.py` (new): tokens complete, 7 chips and 7 verdict colours, text/link/chip contrast >= 4.5:1 per skin, reduced-motion guard, parity, judge paths | exit 0, all four skins |

## 5. Judge paths under every skin: PASSED (AppTest)
Period change moves Players & Comps "Wagered"; bank selectbox and guest-group radio accept a drill-down with no exception; Model page shows "Model average miss per day" $50,920 vs "Constant baseline miss per day" $218,258; an "Evidence:" expander exists on the Model page. **Not covered by AppTest:** clicking a floor-map point (`on_select`), real mouse use.
Skin persistence: card links carry `&skin=<name>` (seen in the DOM: `machine_details?m=M-5076&skin=paper`); clicking the in-app sidebar "Evidence" link under `?skin=paper` kept the paper background (`rgb(243,236,221)`) and fonts. A bare URL typed without `?skin=` starts a new session on the default skin, by design.

## 6. Contrast
- **Palette-level (computed by script and `test_skins.py`): PASSED** for the pairs in `DIRECTIONS.md` and the text/link/chip pairs per skin.
- **Rendered, Lighthouse accessibility (local dev server, Model page, desktop): default 100, paper 100.** Best Practices 96 and SEO 83 for both; the same 5 audits fail in both. Noir and control **UNVERIFIED** by Lighthouse (not run). For reference the live site scored A11y 84 in Phase 0; that run included the Streamlit Cloud wrapper, which this local check does not.
- **Standalone axe-core: NOT RUN.** Injecting axe-core from a CDN into the page was denied by the auto-mode classifier, and I did not work around it. Lighthouse's accessibility category uses axe-core internally; that is the only axe coverage here.
- Noir calendar: a reviewer measured in-range days at about 1.26:1 (dark text on dark). Fixed in `noir.py`; in the live DOM after the fix the day text is `#F3EADB` on the range tint, about 11:1 (my computation from the two colours). The screenshot `design/noir/datepicker_open_1440.png` predates the fix.

## 7. Independent review ("refute presentation-only"): three reviewer agents
- noir: "violations found" (one **major**, the calendar, now fixed) plus minors.
- control and paper: "presentation-only confirmed", minors only.
- Reviewers opened only some screenshots (their `notVerified` lists are in the workflow journal). I opened `control/overview_1440`, `paper/overview_1440_d` and a live noir page myself.

## 8. Defects found after the review and fixed by me
- Noir calendar in-range text (above).
- Paper and control headings fell back to Streamlit's own "Source Sans" because their heading rule was less specific than Streamlit's heading style. Fixed with `.stApp h1...` in both; measured live: paper `.ph h1` now Fraunces, control now IBM Plex Sans.

## 9. OPEN issues (not fixed, with cause)
| Issue | Skin | Why open |
|---|---|---|
| ~~Single-series bar charts use the text colour (NAVY)~~ | noir, control | **FIXED 2026-11-08 (user approved "Bar fix only"):** new `CHART_MARK` token in all four skins (default and paper = NAVY, so unchanged; noir `#3B9BE0` 5.9:1, control `#0072B2` 4.4:1) and two call sites in `pages.py` (lines 182 and 852). Seen live in noir on Players & Comps. Not checked live in control. Chart spec equality for default and paper is inferred from equal token values, not diffed |
| Blue/sky and orange/vermillion are close in lightness (blue vs sky about 1.2 to 1.3:1 in noir and control) | all but default | Okabe-Ito hues kept per the spec; meaning is also carried by shape, dash, labels and tooltips |
| Input and bar-track borders below 3:1 (control sidebar wells about 1.8:1) | control | Outside the spec's pair table (WCAG 1.4.11); no script tests it. **Noir FIXED 2026-11-08:** new `EDGE` #7A6E8C, 3.74:1 on the card (4.29:1 on the sidebar), measured live on selects, pills and the meter track (outline via box-shadow; over-budget red fill 3.09:1 on the track). Date and number inputs inferred, not measured |
| Histogram `T.TEAL` at 0.55 opacity (about 2.3:1 on the control panel) | control | Opacity hard-coded at `pages.py:700` |
| ~~Infinite marquee-bulb animation~~ | noir | **FIXED 2026-11-08:** now 2 loops (about 4.8 s, measured live) and rests lit, so no pause control is needed; reduced-motion rule intact (CSS read, live emulation not run). Noir Lighthouse accessibility: 100 on Overview and Model pages |
| Mobile floor-map legend and "Garage Entrance" label clipped at 390px | noir (seen), others unchecked | Comes from the chart spec |
| `config.toml` is a static light theme, so skins override Streamlit widgets with `!important` CSS tied to 1.67.0 `data-testid` names | all | A matching `config.toml` for the winner is a separate step that needs your approval by name |
| Logo is a fixed SVG; control and paper recolour it with a CSS filter | control, paper | `streamlit_app.py` is outside the allowed list |
| `art.py` assumes a dark hero: control uses a light hero; paper and noir re-ink with attribute selectors | all | Art tokens in `art.py` would be cleaner (seam change) |
| Streamlit's heading font also overrides the default skin's `.ph h1` "Inter Tight" rule | default | Pre-existing; left alone because default must stay identical |

## 10. UNVERIFIED (nothing run or seen)
- Windows forced-colors, a real touch device, real pointer hover, the Vega chart tooltip in any skin.
- Noir and control by Lighthouse; any skin on Streamlit Community Cloud (fonts load from fonts.googleapis.com via `@import`; the Cloud wrapper's own buttons cannot be restyled).
- Cold-start and page-weight cost of the extra webfonts (not measured).
- Human readability and trust: `design/HUMAN_TEST.md` is written, not run.
- Which branch Cloud deploys.

## 11. Screenshots
`design/{noir,control,paper}/` (1440 and 390 for all six pages plus popup states, taken by the Refine agents; some predate their agent's last CSS edit) and `design/baseline/` (the live default). Lighthouse reports: `design/lighthouse_default/`, `design/lighthouse_paper/`.

## 12. Recommendation (opinion, not a result)
Default winner: **paper (C)**. It has the lowest widget-override risk, the best contrast margins, scored Lighthouse 100, and its numbered sections follow the question-to-evidence path the judges use. **noir (A)** is the most memorable but has the most fragile CSS and the open items above; **control (B)** is dense and its near-black chart bars are the loudest evidence on the page. Make the choice after the human test, which is not run yet.
