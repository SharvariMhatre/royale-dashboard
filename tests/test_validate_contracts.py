"""Run: python -I tests/test_validate_contracts.py  (assert-based; exits non-zero on failure)"""
import json, sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from validate_contracts import ACTION_COLS, CLAIM_COLS, check, validate

ver = pd.DataFrame({"machine_id": ["M-1", "M-2"], "bank_id": ["B", "B"], "zone_id": ["Z", "Z"], "x": [1., 2.], "y": [1., 2.],
                    "house_win_usd": [1., 2.], "theo_usd": [1., 2.], "theo_per_hour_usd": [1., 2.], "availability_pct": [99., 98.],
                    "luck_score": [.1, .2], "verdict": ["Unlucky", "Healthy"], "reason": ["a", "b"], "dollar_impact_usd": [1., 2.],
                    "confidence": ["high", "low"], "in_manager_bottom10": [True, False], "extra_col": [1, 2]})
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    def put(name, df):
        (t / (name + ".parquet._meta.json")).unlink(missing_ok=True)
        df.to_parquet(t / (name + ".parquet")); return t / (name + ".parquet")
    e, w = check(put("p2_verdicts", ver)); assert e == [] and any("_meta" in x for x in w), (e, w)   # extra col fine; no sidecar = warning
    assert any("missing column 'verdict'" in x for x in validate(put("p2_verdicts", ver.drop(columns="verdict"))))
    assert any("duplicate" in x for x in validate(put("p2_verdicts", pd.concat([ver, ver]))))
    for v in ("Great", "Mixed / not enough evidence"):   # old verdict names are no longer allowed
        assert any("verdicts must be" in x for x in validate(put("p2_verdicts", ver.assign(verdict=v)))), v
    put("p2_verdicts", ver)
    (t / "p2_verdicts.parquet._meta.json").write_text(json.dumps({"schema_version": "1", "data_release": "r", "generated_at": "x", "producer": "b"}))
    assert check(t / "p2_verdicts.parquet") == ([], [])
    f = pd.DataFrame({"gaming_date": pd.to_datetime(["2025-04-30", "2025-04-29"]), "actual_usd": [1., 1.], "baseline_pred_usd": [1., 1.],
                      "model_pred_usd": [1., 1.], "split": ["train", "test"]})
    assert any("overlap" in x for x in validate(put("p3_forecast_results", f)))
    a = pd.DataFrame([{c: 1 for c in ACTION_COLS}]).assign(action="A-INSPECT", low_estimate_usd=5., high_estimate_usd=1.)
    assert any("low_estimate" in x for x in validate(put("p1_actions", a)))
    assert validate(put("all_actions", a.assign(low_estimate_usd=0.))) == []
    c = pd.DataFrame({k: ["x", "x"] for k in CLAIM_COLS})
    assert any("duplicate" in x for x in validate(put("p1_claims", c)))
    pl = pd.DataFrame({"month": ["2025-01"], "tier": ["Base"], "age_band": ["21-34"], "home_region": ["TX"], "wagered_usd": [1.], "won_back_usd": [1.],
                       "net_usd": [0.], "player_count": [5]})
    assert any("smaller than 10" in x for x in validate(put("p3_players", pl)))
    assert validate(t / "nope.parquet")[0].endswith("file not found")
print("validate_contracts: all checks passed")
