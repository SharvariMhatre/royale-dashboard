# AI-use disclosure

Dashboard Royale entry, The Gilded Ace. AI use is allowed by the rules; this lists what was used, for what, and what people decided.

## Tools
- **Claude Code** (model: Claude Sonnet 5.5) ran in the dashboard owner's terminal, inside the project folder, from Nov 7, 2026. A running log is in `notes/ai_log.md` and the task history in `PROGRESS_sharvari.md`.
- **Databricks AI features** used by the three analysts: [TEAMMATES TO FILL IN: for example Databricks Assistant, Genie, MLflow. Name the feature, the notebook and what it produced. Not recorded in this repo.]

## What Claude Code did
| Area | What the AI wrote or did | Where |
|---|---|---|
| Project setup | Folder layout, `.gitignore`, requirements, first Streamlit skeleton | `app/`, `requirements.txt` |
| Minimum analysis | Per-machine house win, expected win, peer and zone indices, first-pass labels; Q2 to Q6 tables; a weekday-average forecast with a constant baseline | `src/minimum.py` |
| Data checks | Contract validator and unit tests for the team's exported tables | `src/validate_contracts.py`, `tests/` |
| Budget rules | Guide cost formula, 3-action-type limit, $100,000 cap, quantity limits, incompatibility checks, payback sensitivity | `src/budget.py` |
| Export and merge | Script that pulls the team's tables from Databricks using credentials in a git-ignored `.env` (never shown to or stored by the AI), and a script that merges claims and builds the numbers the pages show | `src/export_from_databricks.py`, `src/integrate_team.py` |
| Dashboard | Six pages, filters, tables and charts, wording of labels and captions | `app/` |
| Documents | First drafts of the write-up, the evidence appendix and the judge Q&A, generated from the findings files so every number comes from data | `src/make_docs.py`, `docs/` |

## What people decided
- The dashboard owner set the rules the AI worked under: ratio of sums, off-floor rows excluded, calendar-day hours, no accusations, every displayed number traceable to a findings file.
- People chose the questions, the label thresholds, the order of the label rules and the verdict names, and rejected or changed AI output several times (for example the first "Unlucky" rule was too loose and was tightened to a 20% size test, and an unverified "10,000 replays" caption was held until the team confirmed it).
- The analysts built the Databricks pipeline, the luck simulations, the zone and move analyses, the forecasts and the action estimates, and wrote their own claims.
- The $100,000 plan is a team decision (pending at the time of writing).

## How AI output was checked
- Unit tests for the validator and the budget rules (cost examples from the guide, such as the $3,380 lease line).
- Cross-checks between independent sources: total coin-in in the demand table equals the property-day total ($248,905,219); comp cost totals match across two tables; an independent weekday-average forecast reproduces the team's result to the dollar.
- Every page was run headless after each change, with filters changed, and checked again in a browser by a person.

## Limits
- The data is synthetic (release 0.9.0-draft), so findings are not facts about a real casino.
- AI-drafted text was reviewed by a person before submission. [OWNER TO CONFIRM AFTER FINAL READ.]
