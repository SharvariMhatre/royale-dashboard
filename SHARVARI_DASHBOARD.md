# SHARVARI_DASHBOARD.md — your part, start to finish

You own the Dashboard Royale submission. Your first job is to make sure that entry is complete on its own; your second job is to plug in the team's Databricks outputs as they arrive. Order of work below does exactly that.

## Hour 0–1: setup
1. Devpost: write the deadline with time zone at the top of TEAM_PLAN.md and PROGRESS_sharvari.md.
2. Accounts: GitHub (public repo `royale-dashboard`), Streamlit Community Cloud (sign in with GitHub).
3. Local: Python 3.11+ (`py -3.11` on Windows), `git config --global core.longpaths true`, sparse clone of the data repo next to your project folder:
   ```
   git clone --depth 1 --filter=blob:none --sparse https://github.com/tamu-datathon-org/dashboard-royale.git ../dashboard-royale
   cd ../dashboard-royale && git sparse-checkout set GUIDE.md reference data/1_prepared_views data/2_machine_decision data/4_context
   ```
   If any .parquet is under 1 KB it is a Git LFS pointer: `git lfs install && git lfs pull`.
4. Project folder: put TEAM_PLAN.md and this file in it. Create `.gitignore` with `.venv/`, `app_data/samples/`, `__pycache__/`, `*.csv.gz`. Never commit raw data.
5. Start Claude Code in the project folder: `claude`, `/model sonnet`, paste the kickoff prompt at the end of this file.

## Hour 1–3: walking skeleton, deployed
- `app/streamlit_app.py` with sidebar: period selector (presets Full, each month, Jan–Mar, Apr–Jun, plus custom range), bank filter, guest-group filter.
- Five pages as empty shells with a visible "analysis window" line and a "data version" line.
- Every page loads its file with a helper that returns "pending" when the file is missing or fails validation.
- Deploy on share.streamlit.io: repo, branch main, main file `app/streamlit_app.py`, Python 3.11 under Advanced settings. Open the link in a private window and on your phone. **Do not continue until this works.**

