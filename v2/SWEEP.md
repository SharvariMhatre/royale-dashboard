# Data-dictionary sweep (hour 0)

Every table in `data/` read against `reference/DATA_DICTIONARY.md`. Columns that measure a **mechanism** (a rate, probability or per-event count) are marked M. "Overlap" marks a finding another team published, which we learned about after judging (see the AI disclosure).

## Mechanism columns and what they can test

| Table.column | M | Trap | Question it can answer |
|---|---|---|---|
| `machine_day.sum_bet_squared` x `game_math.payout_multiplier_variance` | M | none | Exact luck SD per machine; no simulation needed |
| `machine_day.payout_positive_spins` / `game_math.hit_probability` | M | A "hit" can pay less than the bet | Does a machine pay as often as its game says? (overlap: Floor Review, Kafo) |
| `game_math.bet_options_cents` vs `sessions.fixed_bet_cents` | M | none | Are the meters recording only legal bets? |
| `game_math.payout_increment_cents` vs `sessions.payout_cents` | M | none | Are all payouts multiples of the game's increment (meter arithmetic)? |
| `sessions.coin_in_cents` vs `fixed_bet_cents x paid_spins` | M | none | Does coin-in reconcile spin by spin? |
| `machine_day.carded_*` vs totals | M | Player tables are carded only | Does the anomaly appear in carded and uncarded play alike? |
| `operations.opened_at / recorded_at / work_started_at / available_at` | M | Waits can be negative (tech already working) | Where does downtime come from: detection, wait or repair? |
| `zone_traffic_hourly.entries_count`, `counter_status` | M | Null = offline, not zero; entries, not people | Is a zone short of people or short of play per person? |
| `shift_roster.planned_headcount` vs `actual_headcount` | M | none | Does understaffing lengthen repairs? (overlap: Floor Review, Clt_Alt) |
| `loyalty_ledger.available_at_utc` vs `event_at_utc` | | Model leakage if used before it was known | When did the comp change become visible? |
| `events.announced_date` | | Leakage | Only events announced before a forecast date may be features |
| `cost_rules` lease classes | | Revenue share is 20% of positive daily win | Does replacing a revenue-share machine cost the same as a fixed lease? |
| `5_optional/visitor_profile_monthly.used_loyalty_card` | | Survey, sampling error | Does the survey's card use match the meters' carded share? |

## What the sweep found (our own checks)

1. **Meter arithmetic is clean everywhere.** All 776,297 carded sessions use a legal bet, every payout is a multiple of its game's increment, and coin-in equals bet x spins on every session. So any payout anomaly is not a counting error.
2. **M-1158 runs like a different paytable.** Same game (Desert Gold, `G-STD90`) as its peers, but it pays on 38.6% of spins vs 31.5% configured (overlap) with a smaller award per hit (2.50x the bet vs 2.85x for its peers). That holds at every bet level (50, 100, 200 cents), every month, and in both carded (2.4% hold) and uncarded (4.3%) play. Effective return is about 97.6% vs 90% configured. Meters are clean (finding 1), so the likely cause is the paytable loaded on the machine: an inspection item, not an accusation.
3. **Fault detection is the same in every zone** (median 7 to 9 minutes from failure to ticket). Back Forty is not slower to notice breakdowns, so downtime does not explain its weak earnings.
4. **No tampering reports name any of the GM's 10.** All 33 machine-tampering reports name other machines.
5. **Lease mix of the GM's 10:** 4 fixed lease, 4 revenue share, 2 owned. Replacing a revenue-share machine with a fixed lease changes the cost line, which the plan search must price.

## Five unasked questions worth building

1. Which paytable is M-1158 effectively running, and what does it cost per day? (mechanism)
2. The same slot was replaced in May (M-1120 to M-5076): what did the replacement actually change? (our own natural experiment)
3. Is the walkway effect bigger than every fake closure date? (placebo)
4. Of every legal $100K plan, where does ours rank, and what would the GM's plan return? (plan search)
5. Does the forecast's interval cover what it claims? (calibration)
