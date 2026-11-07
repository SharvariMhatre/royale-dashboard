"""Run: python -I tests/test_validate_contracts.py  (assert-based; exits non-zero on failure)"""
import json, sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from validate_contracts import check, validate

ver = pd.DataFrame({"machine_id": ["M-1", "M-2"], "zone_id": ["Z", "Z"], "config_id": ["G", "G"], "verdict": ["Unlucky", "Mixed / not enough evidence"],
                    "verdict_reason": ["a", "b"], "dollar_impact_usd": [1., 2.], "luck_score": [.1, .2], "peer_index": [1., 1.],
                    "peer_index_lo": [.9, .9], "peer_index_hi": [1.1, 1.1], "availability": [.99, .99], "moved_flag": [False, False]})
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    def put(name, df):
        (t / (name + ".parquet._meta.json")).unlink(missing_ok=True)
        df.to_parquet(t / (name + ".parquet")); return t / (name + ".parquet")
    e, w = check(put("p2_verdicts", ver)); assert e == [] and any("_meta" in x for x in w), (e, w)   # sidecar missing = warning only
    assert any("missing column 'verdict'" in x for x in validate(put("p2_verdicts", ver.drop(columns="verdict"))))
    assert any("duplicate" in x for x in validate(put("p2_verdicts", pd.concat([ver, ver]))))
    assert any("verdicts must be" in x for x in validate(put("p2_verdicts", ver.assign(verdict="Great"))))
    assert any("peer_index must lie" in x for x in validate(put("p2_verdicts", ver.assign(peer_index_lo=2.0))))
    put("p2_verdicts", ver)
    (t / "p2_verdicts.parquet._meta.json").write_text(json.dumps({"schema_version": "1", "data_release": "r", "generated_at": "x", "producer": "b"}))
    assert check(t / "p2_verdicts.parquet") == ([], [])
    f = pd.DataFrame({"gaming_date": pd.to_datetime(["2025-04-30", "2025-04-29"]), "actual_usd": [1., 1.], "pred_model_usd": [1., 1.],
                      "pred_baseline_usd": [1., 1.], "split": ["train", "test"]})
    assert any("overlap" in x for x in validate(put("p3_forecast_results", f)))
    a = pd.DataFrame({"action_type_id": ["A-INSPECT"], "name": ["x"], "quantity": [1], "targets": ["M-1"], "lead_days": [1], "operating_days": [29],
                      "cost_usd": [1200.], "estimate_lo_usd": [5.], "estimate_hi_usd": [1.], "assumption": ["a"], "metric": ["m"],
                      "measurement_method": ["m"], "evidence_ref": ["e"]})
    assert any("estimate_lo" in x for x in validate(put("p1_actions", a)))
    assert validate(t / "nope.parquet")[0].endswith("file not found")
print("validate_contracts: all checks passed")
