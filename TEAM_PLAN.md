DEADLINE: hacking ends 12:00 PM Central, Sun Nov 8 2026. Clock: h8=7 PM Sat, h12=11 PM Sat, h14=1 AM Sun, h17=4 AM Sun, freeze 4:30 AM Sun.

# TEAM_PLAN.md — Dashboard Royale + Best Use of Databricks (four people)

Reconciled on 2026-11-07 against GUIDE.md and reference/DATA_DICTIONARY.md. Keeps the four-person structure from Nikita and Bharath's plan and fixes the parts that would lose points.

## Roles (updated 2026-11-07: real file names and owners)
| Person | Role | Question focus | Files (all parquet in `app_data/team/`) | Due |
|---|---|---|---|---|
| Person 1 (Aditi) | Data Builder | Q3 downtime + Q5 comps | `p1_downtime`, `p1_comps`, `p1_leak_clues` (1 AM Sun); `p1_actions`, `p1_claims` (4 AM Sun) | h8 / h14 / h17 |
| Person 2 (Bharath) | Machine Detective | Q1 machines | `p2_verdicts`, `p2_luck_sims`, `p2_move_effects` (1 AM Sun); `p2_actions`, `p2_claims` (4 AM Sun) | h14 / h17 |
| Person 3 (Nikita) | Predictor | Q2 demand + Q4 players + model | `p3_forecast_results`, `p3_model_metrics` (11 PM Sat); `p3_demand`, `p3_players`, `p3_concentration` (1 AM Sun); `p3_actions`, `p3_claims` (4 AM Sun) | h12 / h14 / h17 |
| Person 4 (Sharvari) | Dashboard and Storyteller | all, integration | public Streamlit link, write-up, appendix, video, Devpost | submission |

Rule that protects the Dashboard Royale entry: Sharvari builds a **self-sufficient minimum** version of all six answers from `prepared_daily_view`, `property_day` and `player_period` by hour 6 (see SHARVARI_DASHBOARD.md). Team outputs replace those minimums as they arrive. If a team file is late or invalid, the dashboard still answers the question with the minimum version and says which version is shown.

## Fixes to the original four-person plan (why)
1. **Person 2's verdicts need a peer comparison and uncertainty.** The luck replay says whether the result is unusual for that machine's own play, not whether the machine draws less play than its neighbours. Add: theo per available hour vs the median of same-zone peers (leave-one-out, widen to adjacent zones then floor when fewer than 5 peers), plus a 90% interval from a weekly block bootstrap. Verdicts become: Unlucky, Bad spot, Broken, Inspect, Truly bad, **Mixed / not enough evidence**. The last one must exist.
2. **Location test applies to few machines.** Only machines that moved give a before/after. For the rest, use the peer comparison. Report both and say which was used.
3. **The luck replay is a model estimate, not a benefit estimate.** Show it as "share of simulated six-month periods in which a normal copy of this machine lands in the bottom 10". Never use it to estimate what replacing or moving a machine would earn. Validate it: compare simulated daily spread with observed daily spread of luck_residual per machine (calibration ratio) and report where it fails.
4. **Multiple comparisons.** With 300 machines and calibrated two-sided 90% intervals, about 30 fall outside by chance (about 15 on the low side). State it on the Validation page.
5. **Genie is cut from the submission path.** Judges need a public link without a Databricks login. Genie can be a Databricks-prize demo only, after everything else works, owned by Nikita, not Sharvari.
6. **Live Databricks connection is optional, exported files are the default.** Streamlit Community Cloud can query Databricks SQL with a token in secrets, but it adds a failure mode on judging day. Exported parquet files committed to the repo are the deliverable; the live connection is a stretch for the Databricks prize.
7. **Seven pages becomes five.** Overview (Decision Room), Machine Details, Demand & Downtime, Players & Comps, Model Test & $100K Plan (with the evidence table). Floor map only if time remains. Fewer pages, each complete, beats seven thin ones; chart count earns nothing.
8. **Budget rules from the guide:** cost = quantity × (unit_cost_cents + recurring_cost_cents_per_day × max(0, 30 − lead_days)) / 100; purchased machines at full cost; benefits only for days after lead time; respect quantity_limit and incompatibility_group; comp pilot and floor-wide comp change can't both be chosen; keeping money is valid and uses no slot. Metrics match the action: uptime and contribution for maintenance; machine plus bank/zone totals for moves and replacements; incremental contribution and comp cost for comp changes.
9. **Model honesty.** Train Jan–Apr, test May–Jun, baseline = constant training mean, freeze before testing, report MAE in dollars (and MAPE), say which staffing or promotion decision changes. It may lose to the baseline; report it anyway.
10. **Hour-based deadlines need a clock.** Post the Devpost deadline with time zone in TEAM_PLAN.md line 1 and convert hours 8/12/14/17 to clock times. Reserve the final 30% for integration, rehearsal, video and submission; nothing new after that point.

