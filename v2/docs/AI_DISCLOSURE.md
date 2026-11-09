# AI-use disclosure (v2)

The v2 floor review was built after TAMU Datathon 2026 judging by Sharvari Mhatre with Claude (Anthropic) in Claude Code, as a coding, analysis and writing assistant. The submitted entry (Streamlit app in `app/`, Databricks notebooks by Aditi, Bharath and Nikita) is unchanged and keeps its own disclosure in `docs/ai_disclosure.md`.

## What Claude did
- Wrote the DuckDB pipeline (`v2/analysis/`), the static dashboard (`v2/site/`), the verification script, the browser parity test, the Cloudflare Worker and these documents.
- Proposed methods and options; Sharvari chose among them. Choices are logged in `v2/DECISIONS.md`.

## What we learned from other entries, and how it is labelled
After judging we studied published entries in the Devpost gallery. We then ran our own column-by-column sweep of the data (`v2/SWEEP.md`) and built only on what that sweep and our own submission surfaced. Where a result overlaps a finding another team published first, we say so:
- **M-1158's hit rate (38.6% vs 31.5%)** was published first by other teams (for example "Luck, Location, or a Leak? The Gilded Ace Floor Review" and "Kafo"). Our additions are the meter-integrity audit of all 776,297 sessions, the smaller award per hit, and the per-bet, per-month and carded/uncarded breakdowns.
- **Repair waits and technician shortfalls** were also reported by other teams.
- **The walkway closure, the same-slot replacement and the moved machine** come from our own submitted entry; the placebo test is new in v2.
- General techniques (placebo tests, rolling-origin CV, scoring every legal plan, an AI analyst limited to verified facts, an assertion suite) are standard methods. We list them here because we adopted them after seeing them used well.

## How AI output was checked
- `v2/analysis/verify.py`: 40 checks re-derive every headline number from the raw tables and exit 1 on any mismatch.
- `v2/tests/browser_parity.cjs`: the dashboard's in-browser engine matches the Python pipeline for all 310 machines (verdict, luck z, hit-rate z, peer index, theo).
- Claims were removed when a check failed. For example, a "Platinum redemptions quadrupled after the comp change" lead was dropped because the rise had started in January (tier upgrades), not on May 1.
- Every page was reviewed in a browser at desktop and phone width.

## Limits
The data is synthetic (release 0.9.0-draft). Plan effects are assumption ranges grounded in this data, each listed on the dashboard. The "Ask the floor" assistant answers known questions in the browser from verified numbers; free-form questions go to Claude only if a Worker is configured, and it receives only the published facts.
