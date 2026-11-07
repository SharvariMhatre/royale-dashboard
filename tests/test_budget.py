"""Run: python -I tests/test_budget.py"""
import sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import budget

cat = budget.catalog()
def line(a, q, tg="", cost=None):
    c = cat.loc[a]; cost = budget.guide_cost(c, q) if cost is None else cost
    return {"action": a, "quantity": q, "targets": tg, "cost_usd": cost, "expected_benefit_usd": 10., "low_estimate_usd": 0.,
            "high_estimate_usd": 20., "confidence": "low", "how_to_measure": "m"}
assert budget.guide_cost(cat.loc["A-REPLACE-LEASE"], 1) == 3380.0   # guide example: 2,500 + 16 x 55
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    pd.DataFrame([line("A-REPLACE-LEASE", 2, "M-1,M-2"), line("A-INSPECT", 1, cost=999)]).to_parquet(t / "p1_actions.parquet")
    pd.DataFrame([line("A-MOVE-MACHINE", 1, "M-2"), line("A-COMP-PILOT", 1), line("A-COMP-CHANGE", 1), line("A-PROMO", 1),
                  {**line("A-INSPECT", 1), "action": "Machine inspection and paytable verification"},      # name instead of id
                  {**line("A-INSPECT", 1), "action": "Teleport slots"}]).to_parquet(t / "p2_actions.parquet")
    d = budget.load_proposals(t, cat)
    assert d.loc[d.cost_usd == 999, "issues"].iloc[0].startswith("cost mismatch")      # wrong cost flagged
    assert (d.action_type_id == "A-INSPECT").sum() == 2 and d.action_type_id.isna().sum() == 1
    assert "not in the catalogue" in d.issues.iloc[-1]
    e = " | ".join(budget.check_plan(d, cat))
    for must in ("action types", "comp pilot", "machine M-2"):
        assert must in e, e
    ok = d[d.action_type_id.isin(["A-INSPECT", "A-TECH-SHIFT", "A-REPLACE-LEASE"])]
    assert budget.check_plan(ok, cat) == [], budget.check_plan(ok, cat)
    big = d[d.action_type_id == "A-PROMO"].assign(quantity=20, cost_recomputed_usd=1_500_000.0)
    errs = budget.check_plan(big, cat)
    assert any("exceeds" in x for x in errs) and any("limit" in x for x in errs)
    bad_range = pd.DataFrame([{**line("A-INSPECT", 1), "expected_benefit_usd": 50.}]); bad_range.to_parquet(t / "final_budget_plan.parquet")
    assert "outside" in budget.load_proposals(t, cat, stems=("final_budget_plan",)).issues.iloc[0]
print("budget: all checks passed")
