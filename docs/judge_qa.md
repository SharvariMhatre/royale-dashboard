# Likely judge questions

**1. Why is M-1181 Bad spot when luck is Not supported?**
These are two different questions. Bad spot answers why its total is low: it earns 94% of same-game peers, which is normal for its game, but its zone earns 65% of the floor rate for the same games, so its expected win is low. Luck percentile asks whether it also fell short of that low expectation: only 0.9% of fair replays did worse, so luck alone does not explain the extra shortfall. Both can be true. The Inspect rule needs |z| > 3.29 (under 0.1% by chance). M-1181's z is -2.41, well inside that, so it is not an inspect lead, while M-1158 sits at -4.57. The zone stays the main driver, so the verdict is Bad spot. With 310 machines, 6 fall below 1% where about 3.1 would by chance, so one machine at 0.9% is not enough to call a fault.

**2. How do you know it is the location and not the machines?**
Four checks point the same way. The zone earns 65% of the floor rate for the same games (the zone index compares each game with the same game across the floor). The same games elsewhere earn more. Back Forty dipped to 46% of the rest of the floor while its walkway was closed (67% before, 64% after). And M-1152 more than doubled its earnings per available hour after moving to Main Entrance (+106% vs unmoved machines). The limit: only 4 machines moved, so the move evidence is thin and we say so.

**3. How was the model validated?**
Train 2025-01-01..2025-04-30, test 2025-05-01..2025-06-30 (61 days), split by time, frozen before testing. Weekday plus events misses by $50,920 a day against $218,258 for a constant baseline. MLflow run IDs are on the Model page. We reproduced the weekday average result independently. No later-published data was used.

**4. Why not just replace the 10 machines?**
0 of the 10 are truly bad, and 9 sit in the weakest zone, so new machines in the same spots would face the same zone. The GM's plan costs $220,000, more than the whole budget, and the team estimates $0 benefit.

**5. Are the leak clues accusations?**
No. There are 165 clues on 103 machines. They are rule flags to inspect, such as long outages or repeat faults. Downtime in total is 0.38% of scheduled hours, so it does not explain the bottom 10.

**6. How will you know the plan worked?**
Each action has one metric and a control or baseline. Inspection: July hold against the 90% payout rate. Signs: Back Forty expected win per hour, 20 live days after install against the 30 days before, with the other zones as comparison. Moves: each moved machine has a same-game partner left in place, and we keep measuring into August because 30 days is short. Moves and signs may keep paying after day 30; the Overview shows payback (0.4 months for the inspection, 1.4 for signs, 1.2 for moves) as a labelled assumption beyond the guide's 30-day window. The plan spends $14,100 and keeps $85,900; expected benefit is $12,537, range $0 to $27,874.
