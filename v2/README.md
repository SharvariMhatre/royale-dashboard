# Gilded Ace floor review, v2

Static dashboard that recomputes every number in the browser for any period, zone, bank or guest group, plus the pipeline that produces and verifies its data. The original Datathon entry (Streamlit) is unchanged in `../app/`.

**Answer:** don't replace the ten. Nine sit in Back Forty, a zone cut off by its walkway closure; one (M-1158) pays more often and smaller than its game, so inspect its paytable. Spend $38,700 of the $100,000, keep $61,300.

## Run it
```sh
git clone --depth 1 https://github.com/tamu-datathon-org/dashboard-royale.git ../dashboard-royale   # challenge data, beside this repo
pip install duckdb pandas pyarrow numpy scikit-learn
python v2/analysis/build.py        # pipeline -> v2/site/data/*.json, then 40 verification checks (exit 1 on any mismatch)
cd v2/site && python -m http.server 8790   # open http://localhost:8790
node v2/tests/browser_parity.cjs   # browser engine vs Python, all 310 machines (needs playwright)
```
Set `ROYALE_DATA` to point at the data folder if it lives elsewhere.

## What's where
| Path | What |
|---|---|
| `SWEEP.md` | Column-by-column data sweep and the questions it raised |
| `DECISIONS.md` | Every choice, its options and who decided |
| `analysis/q1_machines.py` | Closed-form luck z, hit-rate z, leave-one-out peers, zone index, verdicts, M-1158 mechanism, natural experiments |
| `analysis/q2_q3_demand_downtime.py` | Walkway closure with 78 placebo windows; demand; downtime by month, zone, maker, shift |
| `analysis/model.py` | Five forecasters, rolling-origin CV on Jan to Apr, one test on May to Jun, 80% interval coverage |
| `analysis/q4_q5_guests.py` | Player outcomes and concentration by group; comp change-point scan |
| `analysis/plan.py` | Every legal $100K plan scored with 4,000 simulations; the GM's plan beside it |
| `analysis/claims.py` | Claims & Evidence appendix (`docs/CLAIMS.md`, `site/data/claims.json`) |
| `analysis/verify.py` | 40 checks against the raw tables |
| `site/` | The dashboard: `index.html`, `app.js` (engine + views + judge tour), `ask.js` (Ask the floor) |
| `site/api/ask.js` | Vercel function that lets Claude answer free-form questions from the published facts only (needs `ANTHROPIC_API_KEY`) |

## Publish on Vercel
1. vercel.com, Add New, Project, import `SharvariMhatre/royale-dashboard`.
2. Root Directory: `v2/site`. Framework Preset: Other. Leave Build Command and Output Directory empty.
3. Optional: Settings, Environment Variables, add `ANTHROPIC_API_KEY` to switch on free-form questions in "Ask the floor". Without it, the built-in verified answers still work.
4. Deploy. Every push to `main` redeploys; other branches get preview links.

Write-up: `docs/WRITEUP.md` (387 words). AI use: `docs/AI_DISCLOSURE.md`. Data is synthetic.
