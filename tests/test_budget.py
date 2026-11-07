"""Run: python -I tests/test_budget.py"""
import sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import budget

def line(a, q, tg="", cost=None, lead=None):
    cat = budget.catalog().loc[a]
    return {"action_type_id": a, "name": a, "quantity": q, "targets": tg, "lead_days": int(cat.lead_days if lead is None else lead),
            "operating_days": 0, "cost_usd": budget.guide_cost(cat, q) if cost is None else cost, "estimate_lo_usd": 0., "estimate_hi_usd": 1.,
            "assumption": "a", "metric": "m", "measurement_method": "m", "evidence_ref": "e"}
assert budget.guide_cost(budget.catalog().loc["A-REPLACE-LEASE"], 1) == 3380.0   # guide example
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    pd.DataFrame([line("A-REPLACE-LEASE", 2, "M-1,M-2"), line("A-INSPECT", 1, cost=999)]).to_parquet(t / "p1_actions.parquet")
    pd.DataFrame([line("A-MOVE-MACHINE", 1, "M-2"), line("A-COMP-PILOT", 1), line("A-COMP-CHANGE", 1), line("A-PROMO", 1)]).to_parquet(t / "p2_actions.parquet")
    d = budget.load_proposals(t)
    assert d.loc[d.action_type_id == "A-INSPECT", "flags"].iloc[0].startswith("cost mismatch")      # wrong cost flagged
    e = " | ".join(budget.check_plan(d))
    for must in ("action types", "comp pilot", "machine M-2"):
        assert must in e, e
    ok = d[d.action_type_id.isin(["A-INSPECT", "A-TECH-SHIFT", "A-REPLACE-LEASE"])]
    assert budget.check_plan(ok) == [], budget.check_plan(ok)
    big = pd.concat([d[d.action_type_id == "A-PROMO"]] * 1); big = big.assign(quantity=20, cost_recomputed_usd=1_500_000.0)
    assert any("exceeds" in x for x in budget.check_plan(big)) and any("limit" in x for x in budget.check_plan(big))
print("budget: all checks passed")
