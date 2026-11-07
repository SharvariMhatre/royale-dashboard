# The Gilded Ace: should we replace the 10 lowest machines?

## Problem
The GM wants to replace the 10 lowest-earning machines (Jan 1 to Jun 30, 2025). Low earnings can come from luck, location or a leak. We tested all three before choosing.

## What we found
- 0 of the GM's 10 are truly bad: 6 bad spot, 3 short exposure, 1 inspect.
- 9 of the 10 sit in Back Forty, which earns 65% of the typical zone per available hour. During the walkway closure it earned 46% of the rest of the floor, against 67% before and 64% after.
- M-1120 was retired and M-5076 was installed on 2025-05-13 in the same slot (L-38-5). One slot fills two places on the list, and both had short times on the floor.
- M-1158 is an inspect lead: hold 3.0% against 10.0% expected, and no fair replay did as badly. This is a lead to check, not an accusation.

## How we tested it
- Luck: 10,000 fair replays per machine in Databricks. Luck is a supported explanation for 5 of the 10, unlikely for 3 and not supported for 2. Across the floor 6 machines fall below 1%, against about 3.1 expected by chance.
- Peers: each machine against the same game elsewhere on the floor.
- Moves: 4 machines moved. M-1152 went from Back Forty to Main Entrance and earned 106% more per available hour than the unmoved floor. 4 moves is thin evidence.
- Downtime: 0.38% of scheduled hours, at most $90,663 of expected win. It does not explain the list.

## Model
A weekday plus events forecast of daily coin-in misses by $50,920 on May and June, against $218,258 for a constant baseline. Trained on 2025-01-01..2025-04-30, tested on 2025-05-01..2025-06-30, split by time and frozen before testing.

## $100,000 plan
PENDING: team decision at 6 PM. For comparison, the GM's own plan (replace 10 machines) costs $220,000 and the team estimates $0 benefit.

## How we would measure it
Each funded action gets one metric, a baseline or control, and a 30-day check. Example: for an inspected machine, compare July hold with its confidence interval. Final measures follow the plan decision.
