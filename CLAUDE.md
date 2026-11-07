# Dashboard Royale (TAMU Datathon 2026) - rules for every session

Follow this file in every session. Source of truth: `../dashboard-royale/` (GUIDE.md, README.md, reference/DATA_DICTIONARY.md). Data release `0.9.0-draft`; values may change before 1.0.0. Casino and data are synthetic, except files in `data/4_context/real_sources/`.

## The task
We are floor analytics lead at **The Gilded Ace** (300 machines). The GM wants to replace the 10 lowest-earning machines (Jan 1 - Jun 30, 2025). Low earnings may be **luck, location, or a leak**; test all three before picking one. Build a public interactive dashboard.

## The six questions (minimum; well-supported extras earn credit)
1. Which machines are truly underperforming once exposure, availability and luck are accounted for?
2. What changed in demand across the floor over the six months, and why?
3. How much play was lost to downtime, and when?
4. What did tracked players wager, get back and net, and how concentrated are the results?
5. What did the loyalty (comp) program cost, and did anything about it change?
6. Which actions would we fund with $100,000, and how would we know they worked?

Start tables: Q1 `prepared_daily_view` | Q2 `property_day`, `zone_traffic_hourly` | Q3 `prepared_daily_view` (availability), `operations` | Q4 `player_period` | Q5 `player_period`, `property_day` | Q6 `action_catalog`, `cost_rules`.

## Judging weights
| Criterion | Weight |
|---|---:|
| Analytical validity (correct money math; fair comparisons for exposure/availability/luck; uncertainty shown; a competing explanation tested) | 30% |
| Dashboard and communication (clear question-to-decision path; accessible; every claim traceable) | 25% |
| Modeling and validation (one sensible model that changes a decision, vs a simple baseline, time-based holdout, no leakage) | 20% |
| Recommendations and tradeoffs (priced actions in budget, assumptions, sensitivity, measurement plan) | 15% |
| Originality (unexpected, reproducible finding) | 10% |

Chart count and model complexity earn nothing. Judges will: (1) change the analysis period, (2) drill into one bank or guest group, (3) find how the model was validated, (4) trace one recommendation to its evidence. The dashboard must support all four.

Modeling route: pick a simple daily floor coin-in forecast (e.g. weekday average) on Jan-Apr, compare against a constant training-mean baseline on May-Jun, report MAE in dollars, freeze both before testing, no later-published tourism/survey data as inputs. Not beating the baseline is fine if validation is honest.

