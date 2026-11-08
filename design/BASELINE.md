# Baseline (Phase 0)

Captured 2026-11-07 on branch `feature/ui-improvement`, HEAD `8901dd9`, working tree clean before capture (only `.venv/` and `design/` added, `.venv` is gitignored).

## Environment
- `.venv` created with Python 3.12.10 and `pip install -r requirements.txt pytest` (requirements.txt not edited). Installed: streamlit 1.67.0, pandas 3.1.1, pyarrow 26.0.1, altair 6.3.0 (transitive).

## Tests (run with `.venv\Scripts\python.exe -I tests/<name>.py`; `pytest tests/` collects 0 tests because they are assert scripts)
| script | exit | note |
|---|---|---|
| test_budget.py | 0 | payback, decimal, placeholder checks passed |
| test_validate_contracts.py | 0 | passed |
| test_theme.py | 0 | text contrast OK; `#E69F00` 2.11 and `#56B4E9` 2.16 below 3:1 (known, mitigated) |

## Parity baseline (from local HEAD, not the live site)
- `design/harness/extract.py` runs each page body through `AppTest.from_string` (CONFIRMED: `AppTest.switch_page` cannot switch `st.navigation` callable pages; the default page runs fine via `from_file`). It records metrics, tables, tag-stripped markdown, captions, headers, widget values and alerts per page into `design/baseline/numbers.json`.
- Counts: Overview 16 metrics / 11 tables / 35 markdown; Machine Details 4/2/9; Demand & Downtime 4/6/5; Players & Comps 4/4/5; Model Test & $100K Plan 4/3/3; Evidence 3/1/3. No exceptions on any page.
- Two consecutive runs are byte-identical (deterministic), so any later diff is a real change.
- Not captured by AppTest (Altair/Vega content): chart marks and tooltips, floor map. These are covered by the git-diff scope guard (pages.py, common.py, src/ unchanged) rather than by AppTest.
- Style baseline: `design/baseline/css.txt` (the exact `theme.CSS` string, 12,029 chars) and `design/baseline/tokens.json` (21 token names) captured before any refactor.

## Live site (royale-dashboard777.streamlit.app)
- The app was already awake (no "wake up" prompt). The Streamlit Cloud wrapper puts the app in an iframe and shows "Fork", GitHub and menu buttons plus a "Hosted with Streamlit" badge and creator avatar that skins cannot restyle.
- Screenshots in `design/baseline/`: `overview_1440.png`, `machine_details_1440.png`, `demand_1440.png`, `demand_390.png` (taken with chrome-devtools; full-page captures of the iframe may be clipped, e.g. the sidebar is cut off in the overview image).
- Update: all 6 pages are now captured at 1440 and 390 (12 PNGs: `<page>_1440.png`, `<page>_390.png`). These are viewport-sized captures of the live iframe, not full-page scrolls, so they show the top of each page only; the 1440 shots show the sidebar clipped on the left.
- Lighthouse (desktop, navigation, Model page, `design/baseline/lighthouse/report.{json,html}`): Accessibility 84, Best Practices 96, SEO 83; total timing 12.2 s (this is audit time, not a clean cold-start measure). Failed audits: errors in console, no main landmark, links without discernible name, `user-scalable=no` / low max-scale in the viewport meta, no meta description, invalid robots.txt, llms.txt. Several come from the Streamlit Cloud wrapper, not the app.
- NOT captured: popup states (selectbox open, date picker open); these are deferred to Phase 3 per skin, because they only matter for the skins that restyle them. A true cold-start time is not measured (the app was already awake).
- Live page URL slugs (CONFIRMED from the page): `/`, `machine_details`, `demand_and_downtime`, `players_and_comps`, `model_test_and_100k_plan`, `evidence`.
- Which git branch Cloud deploys is UNKNOWN; the live figures were not used for parity.
- Observed on the live page: every team-file footer shows "Warning: <file>.parquet: no _meta sidecar (version unknown)" (known, listed as adjacent issue); the Demand page shows "Evidence: Q2 claims on what changed in demand (0)".

## How styling is applied (for Checkpoint 1)
- One `<style>` injected by `theme.apply()` (`app/theme.py:209-211`), called once from `app/streamlit_app.py:16`; CSS is a single f-string built from module-level tokens; Streamlit internals styled via `data-testid` selectors and `:has()`.
- Altair theme registered once per import from tokens (`theme.py:206`); modules are reloaded on every run, so a skin must be resolved at import time.
- Leaks outside the token block: `art.py` (8 hexes), `theme.py` verdict tables/CSS (6), logo SVGs (7), `config.toml` (7 duplicated values), `pages.py` inline styles (2).
- Skin seam is feasible with one switch (query param, remembered in `st.session_state`, default = current look), plus the two `target=_self` anchors need `skin=` appended.
