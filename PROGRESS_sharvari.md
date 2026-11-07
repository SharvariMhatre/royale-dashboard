DEADLINE: hacking ends 12:00 PM Central, Sun Nov 8 2026. Clock: h8=7 PM Sat, h12=11 PM Sat, h14=1 AM Sun, h17=4 AM Sun, freeze 4:30 AM Sun.

# PROGRESS (Sharvari)
## Done
- Setup: folders, .gitignore, REQUESTS.md, notes/ai_log.md, git longpaths. Data repo at ../dashboard-royale has real parquet (no LFS pointers found).
## Notes
- Local Python is 3.13.9; Streamlit Cloud must be set to 3.11 (keep code 3.11-compatible).
## Next
- git init + remote (awaiting your OK for any push), then DESCRIBE source tables, then walking skeleton.
- Skeleton: app/streamlit_app.py (5 pages via st.navigation), app/common.py (sidebar filters, safe loader -> "pending", header with analysis window + data version), app_data/filters.json (banks, tiers; made once from the views so the deployed app needs no raw data), requirements.txt pinned (streamlit 1.67.0, pandas 3.1.1, pyarrow 26.0.1). Headless run OK on all pages, shows "pending".
- Skeleton deployed and verified in private window: https://royale-dashboard777.streamlit.app
- src/minimum.py: Q1 done (app_data/min_q1.parquet + _meta). Q2-Q6 + model + findings/minimum.json + page wiring pending user review of Q1 table.
- Q1 labels revised (zone_index, config_index, occupancy_vs_zone; order: Too little data > Broken > Unlucky > Game setting > Location > Truly bad > Mixed). GM bottom 10: 9 Location, 1 Unlucky; no Game setting (same-config machines elsewhere earn more).
- src/minimum.py complete: min_q1..q6, min_q4_conc, min_machine_day, min_model + findings/minimum.json. All five pages wired (app/pages.py), headless-tested on every page, plus Mar and custom-range filters. NOT yet committed/pushed (awaiting OK).
- Known gaps: "Unlucky" fires for 125/310 machines (too loose); Q2/Q5 causes untested; no intervals; budget builder has no benefit estimates; evidence links are a text column, not clickable.
- Committed+pushed minimum version (898dab9). Follow-ups done: Unlucky needs luck < -20% of theo (now 14 machines floor-wide, was 125; bottom 10 unchanged: 9 Location, 1 Unlucky); also_strong column shows second causes (M-1158: Luck + below config peers); GM-list zone sentence built from findings q1.zone_story; model page shows weekday means + leak check (0 May-Jun days in training).
- Pushed 1402502. Wrote src/validate_contracts.py (contract in TEAM_PLAN.md; CLI + validate()) with tests/test_validate_contracts.py (passes). common.load() now returns "pending" for any contract file that fails validation. Budget builder evidence lines are clickable st.page_link (tested in the full nav app; 3 actions cost $16,720 = hand check).
- Contract ambiguities I resolved (tell producers): sidecar name <file>._meta.json (also accepts <stem>._meta.json / <stem>_meta.json); week column may be `week` or `week_start`; q4_concentration needs columns matching top1/top10/top20/gini; floor_day_clean required columns are a subset (contract says "property_day columns +").
- Pushed 1d92edf. TEAM_PLAN.md roles + file contract replaced with real owners/names (p1 Aditi Q3+Q5, p2 Bharath Q1, p3 Nikita Q2+Q4+model; parquet in app_data/team/; due 7 PM / 11 PM / 1 AM / 4 AM). validate_contracts.py rewritten (required cols only where given; _meta optional -> footer warning; verdict set as specified). src/budget.py: merges p*_actions, recomputes cost with guide formula and flags mismatches, enforces 3 types / $100k / quantity limits / comp_policy / same machine targeted twice; tests/test_budget.py passes.
- Display: partial weeks dropped; manager formatting via common.show() (usd, %, "Jan 6"); plain-English column names; model chart has legend + dash styles; Overview "Answer in brief" box built from findings.
- Open: record exact columns from app_data/team/samples/ when they arrive; team-file pages not yet switched from min_* (integration hours); budget.py is not yet used by the page builder.
- Fixed Streamlit Cloud stale-module ImportError: streamlit_app.py reloads validate_contracts/common/pages each run; common.py reloads validate_contracts. Tested stale sys.modules + on-disk edit without restart. (reload keeps removed names; harmless.) budget.py is not imported by the app (needs duckdb, not in requirements).
- Databricks export: src/export_from_databricks.py (+ requirements-export.txt, installed in .venv; app requirements.txt untouched). Exported 22 of 25 tables to app_data/team/; all_claims, all_actions, final_budget_plan missing in workspace.casino (not yet built). Contract in TEAM_PLAN.md + validate_contracts.py replaced with the team's real columns; all 22 exported files PASS (no _meta sidecars: warnings only). Verdict set now: Inspect, Short exposure, Broken, Truly bad, Bad spot, Unlucky, Healthy.
- budget.py updated to the new actions format (action/expected_benefit/low/high); p2_actions use free text, matched to the catalogue by wording and flagged for human confirmation; all costs match the guide formula.
- Not done: pages still on min_* files; nothing pushed after 4130dbd.
