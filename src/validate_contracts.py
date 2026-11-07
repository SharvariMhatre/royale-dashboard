"""Validate a team file against the file contract in TEAM_PLAN.md.
Usage: python -I src/validate_contracts.py app_data/q1_machines.parquet   (no args = every contract file found in app_data/)
Exit code 0 = pass, 1 = fail. A failing file must be treated as 'pending' by the dashboard."""
import json
import re
import sys
from pathlib import Path

import pandas as pd

META_FIELDS = ["schema_version", "data_release", "generated_at", "producer"]
VERDICTS = {"Unlucky", "Bad spot", "Broken", "Inspect", "Truly bad", "Mixed / not enough evidence"}

# file -> (key columns, required columns). Column lists copied from the TEAM_PLAN.md contract table.
# An entry in a list may be a tuple of accepted aliases (the contract names a grain, not an exact column).
C = {
    "machine_day_clean.parquet": (["machine_id", "gaming_date"], [
        "zone_id", "zone_name", "bank_id", "location_id", "config_id", "configured_rtp", "volatility_class", "manufacturer",
        "scheduled_hours", "available_hours", "occupied_hours", "coin_in_usd", "payout_usd", "house_win_usd", "theo_usd",
        "luck_residual_usd", "carded_coin_in_usd", "faults_opened"]),
    "floor_day_clean.parquet": (["gaming_date"], [
        "local_weekday", "is_weekend", "federal_holiday", "events_active", "scheduled_seconds", "coin_in_usd", "house_win_usd",
        "theo_usd", "comp_cost_usd"]),
    "leak_clues.parquet": (["machine_id", "gaming_date", "reason"], ["source_table", "value", "note"]),
    "q1_machines.parquet": (["machine_id", "scope"], [
        "house_win_usd", "theo_usd", "luck_residual_usd", "coin_in_usd", "available_hours", "availability", "theo_per_avail_hour",
        "peer_index", "peer_index_lo", "peer_index_hi", "peer_group_used", "n_peers", "hold_gap", "hold_gap_lo", "hold_gap_hi",
        "luck_sim_share_bottom10", "downtime_hours", "downtime_lost_theo_usd", "moved_flag", "verdict", "verdict_reason",
        "dollar_amount_usd", "source_script"]),
    "forecast.parquet": (["gaming_date"], ["actual_usd", "pred_model_usd", "pred_baseline_usd", "split"]),
    "q2_floor_week.parquet": ([("week", "week_start")], ["coin_in_usd", "theo_usd", "occupied_machine_hours", "entries", "coverage_share"]),
    "q2_zone_month.parquet": (["zone_id", "month"], ["coin_in_usd", "theo_usd", "occupied_machine_hours", "entries", "coverage_share"]),
    "q3_downtime.parquet": (["machine_id", ("week", "week_start")], ["downtime_hours", "lost_theo_usd", "manufacturer", "zone_id"]),
    "q4_player_month.parquet": (["group_type", "group", "month"], ["players", "wagered_usd", "paid_back_usd", "net_usd", "theo_usd"]),
    "q4_concentration.parquet": (["group_type", "group"], ["scope"]),
    "q5_comps_month.parquet": (["month", "tier"], [
        "comp_cost_usd", "comp_face_value_usd", "theo_usd", "comp_cost_to_theo_ratio", "comps_redeemed", "points_earned",
        "points_redeemed"]),
    "budget.parquet": ([], [
        "action_type_id", "name", "quantity", "targets", "lead_days", "operating_days", "cost_usd", "evidence", "estimate_usd",
        "estimate_lo", "estimate_hi", "assumption", "breakeven_improvement", "metric", "measurement_method", "evidence_ref"]),
}
JSON_KEYS = {  # sidecar-free json files and the keys they must contain
    "model_metrics.json": ["mae_model_usd", "mae_baseline_usd", "train", "test", "decision_affected"],
}
CLAIM_COLS = ["claim_id", "claim", "question", "table_or_query", "result", "alternative_explanation", "limitation",
              "source_script", "scope"]


def _first(df, name):
    """Resolve a column name or tuple of aliases to the column present in df (or None)."""
    names = name if isinstance(name, tuple) else (name,)
    return next((n for n in names if n in df.columns), None)


def meta_path(p: Path):
    for c in (p.with_name(p.name + "._meta.json"), p.with_name(p.stem + "._meta.json"), p.with_name(p.stem + "_meta.json")):
        if c.exists():
            return c
    return None


