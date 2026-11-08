"""Export the team's tables from Databricks (workspace.casino) to app_data/team/<table>.parquet.
Credentials come from .env (DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN); they are never printed.
Usage: python -I src/export_from_databricks.py [table ...]     (no args = every table in TABLES)
Needs: pip install -r requirements-export.txt  (kept out of the app's requirements.txt on purpose)"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow.parquet as pq
from databricks import sql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app_data" / "team"
SCHEMA = "workspace.casino"
MAX_ROWS = 2_000_000  # guard: never pull the full 10,000-sim tables (p2_luck_sims is already a 500-per-machine sample)
TABLES = (["p1_downtime", "p1_comps", "p1_leak_clues", "p2_verdicts", "p2_luck_sims", "p2_move_effects", "p3_demand",
           "p3_forecast_results", "p3_model_metrics", "p3_players", "p3_concentration"]
          + [f"{p}_{k}" for k in ("claims", "actions") for p in ("p1", "p2", "p3", "all")]
          + ["final_budget_plan", "p2_zone_index", "p2_b40_closure_effect", "p2_inspection_candidates", "p2_luck_scores",
             "p2_manager_bottom10"])


def main(argv) -> int:
    load_dotenv(ROOT / ".env")
    need = ["DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN"]
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        print("Missing in .env:", ", ".join(missing))  # names only, never values
        return 2
    token = os.environ["DATABRICKS_TOKEN"]
    host = os.environ["DATABRICKS_HOST"].replace("https://", "").replace("http://", "").strip("/")
    wanted = [t for t in (argv or TABLES) if not t.startswith("bronze_")]
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        conn = sql.connect(server_hostname=host, http_path=os.environ["DATABRICKS_HTTP_PATH"], access_token=token)
    except Exception as e:
        print(f"Could not connect: {type(e).__name__}: {str(e).replace(token, '***')[:300]}")
        return 1
    rows = []
    with conn, conn.cursor() as cur:
        cur.execute(f"SHOW TABLES IN {SCHEMA}")
        have = {r[1] for r in cur.fetchall()}  # (database, tableName, isTemporary)
        for t in wanted:
            if t not in have:
                rows.append((t, "-", "missing in workspace.casino, skipped"))
                continue
            try:
                cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{t}")
                n = cur.fetchone()[0]
                if n > MAX_ROWS:
                    rows.append((t, n, f"over {MAX_ROWS:,} rows, skipped"))
                    continue
                cur.execute(f"SELECT * FROM {SCHEMA}.{t}")
                pq.write_table(cur.fetchall_arrow(), OUT / f"{t}.parquet")
                rows.append((t, n, "exported"))
            except Exception as e:
                rows.append((t, "?", f"failed: {type(e).__name__}: {str(e).replace(token, '***')[:150]}"))
    done = {t: n for t, n, note in rows if note == "exported"}
    if done:  # the dashboard shows this time (Central) as the data version; it is not the file's modified date
        (OUT / "_export.json").write_text(json.dumps({
            "exported_at": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"), "timezone": "America/Chicago",
            "source": SCHEMA, "tables": done, "skipped": {t: note for t, n, note in rows if note != "exported"}}, indent=1))
    print(f"{'table':28}{'rows':>10}  note")
    for t, n, note in rows:
        print(f"{t:28}{n:>10,}  {note}" if isinstance(n, int) else f"{t:28}{n:>10}  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
