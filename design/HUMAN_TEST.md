# Human test kit (written, NOT run)

Purpose: pick the default skin on evidence from real readers, not on my taste. Status: **not run**; no results exist. Needs 5 to 8 people who have not seen the dashboard (a teammate counts only for the trust scale, not the task test). Run each person on **one** skin only (between-subjects), balanced across the four: `default`, `noir`, `control`, `paper`. Use a laptop at about 1440px wide, and 2 people per skin on a phone (390px).

URLs (replace HOST with the local or deployed address):
`HOST/?skin=default`, `HOST/?skin=noir`, `HOST/?skin=control`, `HOST/?skin=paper`

## Test 1: five seconds (first impression)
1. Show the Overview for 5 seconds, then hide it.
2. Ask: "What is this page about? What is the main message? What would you click first?"
3. Score: correct purpose (Y/N), message recalled (Y/N: "do not replace the 10, fix the spot" or equivalent), first click is a machine card or a filter (Y/N).
Expected: a decision page about replacing 10 slot machines; the message is that the 10 are mostly not truly bad machines and the problem is the zone (Back Forty).

## Test 2: tasks (timed, think aloud)
| # | Task | Expected answer (source: current data, Overview and Model pages) | Time limit |
|---|---|---|---|
| T1 | "How many of the GM's 10 machines are truly bad, and where do most sit?" | 0 of 10 truly bad; 9 of 10 in Back Forty | 60 s |
| T2 | "Change the period to a custom range and tell me the Wagered figure on Players & Comps." | Reader finds the Period filter, picks Custom range, opens the calendar, and reads the new figure; the figure must change from the full-period value | 120 s |
| T3 | "Pick one machine on the GM's list and say why it looks weak and whether that is real." | Opens a card (e.g. M-1158: hold 3.0% vs 10.0% expected, z = -4.57, verdict Inspect) and states the verdict and reason in their own words | 120 s |
| T4 | "How was the forecast validated, and does it beat the simple baseline?" | Model page: train Jan-Apr, test May-Jun, split by time; model average miss $50,920 per day vs $218,258 for the constant baseline (77% better) | 90 s |
| T5 | "Show me the evidence behind one recommended action." | Opens an "Evidence:" expander under a plan line | 90 s |
Record per task: success (Y/N), time, number of wrong clicks, any moment of "I can't read this", and a one-line comment. Do not hint. Stop at the limit and mark fail.

## Test 3: trust and comfort (after the tasks, 1 to 5, 1 = strongly disagree)
1. "I could read every number comfortably."
2. "I would trust these numbers to make a $100,000 decision."
3. "The look helped me find the evidence."
4. "The look was distracting."  (reverse-scored)
5. "I would be happy to show this to my boss."
Also ask: "Which words describe it?" (open) and "Was anything hard to read?" (open).

## Score sheet (copy per participant)
| Field | Value |
|---|---|
| Participant / date | |
| Skin | default / noir / control / paper |
| Device and width | |
| 5-second test: purpose / message / first click | Y N / Y N / Y N |
| T1 success, seconds | |
| T2 success, seconds | |
| T3 success, seconds | |
| T4 success, seconds | |
| T5 success, seconds | |
| Trust Q1 to Q5 (Q4 reversed) | |
| Unreadable moments (where) | |
| Comments | |

## Decision rule (set before running, so results cannot be bent afterwards)
Rank skins by (1) task success rate T1 to T5 (all must be >= the default's), (2) median task time, (3) mean trust score. Reject a skin that scores below the default on task success even if people like the look. If two skins tie, prefer the one with fewer "can't read this" reports. With so few participants this is a signal, not proof; say so when reporting.

## Do not
- Do not tell participants which skin is which, or which one you prefer.
- Do not run the live Streamlit Cloud wrapper tests as a skin comparison: its buttons and badge cannot be restyled and look the same in every skin.
