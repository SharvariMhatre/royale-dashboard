# Likely judge questions

**1. Why is M-1181 Bad spot when luck is Not supported?**
These are two different questions. Bad spot answers why its total is low: it earns 94% of same-game peers, which is normal for its game, but its zone earns 65% of the floor, so its expected win is low. Luck percentile asks whether it also fell short of that low expectation: only 0.9% of fair replays did worse, so luck alone does not explain the extra shortfall. Both can be true. We keep the verdict Bad spot because the zone is the main driver, and it is not flagged Inspect because the inspect rule fired only on M-1158. With 310 machines, 6 fall below 1% where about 3.1 would by chance, so one machine at 0.9% is not enough to call a fault.

**2. How do you know it is the location and not the machines?**
Four checks point the same way. The zone earns 65% of the typical zone per available hour. The same games elsewhere earn more. Back Forty dipped to 46% of the rest of the floor while its walkway was closed (67% before, 64% after). And M-1152 earned 106% more after moving to Main Entrance. The limit: only 4 machines moved, so the move evidence is thin and we say so.

**3. How was the model validated?**
Train 2025-01-01..2025-04-30, test 2025-05-01..2025-06-30 (61 days), split by time, frozen before testing. Weekday plus events misses by $50,920 a day against $218,258 for a constant baseline. MLflow run IDs are on the Model page. We reproduced the weekday average result independently. No later-published data was used.

**4. Why not just replace the 10 machines?**
0 of the 10 are truly bad, and 9 sit in the weakest zone, so new machines in the same spots would face the same zone. The GM's plan costs $220,000, more than the whole budget, and the team estimates $0 benefit.

**5. Are the leak clues accusations?**
No. There are 165 clues on 103 machines. They are rule flags to inspect, such as long outages or repeat faults. Downtime in total is 0.38% of scheduled hours, so it does not explain the bottom 10.

**6. How will you know the plan worked?**
PENDING: depends on the plan chosen at 6 PM. Each action will have one metric, a baseline or control and a 30-day check. The budget page shows how each line would be measured and a payback sensitivity beyond 30 days, labelled as an assumption.
