"""Merge the team's p*_actions files, recompute costs with the guide formula, and enforce the $100,000 rules.
Usage: python -I src/budget.py            (checks every proposal as one merged plan, prints flags)
Guide cost per line = quantity x (unit_cost_cents + recurring_cost_cents_per_day x max(0, 30 - lead_days)) / 100."""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEAM = ROOT / "app_data" / "team"
CATALOG = ROOT.parent / "dashboard-royale" / "data" / "2_machine_decision" / "action_catalog.parquet"
CATALOG_COPY = ROOT / "app_data" / "min_q6.parquet"  # deployed fallback: same catalogue, already priced
BUDGET, MAX_TYPES, HOLD = 100000, 3, "A-HOLD"


def catalog() -> pd.DataFrame:
    src = CATALOG if CATALOG.exists() else CATALOG_COPY
    c = duckdb.sql(f"SELECT * FROM '{src}'").df()
    if "unit_cost_cents" not in c.columns:  # min_q6 has dollars only: rebuild cents from per-unit cost and operating days
        c["unit_cost_cents"], c["recurring_cost_cents_per_day"] = (c.cost_per_unit_usd * 100).round(), 0
    return c.set_index("action_type_id")


def guide_cost(row, qty) -> float:
    return qty * (row.unit_cost_cents + row.recurring_cost_cents_per_day * max(0, 30 - row.lead_days)) / 100


def load_proposals(team_dir: Path = TEAM, cat: pd.DataFrame | None = None) -> pd.DataFrame:
    """All p*_actions lines with: source, cost_recomputed_usd, flags (semicolon text; empty = fine)."""
    cat = catalog() if cat is None else cat
    parts = []
    for f in sorted(team_dir.glob("p[123]_actions.parquet")):
        d = pd.read_parquet(f)
        d.insert(0, "source", f.stem[:2])
        parts.append(d)
    if not parts:
        return pd.DataFrame()
    d = pd.concat(parts, ignore_index=True)
    rec, flags = [], []
    for r in d.itertuples():
        f = []
        if r.action_type_id not in cat.index:
            rec.append(float("nan")); flags.append("unknown action_type_id"); continue
        c = cat.loc[r.action_type_id]
        cost = guide_cost(c, r.quantity)
        rec.append(cost)
        if abs(cost - r.cost_usd) > 1:
            f.append(f"cost mismatch: file ${r.cost_usd:,.0f} vs guide ${cost:,.0f}")
        if int(r.lead_days) != int(c.lead_days):
            f.append(f"lead_days {r.lead_days} vs catalogue {int(c.lead_days)}")
        if r.quantity > c.quantity_limit:
            f.append(f"quantity {r.quantity} above limit {int(c.quantity_limit)}")
        flags.append("; ".join(f))
    d["cost_recomputed_usd"], d["flags"] = rec, flags
    return d


def check_plan(plan: pd.DataFrame, cat: pd.DataFrame | None = None) -> list[str]:
    """Rule errors for a chosen plan (rows of load_proposals). Empty list = plan is allowed."""
    cat = catalog() if cat is None else cat
    errs = []
    p = plan[plan.action_type_id != HOLD]
    types = set(p.action_type_id)
    if len(types) > MAX_TYPES:
        errs.append(f"{len(types)} action types chosen; the limit is {MAX_TYPES}")
    total = float(p.cost_recomputed_usd.sum()) if "cost_recomputed_usd" in p else float(p.cost_usd.sum())
    if total > BUDGET:
        errs.append(f"total ${total:,.0f} exceeds ${BUDGET:,}")
    for t, g in p.groupby("action_type_id"):
        if t in cat.index and g.quantity.sum() > cat.loc[t].quantity_limit:
            errs.append(f"{t}: total quantity {int(g.quantity.sum())} above limit {int(cat.loc[t].quantity_limit)}")
    groups = {t: cat.loc[t].incompatibility_group for t in types if t in cat.index and isinstance(cat.loc[t].incompatibility_group, str)}
    if len({t for t, g in groups.items() if g == "comp_policy"}) > 1:
        errs.append("comp pilot and floor-wide comp change cannot both be chosen")
    seen = {}  # machine -> row index of the move/replacement that targets it
    for i, r in zip(p.index, p.itertuples()):
        if groups.get(r.action_type_id) != "same_machine":
            continue
        for m in re.findall(r"M-\d+", str(r.targets)):
            if seen.setdefault(m, i) != i:
                errs.append(f"machine {m} is targeted by more than one move/replacement")
    return sorted(set(errs))


def main() -> int:
    d = load_proposals()
    if d.empty:
        print("No p*_actions files in app_data/team/ yet.")
        return 0
    print(d[["source", "action_type_id", "name", "quantity", "cost_usd", "cost_recomputed_usd", "flags"]].to_string())
    for e in check_plan(d):
        print("RULE:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
