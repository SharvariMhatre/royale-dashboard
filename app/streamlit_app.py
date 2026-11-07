import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import importlib
import streamlit as st

# Reload our own modules on every run: a long-lived server process can otherwise keep stale versions after a deploy.
for _m in ("validate_contracts", "budget", "common", "pages"):
    importlib.reload(importlib.import_module(_m))
from common import sidebar, header, footer  # noqa: E402
import pages  # noqa: E402

st.set_page_config(page_title="The Gilded Ace - Decision Room", layout="wide")

PAGES = {
    "Overview": ("Decision Room", "Which 10 machines would we replace, and what do we fund with $100,000?", ["team/p2_verdicts.parquet", "min_q1.parquet"]),
    "Machine Details": ("Machine Details", "Why did this machine look weak, and is it really?", ["team/p2_verdicts.parquet"]),
    "Demand & Downtime": ("Demand & Downtime", "What changed in demand, and how much play did downtime cost?", ["team/p3_demand.parquet", "team/p1_downtime.parquet"]),
    "Players & Comps": ("Players & Comps", "What did tracked players and the comp program do?", ["team/p3_players.parquet", "team/p1_comps.parquet"]),
    "Model Test & $100K Plan": ("Model Test & $100K Plan", "How was the forecast validated, and how is the budget spent?", ["team/p3_forecast_results.parquet", "team/p3_model_metrics.parquet"]),
    "Evidence": ("Evidence", "Every claim, the alternative explanation tested, and its limitation.", ["team/all_claims.parquet"]),
}
BODY = {"Overview": "overview", "Machine Details": "details", "Demand & Downtime": "demand", "Players & Comps": "players",
        "Model Test & $100K Plan": "model_plan", "Evidence": "evidence_page"}

def make(key):
    def page():
        title, q, files = PAGES[key]
        header(title, q, sidebar(), files)
        sel = st.session_state["sel"]
        getattr(pages, BODY[key])(sel)
        footer(files)
    page.__name__ = key.replace(" ", "_").replace("&", "and").replace("$", "")
    return page

fns = {k: make(k) for k in PAGES}
page_objs = {k: st.Page(fns[k], title=k, url_path=fns[k].__name__.lower()) for k in PAGES}
pages.PAGE_OBJ.update(page_objs)  # lets the budget builder link to evidence pages
nav = st.navigation(list(page_objs.values()))
nav.run()