def validate(path) -> list[str]:
    """Return a list of error strings; empty list = valid."""
    p = Path(path)
    if not p.exists():
        return [f"{p.name}: file not found"]
    if p.name in JSON_KEYS:
        try:
            j = json.loads(p.read_text())
        except Exception as e:
            return [f"{p.name}: not valid JSON ({e})"]
        return [f"{p.name}: missing key '{k}'" for k in JSON_KEYS[p.name] if k not in j]
    if p.name == "q2_explanations.json":
        try:
            j = json.loads(p.read_text())
        except Exception as e:
            return [f"{p.name}: not valid JSON ({e})"]
        rows = j if isinstance(j, list) else j.get("explanations", [])
        errs = [] if rows else [f"{p.name}: no explanations"]
        for i, r in enumerate(rows):
            errs += [f"{p.name}: explanation {i} missing '{k}'" for k in ("name", "tested_how", "supported") if k not in r]
            if r.get("supported") not in ("yes", "no", "untested"):
                errs.append(f"{p.name}: explanation {i} 'supported' must be yes/no/untested")
        return errs
    if p.name == "claims.csv":
        try:
            df = pd.read_csv(p)
        except Exception as e:
            return [f"{p.name}: unreadable ({e})"]
        return [f"{p.name}: missing column '{c}'" for c in CLAIM_COLS if c not in df.columns]
    if p.name not in C:
        return [f"{p.name}: not a contract file (known: {', '.join(sorted(list(C) + list(JSON_KEYS)))})"]

    errs = []
    try:
        df = pd.read_parquet(p)
    except Exception as e:
        return [f"{p.name}: unreadable parquet ({type(e).__name__}: {e})"]
    if df.empty:
        return [f"{p.name}: no rows"]
    keys, cols = C[p.name]
    mp = meta_path(p)
    if mp is None:
        errs.append(f"{p.name}: missing _meta sidecar ({p.name}._meta.json)")
    else:
        try:
            meta = json.loads(mp.read_text())
            errs += [f"{mp.name}: missing '{f}'" for f in META_FIELDS if not meta.get(f)]
        except Exception as e:
            errs.append(f"{mp.name}: not valid JSON ({e})")
    resolved_keys = []
    for k in keys + cols:
        if _first(df, k) is None:
            errs.append(f"{p.name}: missing column '{k if isinstance(k, str) else '/'.join(k)}'")
    resolved_keys = [c for c in (_first(df, k) for k in keys) if c]
    if resolved_keys and len(resolved_keys) == len(keys):
        if df[resolved_keys].isna().any().any():
            errs.append(f"{p.name}: null in key columns {resolved_keys}")
        n = int(df.duplicated(resolved_keys).sum())
        if n:
            errs.append(f"{p.name}: {n} duplicate rows for key {resolved_keys}")
    # file-specific sanity rules
    if p.name == "q1_machines.parquet" and "verdict" in df:
        bad = sorted(set(df.verdict.dropna()) - VERDICTS)
        if bad:
            errs.append(f"{p.name}: unknown verdicts {bad}; allowed {sorted(VERDICTS)}")
        if df.verdict.isna().any():
            errs.append(f"{p.name}: verdict is empty for some rows")
    if p.name == "forecast.parquet" and "split" in df and not set(df.split) <= {"train", "test"}:
        errs.append(f"{p.name}: split must be 'train' or 'test'")
    if p.name == "forecast.parquet" and {"split", "gaming_date"} <= set(df.columns):
        d = pd.to_datetime(df.gaming_date)
        if d[df.split == "train"].max() >= d[df.split == "test"].min():
            errs.append(f"{p.name}: train dates overlap test dates (must split by time)")
    if p.name.startswith("q4_player") and "players" in df and (df.players < 10).any():
        errs.append(f"{p.name}: group smaller than 10 players")
    if p.name.startswith("q4_") and any("player_id" in c for c in df.columns):
        errs.append(f"{p.name}: individual player IDs are not allowed")
    if p.name == "q4_concentration.parquet":
        for pat in ("top1", "top10", "top20", "gini"):
            if not any(re.search(pat, c) for c in df.columns):
                errs.append(f"{p.name}: no column matching '{pat}'")
    if p.name == "budget.parquet" and "cost_usd" in df:
        if (df.cost_usd < 0).any():
            errs.append(f"{p.name}: negative cost_usd")
        if "action_type_id" in df and df.loc[df.action_type_id != "A-HOLD", "action_type_id"].nunique() > 3:
            errs.append(f"{p.name}: more than 3 action types")
        if df.cost_usd.sum() > 100000:
            errs.append(f"{p.name}: total cost ${df.cost_usd.sum():,.0f} exceeds $100,000")
        if {"estimate_usd", "estimate_lo", "estimate_hi"} <= set(df.columns):
            e = df.dropna(subset=["estimate_usd", "estimate_lo", "estimate_hi"])
            if ((e.estimate_lo > e.estimate_usd) | (e.estimate_usd > e.estimate_hi)).any():
                errs.append(f"{p.name}: estimate must satisfy lo <= estimate <= hi")
    for c in df.columns:  # cents/dollars mix-up guard
        if c.endswith("_cents"):
            errs.append(f"{p.name}: column '{c}' is in cents; the contract uses dollars (_usd)")
    return errs


def main(argv):
    root = Path(__file__).resolve().parent.parent / "app_data"
    names = [Path(a) for a in argv] or [root / n for n in list(C) + list(JSON_KEYS) + ["q2_explanations.json", "claims.csv"]
                                       if (root / n).exists()]
    if not names:
        print("No contract files found in app_data/ yet.")
        return 0
    bad = 0
    for p in names:
        errs = validate(p)
        print(("PASS " if not errs else "FAIL ") + p.name)
        for e in errs:
            print("   -", e)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
