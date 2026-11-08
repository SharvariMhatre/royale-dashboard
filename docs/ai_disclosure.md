# AI-use disclosure

Dashboard Royale entry, The Gilded Ace: Floor Doctor. TAMU Datathon 2026.
Team: Sharvari Mhatre, Aditi, Bharath, Nikita.

AI tools are allowed by the challenge rules with disclosure. This page lists what we used, what it was used for, and what people decided and checked.

## Tools used
| Tool | Who | Used for |
|---|---|---|
| **Claude** (Anthropic): Claude Code in the terminal (Claude Sonnet 5.5, Claude Opus 5.5 at times) and Claude on claude.ai | Whole team | Planning the work split, reading the challenge guide, writing and debugging Python, SQL and PySpark code, building the Streamlit dashboard, reviewing results against the rubric, drafting documents and team messages |
| **ChatGPT** (OpenAI) | Whole team | Brainstorming approaches, explaining methods and errors, checking code and wording |

All analysis code ran on the challenge data in Databricks notebooks (Spark SQL, PySpark) and in Python on our laptops. Model runs were tracked in MLflow.

## What AI helped with, by person
| Person | Role | AI helped with | Where |
|---|---|---|---|
| **Aditi** | Data builder (Q3 downtime, Q5 comps) | Cleaning-pipeline code, downtime and comp-cost queries, leak-clue rules, priced action estimates and claims | Databricks `p1_*` notebooks and tables |
| **Bharath** | Machine detective (Q1) | Spark code for 10,000 fair luck replays per machine, same-game peer comparison, zone index, walkway-closure and moved-machine analyses, verdict rules, claims and actions | Databricks `p2_*` notebooks and tables |
| **Nikita** | Predictor (Q2 demand, Q4 players, model) | Demand and player-concentration queries, the weekday and weekday-plus-events forecasts with a constant baseline, MLflow tracking, claims and actions | Databricks `p3_*` notebooks and tables |
| **Sharvari Mhatre** | Dashboard, integration and submission | Streamlit dashboard and its design (pages, floor map, illustrations, themes), the Databricks export script, file validator, budget checks, tests, write-up, evidence appendix and judge Q&A drafts | This repository: `app/`, `src/`, `tests/`, `docs/` |

## What people decided
- **The questions, rules and conclusions are the team's.** We set the working rules the AI followed: ratio of sums, off-floor rows excluded (exactly 1,018), calendar-day hours (March 8 has 23), cents to dollars once, unusual payouts are leads to inspect and never accusations, and no individual player shown.
- **We chose every threshold and verdict:** the luck bands (Supported at 20% or more, Unlikely 1 to 20%, Not supported under 1%), the inspect rule (|z| > 3.29), the bad-spot and short-exposure rules, and the verdict names.
- **We rejected or corrected AI output several times.** Examples: a first "Unlucky" rule was too loose (125 of 310 machines) and was tightened to a 20% size test; a first idea that game settings explained the bottom 10 was disproved by the data (the same games earn 35-48% more in other zones); a mislabelled zone comparison was corrected to "65% of the floor rate for the same games"; a "10,000 replays" caption was held until we verified it in Databricks.
- **The $100,000 plan is a team decision:** inspect M-1158, signs for Back Forty, and move 3 machines with 3 matched controls, for $14,100, keeping $85,900. The sign-lift assumption (2%, range 0 to 5%) is ours and is labelled as an assumption.

## How AI output was checked
- **Independent cross-checks:** demand coin-in equals the property-day total exactly ($248,905,219); comp cost matches across two tables ($190,669); an independent weekday-average forecast reproduces the team's MAE to the dollar ($68,699); the downtime table has exactly 55,092 on-floor rows.
- **Verified in Databricks by a person:** the luck scores need four decimal places for 276 of 310 machines, which is only possible with 10,000 replays per machine.
- **Automated tests:** a contract validator for every exported table, budget rules checked against the guide's worked example ($3,380 lease line), and contrast tests for the dashboard colours.
- **Manual checks:** every page was run after each change and checked in a browser, including the four judge tests (change period, drill into a bank and a guest group, find the model validation, trace a recommendation to its evidence).

## Limits
- The data is synthetic (release 0.9.0-draft), so findings are not facts about a real casino.
- AI can make mistakes; every number shown in the dashboard and documents comes from data files, not typed text, and was reviewed by the team.
- AI-drafted text was read and approved by Sharvari Mhatre on Nov 8, 2026, for the team.
