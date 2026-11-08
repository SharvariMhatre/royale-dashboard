"""Merge the team's p*_actions files (columns: action, quantity, targets, cost_usd, expected_benefit_usd, low/high_estimate_usd, ...), recompute costs with the guide formula, and enforce the $100,000 rules.
Usage: python -I src/budget.py            (checks every proposal as one merged plan, prints issues)
Guide cost per line = quantity x (unit_cost_cents + recurring_cost_cents_per_day x max(0, 30 - lead_days)) / 100."""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEAM = ROOT / "app_data" / "team"
CATALOG = ROOT.parent / "dashboard-royale" / "data" / "2_machine_decision" / "action_catalog.parquet"
CATALOG_COPY = ROOT / "app_data" / "min_q6.parquet"  # deployed fallback: same catalogue, already priced
BUDGET, MAX_TYPES, HOLD = 100000, 3, "A-HOLD"
KEYWORDS = [(("whole bank",), "A-MOVE-BANK"), (("relocate", "bank"), "A-MOVE-BANK"), (("move", "bank"), "A-MOVE-BANK"),
            (("move", "machine"), "A-MOVE-MACHINE"), (("relocate", "machine"), "A-MOVE-MACHINE"),
            (("purchas",), "A-REPLACE-BUY"), (("lease",), "A-REPLACE-LEASE"), (("inspect",), "A-INSPECT"),
            (("technician",), "A-TECH-SHIFT"), (("preventive",), "A-PREVENTIVE"), (("wayfinding",), "A-WAYFINDING"),
            (("signage",), "A-WAYFINDING"), (("comp", "pilot"), "A-COMP-PILOT"), (("comp", "change"), "A-COMP-CHANGE"),
            (("promotion",), "A-PROMO"), (("survey",), "A-SURVEY")]


def catalog() -> pd.DataFrame:
    src = CATALOG if CATALOG.exists() else CATALOG_COPY
    c = pd.read_parquet(src)
    if "unit_cost_cents" not in c.columns:  # min_q6 has dollars only: rebuild cents from per-unit cost and operating days
        c["unit_cost_cents"], c["recurring_cost_cents_per_day"] = (c.cost_per_unit_usd * 100).round(), 0
    return c.set_index("action_type_id")


def guide_cost(row, qty) -> float:
    return qty * (row.unit_cost_cents + row.recurring_cost_cents_per_day * max(0, 30 - row.lead_days)) / 100


def resolve(action, cat: pd.DataFrame):
    """The files give `action`: accept the catalogue id (A-INSPECT) or its name; 'preserve/keep/hold' means A-HOLD."""
    a = str(action).strip()
    if a.upper() in cat.index:
        return a.upper()
    low = a.lower()
    for t, n in cat["name"].items():
        if n.lower() == low:
            return t
    if any(w in low for w in ("preserve", "keep the money", "hold")):
        return HOLD
    # free-text wording from the team files; the match is reported in `issues` so a person can confirm it
    for words, t in KEYWORDS:
        if all(w in low for w in words):
            return t
    return None


def load_proposals(team_dir: Path = TEAM, cat: pd.DataFrame | None = None,
                   stems=("p1_actions", "p2_actions", "p3_actions")) -> pd.DataFrame:
    """Action lines (default: the three person files; pass stems=('final_budget_plan',) to check the chosen plan).
    Adds action_type_id, cost_recomputed_usd and issues (semicolon text; empty = fine)."""
    cat = catalog() if cat is None else cat
    parts = []
    for st_ in stems:
        f = team_dir / f"{st_}.parquet"
        if f.exists():
            d = pd.read_parquet(f)
            for c in d.columns:  # Databricks DECIMAL arrives as Decimal objects: use floats so cost arithmetic works
                if d[c].dtype == object and d[c].notna().any() and type(d[c].dropna().iloc[0]).__name__ == "Decimal":
                    d[c] = d[c].astype(float)
            d.insert(0, "source", st_)
            parts.append(d)
    if not parts:
        return pd.DataFrame()
    d = pd.concat(parts, ignore_index=True)
    ids, rec, issues = [], [], []
    for r in d.itertuples():
        t = resolve(r.action, cat)
        ids.append(t)
        if t is None:
            rec.append(float("nan")); issues.append("action not in the catalogue"); continue
        c = cat.loc[t]
        cost = guide_cost(c, r.quantity)
        rec.append(cost)
        f = []
        if str(r.action).strip().upper() != t and str(r.action).strip().lower() != str(c["name"]).lower() and t != HOLD:
            f.append(f"matched by wording to {t}")
        if abs(cost - r.cost_usd) > 1:
            f.append(f"cost mismatch: file ${r.cost_usd:,.0f} vs guide ${cost:,.0f}")
        if r.quantity > c.quantity_limit:
            f.append(f"quantity {r.quantity} above limit {int(c.quantity_limit)}")
        if not (r.low_estimate_usd <= r.expected_benefit_usd <= r.high_estimate_usd):
            f.append("expected benefit is outside its low-high range")
        issues.append("; ".join(f))
    d["action_type_id"], d["cost_recomputed_usd"], d["issues"] = ids, rec, issues
    return d


PERMANENT = {"A-MOVE-MACHINE", "A-MOVE-BANK", "A-INSPECT"}  # one-time cost, benefit can continue after the 30-day window


def payback(lines: pd.DataFrame, months=(3, 6)) -> pd.DataFrame:
    """ASSUMPTION beyond the guide's 30-day window: a permanent action's 30-day benefit repeats every month at the same size
    (no decay, no extra cost). Returns months to pay back and cumulative net benefit after 3 and 6 months (expected / low / high)."""
    p = lines[lines.action_type_id.isin(PERMANENT)].copy()
    cost, e, lo, hi = p.cost_recomputed_usd, p.expected_benefit_usd, p.low_estimate_usd, p.high_estimate_usd
    p["months_to_pay_back"] = (cost / e).where(e > 0)
    for n in months:
        p[f"net_{n}m_expected"], p[f"net_{n}m_low"], p[f"net_{n}m_high"] = e * n - cost, lo * n - cost, hi * n - cost
    return p


def check_plan(plan: pd.DataFrame, cat: pd.DataFrame | None = None) -> list[str]:
    """Rule errors for a chosen plan (rows of load_proposals). Empty list = plan is allowed."""
    cat = catalog() if cat is None else cat
    errs = []
    p = plan[(plan.action_type_id != HOLD) & plan.action_type_id.notna()]
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
    else:
        print(d[["source", "action", "quantity", "cost_usd", "cost_recomputed_usd", "issues"]].to_string())
    fin = load_proposals(stems=("final_budget_plan",))
    if not fin.empty:
        print("final_budget_plan:", "OK" if not check_plan(fin) else "")
        for e in check_plan(fin):
            print("RULE:", e)
        for r in fin.itertuples():
            if r.issues:
                print("FLAG:", r.action, "-", r.issues)
    return 0


if __name__ == "__main__":
    sys.exit(main())
