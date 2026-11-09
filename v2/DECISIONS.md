# Decision log (v2)

Claude proposes options and the ambitious version; Sharvari decides. Nothing is "Decided" until she says so.

| ID | Date | Question | Options | Decision | Rationale | Decided by |
|---|---|---|---|---|---|---|
| D-01 | 2026-11-09 | Where v2 lives | New repo; upgrade royale-dashboard | Upgrade royale-dashboard on branch `v2`; the submitted Streamlit app stays in `app/` | Keep one link and history | Sharvari |
| D-02 | 2026-11-09 | Stack | Static page that recomputes in the browser + AI analyst; Next.js + live Databricks; keep Streamlit | Static page + AI analyst | Every filter recomputes instantly, no server to sleep, judges can do things | Sharvari |
| D-03 | 2026-11-09 | Other teams' ideas | Rebuild and credit; only our own ideas | Only our own ideas. Our own column sweep runs fresh; any overlap with a published entry is labelled in the AI disclosure as "studied other entries after judging" | Honesty about what we learned after judging | Sharvari |
| D-04 | 2026-11-09 | Databricks | Real workspace; Free Edition | Real workspace (`workspace.casino`), later phase | Access still works | Sharvari |
| D-05 | 2026-11-09 | Luck test | 10,000 Spark replays; closed form | Closed form: z = (house win - theo) / sqrt(sum_bet_squared x payout_multiplier_variance). Spark compute moves to work that needs it | The replays drew normal noise with the same SD, so they reproduce the closed form exactly | Proposed by Claude |
