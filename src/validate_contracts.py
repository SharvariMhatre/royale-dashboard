"""Validate a team file against the file contract in TEAM_PLAN.md (files live in app_data/team/ as parquet).
Usage: python -I src/validate_contracts.py app_data/team/p2_verdicts.parquet  (no args = every contract file found)
Exit code 0 = pass, 1 = fail. Errors make a page show 'pending'; warnings (e.g. no _meta sidecar) only go in the footer."""
import json
import sys
from pathlib import Path

import pandas as pd

META_FIELDS = ["schema_version", "data_release", "generated_at", "producer"]
VERDICTS = {"Unlucky", "Bad spot", "Broken", "Inspect", "Truly bad", "Mixed / not enough evidence"}
ACTION_COLS = ["action_type_id", "name", "quantity", "targets", "lead_days", "operating_days", "cost_usd", "estimate_lo_usd",
               "estimate_hi_usd", "assumption", "metric", "measurement_method", "evidence_ref"]
CLAIM_COLS = ["claim_id", "claim", "question", "table_or_query", "result", "alternative_explanation", "limitation", "source_script"]

# stem -> (required columns, unique key or None). Only the columns we were given are required; the rest are
# recorded from the 20-row samples in app_data/team/samples/ when they arrive.
REQ = {
    "p1_machine_day_clean": (["machine_id", "gaming_date"], ["machine_id", "gaming_date"]),
    "p1_downtime": ([], None), "p1_comps": ([], None),
    "p1_leak_clues": (["machine_id", "gaming_date", "reason"], None),
    "p2_verdicts": (["machine_id", "zone_id", "config_id", "verdict", "verdict_reason", "dollar_impact_usd", "luck_score",
                     "peer_index", "peer_index_lo", "peer_index_hi", "availability", "moved_flag"], ["machine_id"]),
    "p2_luck_sims": ([], None), "p2_move_effects": ([], None),
    "p3_forecast_results": (["gaming_date", "actual_usd", "pred_model_usd", "pred_baseline_usd", "split"], ["gaming_date"]),
    "p3_model_metrics": ([], None), "p3_demand": ([], None), "p3_players": ([], None), "p3_concentration": ([], None),
}
for _p in ("p1", "p2", "p3"):
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
        return [f"{p.name}: missing column '{c}'" for c in CLAIM_COLS + ["scope"] if c not in df.columns], warns
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
        w = df.dropna(subset=["peer_index", "peer_index_lo", "peer_index_hi"])
        if ((w.peer_index_lo > w.peer_index) | (w.peer_index > w.peer_index_hi)).any():
            errs.append(f"{p.name}: peer_index must lie within [peer_index_lo, peer_index_hi]")
    if p.stem == "p3_forecast_results" and not errs:
        if not set(df.split) <= {"train", "test"}:
            errs.append(f"{p.name}: split must be 'train' or 'test'")
        elif {"train", "test"} <= set(df.split):
            d = pd.to_datetime(df.gaming_date)
            if d[df.split == "train"].max() >= d[df.split == "test"].min():
                errs.append(f"{p.name}: train dates overlap test dates (must split by time)")
    if p.stem in ("p3_players", "p3_concentration"):
        if any("player_id" in c for c in df.columns):
            errs.append(f"{p.name}: individual player IDs are not allowed")
        if "players" in df.columns and (df.players < 10).any():
            errs.append(f"{p.name}: group smaller than 10 players")
    if p.stem.endswith("_actions") and not errs:
        if (df.cost_usd < 0).any():
            errs.append(f"{p.name}: negative cost_usd")
        if (df.quantity <= 0).any():
            errs.append(f"{p.name}: quantity must be positive")
        if (df.estimate_lo_usd > df.estimate_hi_usd).any():
            errs.append(f"{p.name}: estimate_lo_usd must be <= estimate_hi_usd")
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
    names = [Path(a) for a in argv] or sorted(TEAM_DIR.glob("p[123]_*.parquet"))
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
