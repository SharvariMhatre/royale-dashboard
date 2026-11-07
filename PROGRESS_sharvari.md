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
