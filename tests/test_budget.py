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
# payback sensitivity: only permanent actions, cost recovered at cost/benefit months, linear in months
pb = budget.payback(pd.DataFrame([
    {"action_type_id": "A-INSPECT", "cost_recomputed_usd": 1200., "expected_benefit_usd": 600., "low_estimate_usd": 0., "high_estimate_usd": 1200.},
    {"action_type_id": "A-MOVE-MACHINE", "cost_recomputed_usd": 1000., "expected_benefit_usd": 0., "low_estimate_usd": -5., "high_estimate_usd": 5.},
    {"action_type_id": "A-PROMO", "cost_recomputed_usd": 1., "expected_benefit_usd": 1., "low_estimate_usd": 1., "high_estimate_usd": 1.}]))
assert list(pb.action_type_id) == ["A-INSPECT", "A-MOVE-MACHINE"]
assert pb.months_to_pay_back.iloc[0] == 2.0 and pd.isna(pb.months_to_pay_back.iloc[1])
assert pb.net_3m_expected.iloc[0] == 600. and pb.net_6m_high.iloc[0] == 6000. and pb.net_3m_low.iloc[1] == -1015.
print("payback: all checks passed")
# DECIMAL columns (as exported from Databricks) must not break the cost check
from decimal import Decimal
with tempfile.TemporaryDirectory() as t2:
    t2 = Path(t2)
    pd.DataFrame([{**line("A-INSPECT", 1), "cost_usd": Decimal("1200.00"), "expected_benefit_usd": Decimal("2897.0"),
                   "low_estimate_usd": Decimal("0"), "high_estimate_usd": Decimal("5794")}]).to_parquet(t2 / "final_budget_plan.parquet")
    dd = budget.load_proposals(t2, cat, stems=("final_budget_plan",))
    assert dd.issues.iloc[0] == "" and dd.cost_recomputed_usd.iloc[0] == 1200.0
print("decimal columns: all checks passed")
