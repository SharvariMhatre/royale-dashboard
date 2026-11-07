import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import streamlit as st
from common import sidebar, header
import pages

st.set_page_config(page_title="The Gilded Ace - Decision Room", layout="wide")

PAGES = {
    "Overview": ("Decision Room", "Which 10 machines would we replace, and what do we fund with $100,000?", ["min_q1.parquet"]),
    "Machine Details": ("Machine Details", "Why did this machine look weak, and is it really?", ["min_q1.parquet"]),
    "Demand & Downtime": ("Demand & Downtime", "What changed in demand, and how much play did downtime cost?", ["min_q2.parquet", "min_q3.parquet"]),
    "Players & Comps": ("Players & Comps", "What did tracked players and the comp program do?", ["min_q4.parquet", "min_q5.parquet"]),
    "Model Test & $100K Plan": ("Model Test & $100K Plan", "How was the forecast validated, and how is the budget spent?", ["min_model.parquet", "min_q6.parquet"]),
}

BODY = {"Overview": "overview", "Machine Details": "details", "Demand & Downtime": "demand",
        "Players & Comps": "players", "Model Test & $100K Plan": "model_plan"}

def make(key):
    def page():
        title, q, files = PAGES[key]
        header(title, q, sidebar(), files)
        sel = st.session_state["sel"]
        getattr(pages, BODY[key])(sel)
    page.__name__ = key.replace(" ", "_").replace("&", "and").replace("$", "")
    return page

nav = st.navigation([st.Page(make(k), title=k, url_path=make(k).__name__.lower()) for k in PAGES])
nav.run()
