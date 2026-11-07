DEADLINE: hacking ends 12:00 PM Central, Sun Nov 8 2026. Clock: h8=7 PM Sat, h12=11 PM Sat, h14=1 AM Sun, h17=4 AM Sun, freeze 4:30 AM Sun.

# PROGRESS (Sharvari)
## Done
- Setup: folders, .gitignore, REQUESTS.md, notes/ai_log.md, git longpaths. Data repo at ../dashboard-royale has real parquet (no LFS pointers found).
## Notes
- Local Python is 3.13.9; Streamlit Cloud must be set to 3.11 (keep code 3.11-compatible).
## Next
- git init + remote (awaiting your OK for any push), then DESCRIBE source tables, then walking skeleton.
- Skeleton: app/streamlit_app.py (5 pages via st.navigation), app/common.py (sidebar filters, safe loader -> "pending", header with analysis window + data version), app_data/filters.json (banks, tiers; made once from the views so the deployed app needs no raw data), requirements.txt pinned (streamlit 1.67.0, pandas 3.1.1, pyarrow 26.0.1). Headless run OK on all pages, shows "pending".