## Common issues (traps - never do the left column)
- Ranking machines by total house win -> adjust for luck (theo), availability, time on floor.
- Treating player-vs-machine mismatch as broken data -> player tables are carded play only; use `carded_*` columns in `machine_day` to compare.
- Averaging daily ratios -> use ratio of sums: `SUM(house_win)/SUM(coin_in)`.
- Joining `sessions` to `fnb_transactions` row by row then summing -> aggregate each table first, then join.
- Counting not-installed/retired days as zero sales -> 1,018 rows in `prepared_daily_view` and `machine_day` are not-installed/retired days; `WHERE active` removes exactly those (verified). Exclude, or compare per day on floor.
- Joining `machine_day` to `placements` by machine only -> join on the interval `[effective_from_utc, effective_to_utc)`.
- Assuming a machine never moves -> use `placements` / `prepared_daily_view` for location by date.
- Assuming 24-hour days -> 2025-03-08 has 23 hours; use `scheduled_seconds` from `calendar_day`.
- Missing traffic count = 0 -> missing means counter offline; check `counter_status`.
- Traffic counts as unique visitors -> they are entries; seated players are not counted.
- Mixing cents and dollars -> `_cents` integer cents, `_usd` dollars.
- Subtracting `comp_cost_usd` and `linked_pos_cogs_usd` -> comp cost is already inside cogs; subtract once. Same for `economic_cost_cents` in the loyalty ledger.
- Calling negative house win an error -> real, and luck.
- Treating `trips` as whole Vegas trips -> they are visits to this casino only.
- Applying LVCVA survey numbers to this casino's guests -> they describe all Las Vegas visitors.
- Random train/test split -> split by time.
- Leaking the future (e.g. next week's repairs) -> use only what was known on the prediction date; `lag_*` columns are model-safe.
- "Unusual payout = cheating" -> inspect, never accuse.
- Also: gaming day = 06:00-06:00 local; convert event `_utc`/`_local` timestamps to gaming date before daily grouping. Large files (`machine_hour`, `sessions`, `loyalty_ledger`, 750k+ rows): use Parquet + DuckDB, aggregate before BI tools. Prefer `.parquet` for code.

## Money definitions
| Term | Definition |
|---|---|
| Coin-in | Total wagered, including replayed winnings |
| Payout | Total paid back by the game |
| House win | Coin-in - payout (can be negative) |
| Hold | House win / coin-in (use ratio of sums) |
| RTP | Game's long-run payout rate (`configured_rtp`) |
| Theo | Expected house win = coin-in x (1 - RTP) |
| Luck residual | Machine: house win - theo. Player table: tracked net + theo |
| Player net (`tracked_net_usd`) | Payout - coin-in (player view, opposite sign of house win) |
| Tracked contribution | Tracked gaming win + linked F&B cash - linked F&B cogs - other redeemed benefit costs (carded only; label `tracked` when coverage is partial) |
| Average bet | Sum coin-in / sum paid spins |
| Hit rate | Payout-positive spins / paid spins (a positive payout can be less than the wager) |
| Comp reinvestment | Redeemed comp economic cost / theo, handle zero denominators, state the period |
| Total game payout | Jackpots/handpays counted once |
| Ratios | Fractions (0.095 = 9.5%); undefined when the denominator is zero |
| Property-day contribution (`property_day.contribution_after_supplied_costs_usd`) | `house_win_usd + pos_cash_usd - pos_cogs_usd - machine_supplied_costs_usd - tech_labor_cost_usd` (tech labor IS included; fact-checked by the user) |
| Machine-day contribution (`prepared_daily_view.contribution_after_supplied_costs_usd`) | house win - lease, service, power, repair (no POS, no tech labor); subtract each cost once |
| Comp face value | Menu price of comped items; not cash revenue |
| Comp cost | Cost to house; already inside POS cogs |
| Availability ratio | available / scheduled hours |

Budget cost per action: `quantity x (unit_cost_cents + recurring_cost_cents_per_day x max(0, 30 - lead_days)) / 100`. Fixed packages charged in full; purchases charged in full. Lease example: 14-day lead -> $2,500 + 16 x $55 = $3,380. Worked example (DATASET.md): guest wagers $500 via replay, gets $460 payout, cashes out $60 -> player gaming net is -$40 (not +$460); theo at 92% RTP is $40.
Supplied costs are partial (no rent, taxes, depreciation, full staffing): call the metric "contribution after supplied costs", never "profit". Zero play, negative daily house win and payout above 100% are valid.

## $100,000 budget rules
30 days from July 1, 2025. Up to **3 action types** from `action_catalog`; keeping money is valid (uses no slot) and is the right answer if the cause is luck. Respect `quantity_limit`, `lead_days`, downtime and incompatibilities: no conflicting moves/replacements on one machine; no comp pilot together with the floor-wide comp change. Catalog gives prices, not results: estimate benefit from data and state uncertainty. For each action state cost, expected effect, uncertainty, measurement method.

## Rules
Don't present findings as facts about a real casino. Test an alternative explanation for every pattern. No accusations. Report player outcomes honestly; no ideas that push heavy losers to gamble more (protective ideas welcome). AI use allowed with disclosure. Outside data allowed if public and cited.

## Submission checklist (Devpost)
- [ ] Public interactive dashboard (link or file, any tool); test the link in a private browser window; file submissions include opening instructions
- [ ] Video walkthrough, 2 minutes or less, showing the dashboard and explaining priced actions
- [ ] Write-up, 400 words or less
- [ ] One ML/time-series method informing a decision, vs a simple baseline on a time-based holdout
- [ ] All code or transformation steps
- [ ] Up to 3 priced action types, each with cost, expected effect, uncertainty, measurement plan
- [ ] AI-use disclosure (in appendix)
- [ ] Claims & Evidence appendix: per claim, table/query -> result -> alternative explanation -> limitation (attached file or public link; separate from the 400 words)

## Working conventions
- Update `HANDOFF.md` at the end of any session that changes state (see hackathon-skills:session-handoff-maintenance).
- Tooling decisions (opt-in-picker) are still pending; default is to add nothing.
- Python: use the project venv `.venv` (duckdb, pyarrow, pandas installed). Run `.venv\Scripts\python.exe -I script.py`. Data lives in `../dashboard-royale/data/`; verify with `scripts/verify_data.py` and `scripts/verify_semantics.py` there.
