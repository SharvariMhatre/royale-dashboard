"""Run the whole v2 pipeline, publish results for the site, then verify.  python build.py"""
from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path

from common import OUT, RESULTS, dump

HERE = Path(__file__).parent
STEPS = ["export_data", "q1_machines", "q2_q3_demand_downtime", "model", "q4_q5_guests", "plan", "claims"]

for s in STEPS:
    print(f"== {s}")
    runpy.run_path(str(HERE / f"{s}.py"), run_name="__main__")

bundle = {p.stem: json.loads(p.read_text()) for p in sorted(RESULTS.glob("*.json"))}
(OUT / "results.json").write_text(dump(bundle, separators=(",", ":")))
print("== verify")
sys.exit(subprocess.call([sys.executable, str(HERE / "verify.py")], cwd=HERE))
