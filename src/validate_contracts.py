"""Validate a team file against the file contract in TEAM_PLAN.md (files live in app_data/team/ as parquet).
Usage: python -I src/validate_contracts.py app_data/team/p2_verdicts.parquet  (no args = every contract file found)
Exit code 0 = pass, 1 = fail. Errors make a page show 'pending'; warnings (e.g. no _meta sidecar) only go in the footer."""
import json
import sys
from pathlib import Path

import pandas as pd

META_FIELDS = ["schema_version", "data_release", "generated_at", "producer"]
VERDICTS = {"Inspect", "Short exposure", "Broken", "Truly bad", "Bad spot", "Unlucky", "Healthy"}
CLAIM_COLS = ["claim_id", "question", "claim", "evidence_table", "result", "alternative_tested", "limitation", "confidence"]
ACTION_COLS = ["action", "quantity", "targets", "cost_usd", "expected_benefit_usd", "low_estimate_usd", "high_estimate_usd",
               "confidence", "how_to_measure"]

# stem -> (required columns, unique key or None). Extra columns are fine; a missing required column fails.
REQ = {
    "p1_downtime": (["machine_id", "gaming_date", "bank_id", "zone_id", "manufacturer", "available_hours", "scheduled_hours",
                     "availability_pct", "lost_theo_usd", "cause"], None),
    "p1_comps": (["month", "comp_cost_usd", "points_earned", "points_redeemed", "tier"], None),
    "p1_leak_clues": (["machine_id", "gaming_date", "rule_failed", "details"], None),
    "p2_verdicts": (["machine_id", "bank_id", "zone_id", "x", "y", "house_win_usd", "theo_usd", "theo_per_hour_usd",
                     "availability_pct", "luck_score", "verdict", "reason", "dollar_impact_usd", "confidence",
                     "in_manager_bottom10"], ["machine_id"]),
    "p2_luck_sims": (["machine_id", "sim_house_win_usd"], None),
    "p2_move_effects": (["machine_id", "from_location", "to_location", "theo_per_hour_before", "theo_per_hour_after",
                         "change_pct"], None),
    "p3_demand": (["gaming_date", "zone_id", "coin_in_usd", "traffic_count", "event_name"], None),
    "p3_forecast_results": (["gaming_date", "actual_usd", "baseline_pred_usd", "model_pred_usd", "split"], ["gaming_date"]),
    "p3_model_metrics": (["model_name", "mae_usd", "mlflow_run_id"], None),
    "p3_players": (["month", "tier", "age_band", "home_region", "wagered_usd", "won_back_usd", "net_usd", "player_count"], None),
    "p3_concentration": (["top_pct", "share_of_net_loss"], None),
    "final_budget_plan": (ACTION_COLS, None),
    # optional extras from Bharath: non-empty is the only check
    "p2_zone_index": ([], None), "p2_b40_closure_effect": ([], None), "p2_inspection_candidates": ([], None),
    "p2_luck_scores": ([], None), "p2_manager_bottom10": ([], None),
}
for _p in ("p1", "p2", "p3", "all"):
    REQ[f"{_p}_actions"] = (ACTION_COLS, None)
    REQ[f"{_p}_claims"] = (CLAIM_COLS, ["claim_id"])
CONTRACT_STEMS = set(REQ)
TEAM_DIR = Path(__file__).resolve().parent.parent / "app_data" / "team"


def meta_path(p: Path):
    for c in (p.with_name(p.name + "._meta.json"), p.with_name(p.stem + "._meta.json"), p.with_name(p.stem + "_meta.json")):
        if c.exists():
            return c
    return None


def check(path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). No errors = valid."""
    p = Path(path)
    errs, warns = [], []
    if not p.exists():
        return [f"{p.name}: file not found"], warns
    if p.name == "claims.csv":
        try:
            df = pd.read_csv(p)
        except Exception as e:
            return [f"{p.name}: unreadable ({e})"], warns
        return [f"{p.name}: missing column '{c}'" for c in CLAIM_COLS + ["source_script"] if c not in df.columns], warns
    if p.stem not in REQ:
        return [f"{p.name}: not a contract file (known: {', '.join(sorted(REQ))})"], warns
    try:
        df = pd.read_parquet(p)
    except Exception as e:
        return [f"{p.name}: unreadable parquet ({type(e).__name__}: {e})"], warns
    if df.empty:
        return [f"{p.name}: no rows"], warns
    req, key = REQ[p.stem]
    errs += [f"{p.name}: missing column '{c}'" for c in req if c not in df.columns]
    if key and not errs:
        k = key + (["scope"] if p.stem == "p2_verdicts" and "scope" in df.columns else [])
        if df[k].isna().any().any():
            errs.append(f"{p.name}: null in key columns {k}")
        n = int(df.duplicated(k).sum())
        if n:
            errs.append(f"{p.name}: {n} duplicate rows for key {k}")
    errs += [f"{p.name}: column '{c}' is in cents; use dollars (_usd)" for c in df.columns if c.endswith("_cents")]
    if p.stem == "p2_verdicts" and not errs:
        bad = sorted(set(df.verdict.dropna()) - VERDICTS)
        if bad or df.verdict.isna().any():
            errs.append(f"{p.name}: verdicts must be one of {sorted(VERDICTS)}; got {bad or 'empty values'}")
    if p.stem == "p3_forecast_results" and not errs:
        if not set(df.split) <= {"train", "test"}:
            errs.append(f"{p.name}: split must be 'train' or 'test'")
        elif {"train", "test"} <= set(df.split):
            d = pd.to_datetime(df.gaming_date)
            if d[df.split == "train"].max() >= d[df.split == "test"].min():
                errs.append(f"{p.name}: train dates overlap test dates (must split by time)")
    if p.stem == "p3_players" and not errs:
        if any("player_id" in c for c in df.columns):
            errs.append(f"{p.name}: individual player IDs are not allowed")
        if (df.player_count < 10).any():
            errs.append(f"{p.name}: group smaller than 10 players")
    if p.stem in ("final_budget_plan",) or p.stem.endswith("_actions"):
        if not errs:
            if (df.cost_usd < 0).any():
                errs.append(f"{p.name}: negative cost_usd")
            if (df.quantity <= 0).any():
                errs.append(f"{p.name}: quantity must be positive")
            if (df.low_estimate_usd > df.high_estimate_usd).any():
                errs.append(f"{p.name}: low_estimate_usd must be <= high_estimate_usd")
    mp = meta_path(p)
    if mp is None:
        warns.append(f"{p.name}: no _meta sidecar (version unknown)")
    else:
        try:
            meta = json.loads(mp.read_text())
            warns += [f"{mp.name}: missing '{f}'" for f in META_FIELDS if not meta.get(f)]
        except Exception:
            warns.append(f"{mp.name}: not valid JSON")
    return errs, warns


def validate(path) -> list[str]:
    return check(path)[0]


def main(argv):
    names = [Path(a) for a in argv] or sorted(f for f in TEAM_DIR.glob("*.parquet") if f.stem in REQ)
    if not names:
        print("No team files in app_data/team/ yet.")
        return 0
    bad = 0
    for p in names:
        errs, warns = check(p)
        print(("PASS " if not errs else "FAIL ") + p.name)
        for e in errs:
            print("   - ERROR", e)
        for w in warns:
            print("   - warning", w)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
