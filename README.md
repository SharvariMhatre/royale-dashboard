# The Gilded Ace: Floor Doctor

Dashboard Royale entry, TAMU Datathon 2026. The GM wants to replace the 10 lowest-earning slot machines (Jan 1 to Jun 30, 2025). Low earnings can come from luck, location or a leak, so we tested all three before recommending anything.

**Live dashboard:** https://royale-dashboard777.streamlit.app (public, no login; the first load after a quiet period can take a few seconds)

## What we found
- 0 of the GM's 10 machines are truly bad: 6 are in a bad spot, 3 have a short time on the floor, 1 is an inspect lead. 9 of the 10 sit in Back Forty, which earns 65% of the floor rate for the same games.
- The casino already replaced one machine in slot L-38-5 on 2025-05-13, and the replacement landed on the list too: replacing does not fix a bad spot.
- Downtime is 0.38% of scheduled hours. A weekday plus events forecast beats a constant baseline on a time-based holdout ($50,920 vs $218,258 average daily miss).
- The team's $100,000 plan spends $14,100 on three actions (inspect M-1158, Back Forty signs, move 3 machines with matched controls) and keeps $85,900.

All numbers shown in the app come from `app_data/findings/*.json` or are recomputed live from the files in `app_data/`. The write-up, the evidence appendix and the judge Q&A in `docs/` are generated from the same files.

## Team
| Person | Role | Owns |
|---|---|---|
| Sharvari Mhatre | Dashboard and storyteller | Streamlit app, integration, validation, write-up, video, submission |
| Aditi | Data builder | Downtime, comps and leak clues (`p1_*` tables) |
| Bharath | Machine detective | Machine verdicts, luck simulations, zone and move analysis (`p2_*` tables) |
| Nikita | Predictor | Demand, players and the forecast model (`p3_*` tables) |

## Data flow
```
challenge data (synthetic, release 0.9.0-draft)
   -> Databricks (workspace.casino): p1, p2, p3 notebooks, luck simulations, MLflow forecast runs
   -> src/export_from_databricks.py -> app_data/team/*.parquet + _export.json (export time, Central)
   -> src/validate_contracts.py (checks every file; a bad file shows as "pending", never as wrong numbers)
   -> src/integrate_team.py -> app_data/team/all_claims.parquet + app_data/findings/team.json
   -> Streamlit app (app/): reads the files, recomputes anything that depends on the period, bank or guest-group filters
```
A self-sufficient fallback (`src/minimum.py`, built only from the challenge's prepared views) answers all six questions on its own. Each page falls back to it if a team file is missing or fails validation.

## How to reproduce
Python 3.11 or newer.
```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt        # the app: streamlit, pandas, pyarrow
.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py     # opens the dashboard locally
```
Run the checks:
```
.venv\Scripts\python.exe -I tests/test_validate_contracts.py
.venv\Scripts\python.exe -I tests/test_budget.py
.venv\Scripts\python.exe -I tests/test_theme.py
.venv\Scripts\python.exe -I src/validate_contracts.py              # validates every file in app_data/team/
```
Rebuild the data (optional; the repo already contains the results):
1. **Minimum version.** Clone the challenge data repo next to this folder as `../dashboard-royale`, install `duckdb`, then run `src/minimum.py`. It writes `app_data/min_*.parquet` and `app_data/findings/minimum.json`.
2. **Team tables.** Needs Databricks access: put `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH` and `DATABRICKS_TOKEN` in a git-ignored `.env`, install `requirements-export.txt`, then run `src/export_from_databricks.py`. Credentials are never printed or committed.
3. **Findings and documents.** Run `src/integrate_team.py`, then `src/make_docs.py`.

## Folder guide
| Path | What it is |
|---|---|
| `app/` | The Streamlit app: `streamlit_app.py` (entry and navigation), `pages.py` (six pages), `common.py` (filters, safe loaders), `theme.py` and `art.py` (design system and illustrations) |
| `app_data/team/` | The team's exported tables, `all_claims.parquet`, and `_export.json` (when and from where they were exported) |
| `app_data/findings/` | `team.json` and `minimum.json`: every headline number the pages and documents use |
| `app_data/min_*.parquet` | The minimum version's tables, plus `min_machine_day` for live recalculation by date range and bank |
| `src/` | Export, integration, validation, budget rules, minimum version and document generation |
| `tests/` | Unit tests for the contract validator, the budget rules and the colour contrast |
| `docs/` | `writeup.md` (400 words or fewer), `evidence.md` (claims and evidence appendix), `judge_qa.md`, `ai_disclosure.md` |
| `TEAM_PLAN.md`, `REQUESTS.md`, `PROGRESS_sharvari.md` | The file contract between teammates, open requests, and the working log |

## Method notes
- Money math uses ratios of sums, hours from the calendar's scheduled seconds (23 hours on 2025-03-08), cents converted once, and only on-floor machine-days.
- Verdicts weigh luck (10,000 fair replays per machine), exposure (days on the floor), location (zone against the same game across the floor), availability and downtime. Anomalies are leads to inspect, never accusations.
- The forecast trains on Jan to Apr and tests on May to Jun, frozen before testing, against a constant-mean baseline.
- Costs in the plan follow the guide formula (`quantity x (unit cost + daily cost x max(0, 30 - lead days))`) and are recomputed by `src/budget.py`, which also enforces 3 action types, $100,000, quantity limits and incompatibilities.
- Benefits after the 30-day window (moves, signs, inspection) are shown only as a labelled assumption.

## Data and AI
The data is synthetic, so findings are not facts about a real casino. AI use is disclosed in `docs/ai_disclosure.md`.
