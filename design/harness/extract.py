"""Baseline/parity extractor. Runs each page body via AppTest.from_string (st.navigation callable pages
cannot be switched in AppTest, confirmed). Usage: python -I design/harness/extract.py OUT.json [skin]"""
import json, re, sys, os
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
PAGES = ["Overview", "Machine Details", "Demand & Downtime", "Players & Comps", "Model Test & $100K Plan", "Evidence"]
SCRIPT = '''
import sys, importlib
sys.path.insert(0, r"%(root)s/app"); sys.path.insert(0, r"%(root)s/src")
import streamlit as st
for _m in ("validate_contracts","budget","theme","art","common","pages"):
    importlib.reload(importlib.import_module(_m))
from common import sidebar, header, footer
import pages, theme
st.set_page_config(layout="wide")
theme.apply()
KEY = %(key)r
BODY = {"Overview":"overview","Machine Details":"details","Demand & Downtime":"demand","Players & Comps":"players","Model Test & $100K Plan":"model_plan","Evidence":"evidence_page"}
sel = sidebar()
getattr(pages, BODY[KEY])(st.session_state["sel"])
'''
TAG = re.compile(r"<[^>]+>")

def txt(x):
    return re.sub(r"\s+", " ", TAG.sub(" ", str(x))).strip()

def snapshot(at):
    out = {"exceptions": [str(e.value) for e in at.exception]}
    out["metrics"] = [[m.label, str(m.value), str(m.delta)] for m in at.metric]
    out["tables"] = [json.loads(t.value.to_json(orient="split")) for t in at.table]
    out["markdown"] = [txt(m.value) for m in at.markdown]
    out["captions"] = [txt(c.value) for c in at.caption]
    out["headers"] = [txt(h.value) for h in at.header] + [txt(h.value) for h in at.subheader]
    out["widgets"] = {"selectbox": [[s.label, s.value] for s in at.selectbox], "radio": [[s.label, s.value] for s in at.radio],
                      "multiselect": [[s.label, list(s.value)] for s in at.multiselect]}
    out["alerts"] = [txt(a.value) for a in list(at.warning) + list(at.error) + list(at.info) + list(at.success)]
    return out

def run(skin=None):
    res = {}
    for key in PAGES:
        at = AppTest.from_string(SCRIPT % {"root": ROOT.as_posix(), "key": key}, default_timeout=180)
        if skin:
            at.query_params["skin"] = skin
        at.run()
        res[key] = snapshot(at)
    return res

if __name__ == "__main__":
    out = Path(sys.argv[1]); skin = sys.argv[2] if len(sys.argv) > 2 else None
    data = run(skin)
    out.write_text(json.dumps(data, indent=1, sort_keys=True, default=str), encoding="utf-8")
    for k, v in data.items():
        print(k, "| exc", len(v["exceptions"]), "| metrics", len(v["metrics"]), "| tables", len(v["tables"]), "| md", len(v["markdown"]))