## Shared definitions (everyone uses these; Aditi's `p1_machine_day_clean` implements them)
- Window 2025-01-01..2025-06-30; gaming day 06:00–06:00; exclude rows with `active = false` or empty `location_id` (about 1,018).
- Hours from `calendar_day.scheduled_seconds` (82,800 on 2025-03-08); availability = available / scheduled.
- Ratio of sums only. Hold = sum(house_win)/sum(coin_in). Theo per available hour = sum(theo)/sum(available_hours).
- `_cents` ÷ 100 exactly once. Comp cost is inside cogs. Carded play compared only with `carded_*` columns.
- Traffic: null `entries_count` or `counter_status != 'ok'` = offline, excluded, coverage reported. Entries, not unique visitors.
- Location by date from `placements` (or `prepared_daily_view`). `floor_walkways` closure is a candidate demand explanation to test.
- Payout anomalies are leads to inspect. No accusations. No individual player IDs; groups of 10 or more. No ideas that push heavy losers to play more.

## File contract (Databricks `workspace.casino` tables, exported to `app_data/team/<table>.parquet` by `src/export_from_databricks.py`)
Extra columns are fine; a missing required column fails ("Pending" on the page). `_meta` sidecars are optional (missing = warning in the page footer). Checked by `src/validate_contracts.py`.
| Table | Required columns | Extra checks |
|---|---|---|
| `p1_downtime` | machine_id, gaming_date, bank_id, zone_id, manufacturer, available_hours, scheduled_hours, availability_pct, lost_theo_usd, cause | |
| `p1_comps` | month, comp_cost_usd, points_earned, points_redeemed, tier | |
| `p1_leak_clues` | machine_id, gaming_date, rule_failed, details | |
| `p2_verdicts` | machine_id, bank_id, zone_id, x, y, house_win_usd, theo_usd, theo_per_hour_usd, availability_pct, luck_score, verdict, reason, dollar_impact_usd, confidence, in_manager_bottom10 | unique machine_id; verdict in {Inspect, Short exposure, Broken, Truly bad, Bad spot, Unlucky, Healthy} |
| `p2_luck_sims` | machine_id, sim_house_win_usd | 500-per-machine sample only |
| `p2_move_effects` | machine_id, from_location, to_location, theo_per_hour_before, theo_per_hour_after, change_pct | |
| `p2_zone_index`, `p2_b40_closure_effect`, `p2_inspection_candidates`, `p2_luck_scores`, `p2_manager_bottom10` | (none) | non-empty |
| `p3_demand` | gaming_date, zone_id, coin_in_usd, traffic_count, event_name | |
| `p3_forecast_results` | gaming_date, actual_usd, baseline_pred_usd, model_pred_usd, split | split in {train, test}; train dates before test dates; unique gaming_date |
| `p3_model_metrics` | model_name, mae_usd, mlflow_run_id | |
| `p3_players` | month, tier, age_band, home_region, wagered_usd, won_back_usd, net_usd, player_count | no player_id; player_count >= 10 |
| `p3_concentration` | top_pct, share_of_net_loss | |
| `p1_claims`, `p2_claims`, `p3_claims`, `all_claims` | claim_id, question, claim, evidence_table, result, alternative_tested, limitation, confidence | unique claim_id |
| `p1_actions`, `p2_actions`, `p3_actions`, `all_actions`, `final_budget_plan` | action, quantity, targets, cost_usd, expected_benefit_usd, low_estimate_usd, high_estimate_usd, confidence, how_to_measure | cost_usd >= 0; quantity > 0; low <= high |

Budget rules (max 3 action types, $100,000, quantity limits, incompatibilities, guide cost formula vs `action_catalog`) are enforced by `src/budget.py`. `bronze_*` tables and the full 10,000-sim tables are never exported. `p1_machine_day_clean` is no longer part of the contract.

## Checkpoints (humans talk)
- C1 (h1): deadline posted, Databricks workspace shared, GitHub repo cloned by all, this contract agreed, 20-row samples of each file cut from `prepared_daily_view`.
- C2 (h8): Person 1's clean tables validated; Sharvari's minimum version of all six questions live on a public link.
- C3 (h12): model file validated; Person 2 explains the verdict method; Sharvari teaches it back.
- C4 (h14): verdicts and Q2–Q5 files wired; budget draft reviewed against verdicts.
- C5 (h17): budget wired; freeze numbers; run everything from scratch once.
- C6 (final 30%): rehearsal, timed judge tests, video, write-up, Devpost draft, private-window checks, wake the app before judging.

## Cut order
Floor map, Genie, live Databricks connection, automatic re-run job polish, Missouri/weather anchors, model version 2, visual polish. Never cut: six questions, four judge tests, honest validation, evidence table, priced plan, video.
