"""Run: python -I tests/test_validate_contracts.py  (assert-based; exits non-zero on failure)"""
import json, sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from validate_contracts import validate

META = {"schema_version": "1", "data_release": "0.9.0-draft", "generated_at": "x", "producer": "t"}
q5 = pd.DataFrame({"month": ["2025-01", "2025-02"], "tier": ["Base", "Base"], "comp_cost_usd": [1.0, 2.0], "comp_face_value_usd": [2.0, 3.0],
                   "theo_usd": [10.0, 20.0], "comp_cost_to_theo_ratio": [.1, .1], "comps_redeemed": [1, 2], "points_earned": [1, 2], "points_redeemed": [1, 2]})
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    def put(name, df, meta=True):
        df.to_parquet(t / name)
        (t / (name + "._meta.json")).unlink(missing_ok=True)
        if meta: (t / (name + "._meta.json")).write_text(json.dumps(META))
        return t / name
    assert validate(put("q5_comps_month.parquet", q5)) == []
    assert any("missing column 'tier'" in e for e in validate(put("q5_comps_month.parquet", q5.drop(columns="tier"))))
    assert any("duplicate" in e for e in validate(put("q5_comps_month.parquet", pd.concat([q5, q5]))))
    assert any("_meta" in e for e in validate(put("q5_comps_month.parquet", q5, meta=False)))
    f = pd.DataFrame({"gaming_date": pd.to_datetime(["2025-04-30", "2025-04-29"]), "actual_usd": [1., 1.], "pred_model_usd": [1., 1.],
                      "pred_baseline_usd": [1., 1.], "split": ["train", "test"]})
    assert any("overlap" in e for e in validate(put("forecast.parquet", f)))
    assert validate(t / "nope.parquet")[0].endswith("file not found")
print("validate_contracts: all checks passed")