## Hour 3–6: the self-sufficient minimum (this is what guarantees the entry)
Using only `prepared_daily_view`, `property_day`, `player_period`, `calendar_day`, `action_catalog`, write `src/minimum.py` that produces `app_data/min_*` files with the guide-level answers:
- Q1: per machine, house win, theo, luck residual, available hours, theo per available hour, simple peer index vs zone median (leave-one-out), GM's bottom 10 flagged. Label with the simple rule: availability low → Broken lead; luck residual negative but theo per available hour normal → Unlucky; peer index clearly low → Truly bad lead; else Mixed. (Person 2's richer verdicts with intervals replace this at hour 14.)
- Q2: weekly floor coin-in, theo, occupied hours, entries, with event and holiday markers.
- Q3: downtime hours and lost theo (downtime × own theo per available hour) by week and manufacturer.
- Q4: by tier and month, wagered, paid back, net, theo; top 10% share of theo (groups of 10+ only).
- Q5: comp cost and comp cost / theo by month and tier.
- Q6: cost calculator for the catalog with the guide formula, limits and incompatibilities; "keep the money" row.
- Model placeholder: weekday-mean vs constant-mean on daily coin-in, Jan–Apr train, May–Jun test, MAE both. (Person 3's MLflow version replaces it at hour 12; if theirs is late, yours satisfies the requirement.)
Each `min_*` file writes its numbers to `app_data/findings/minimum.json`. Wire all five pages to these files. At hour 6 the dashboard answers all six questions, roughly.

## Hour 6–8: Decision Room and evidence links
- Page 1 Overview / Decision Room: GM's bottom 10 next to the evidence view (house win, theo per available hour, peer index with interval when available, availability, label, one-line reason); label counts; the budget builder (up to 3 action types, quantity, targets, cost with lead days and operating days, incompatibility check, remaining money, keep-money row, each line linking to its evidence).
- `claims.csv` and the evidence table on page 5; every chart gets a caption "source: <file>, script: <name>, scope: <scope>".

## Filter rules (judges' test 1 depends on these)
- Totals, hold, theo per available hour, availability, peer index point estimates: recomputed live from `machine_day_clean` (or `prepared_daily_view` until hour 8) for any date range.
- Intervals, verdicts and simulated luck share: precomputed per scope by Person 2. Show them when the selected range equals a scope; for a custom range show point estimates and the note "intervals and verdicts shown for nearest precomputed scope: <scope>".
- Player and comp pages: whole months only; a custom range snaps to months and says so.
- Model page: fixed split dates, unaffected by filters, stated on the page.
- Never show a full-period label as if it were recomputed for a month.

## Hour 8, 12, 14, 17: integration (same routine each time)
1. Pull. Run `python src/validate_contracts.py app_data/<file>`.
2. If it passes: switch the page's loader from `min_*` to the team file, keep the `min_*` fallback, add the file's `_meta` version to the page footer, re-run the page, push, check the live link.
3. If it fails: tell the producer in REQUESTS.md with the exact error, keep showing the minimum version, note it in PROGRESS_sharvari.md. Don't patch their file yourself.
4. Add their findings to `claims.csv` only after validation.
Priority if time is short: q1_machines (h14) > forecast (h12) > budget (h17) > q2/q4/q5.

## Hour 14–17: Machine Details and the four judge tests
- Page 2 Machine Details: select a machine or a bank → evidence card: why it looked weak; exposure and availability; actual vs theo over time; peer comparison with interval and the peer group used; competing explanations tested (moved? downtime? luck? hold gap?); verdict or "not enough evidence"; source and script.
- Time each judge test in a private window: change period, drill into a bank and a guest group, find the model validation, trace one recommendation to evidence. Target under 60 seconds each. Fix what fails.

## Final 30%: finish and submit
- Freeze numbers. Screenshots of every page in `docs/screenshots/`.
- `docs/writeup.md` ≤ 400 words (print the count), `docs/appendix_claims.md` from `claims.csv`, `docs/ai_disclosure.md`, README with reproduction steps.
- Video ≤ 2:00: 0:00 the GM's list and the question; 0:20 Decision Room, what the labels mean, one number that changed; 0:50 one machine's evidence card; 1:15 model test and the decision it changes; 1:35 the $100K plan, remaining money, how we'd measure it.
- Devpost: submit a draft early, video public or unlisted, all four names, appendix attached or linked, dashboard link rechecked in a private window. Wake the app right before judging.
- Someone outside the team reads only page 1 and answers: which machines would you replace, how much money is left, how will you know it worked. Fix what they get wrong.

## Design rules
Colourblind-safe palette, never colour alone; units on every axis; one-sentence takeaway above each chart; analysis window and data version visible on every page; no animation; plain words a manager understands; "not enough evidence" is an allowed answer.

## Claude Code kickoff prompt (paste once)
```
Read TEAM_PLAN.md and SHARVARI_DASHBOARD.md fully. I am Sharvari, Person 4: I own the Streamlit dashboard, the claims table, the write-up, the video and the Devpost submission for Dashboard Royale, and I integrate the team's Databricks exports when they arrive. I know Python basics and will present to judges, so explain each design decision in two plain sentences.

Work through SHARVARI_DASHBOARD.md in order: setup, walking skeleton deployed, the self-sufficient minimum (src/minimum.py producing app_data/min_* for all six questions), Decision Room and evidence links, then integration routines, Machine Details, judge tests, submission materials. Also write src/validate_contracts.py from the file contract in TEAM_PLAN.md.

Rules: DESCRIBE every table before using a column and never assume names; never print raw data (DuckDB, max 20 rows); ratio of sums only; exclude inactive / empty-location rows; use calendar_day.scheduled_seconds; cents to dollars once; every displayed number comes from app_data/findings/*.json; follow the filter rules exactly and label the scope of every interval; every page shows "pending" if its file is missing or invalid; never edit a teammate's file, write the problem in REQUESTS.md instead; ask me before any push or deletion; stop after the skeleton is deployed and at each integration hour; update PROGRESS_sharvari.md after each task; keep a running notes/ai_log.md.

Start with setup now and tell me in 5 lines what you are about to do.
```

## Resume prompt (after a usage limit or /clear)
```
Read SHARVARI_DASHBOARD.md and PROGRESS_sharvari.md. I am Sharvari. Tell me in 5 lines where we are, then continue from the next unfinished step. Do not redo finished steps.
```
