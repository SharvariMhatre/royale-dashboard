"""Per-skin checks. Run: python -I tests/test_skins.py
1. every skin defines every token the loader copies, with the right shapes;
2. text/link/chip contrast >= 4.5:1 on the skin's own surfaces (default and all three skins);
3. AppTest parity: every page's numbers, tables, headers, captions and widgets equal design/baseline/numbers.json (only the CSS differs);
4. the four judge paths still work under each skin: change the period, drill into a bank, find the model validation, find an evidence expander."""
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "design" / "harness"))
import theme  # noqa: E402  (imports the default skin outside Streamlit)
import extract  # noqa: E402  (design/harness: AppTest page runner)
import compare  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

SKINS = ["default", "noir", "control", "paper"]
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check_tokens(name):
    s = importlib.reload(importlib.import_module(f"skins.{name}"))
    missing = [t for t in theme._TOKENS if not hasattr(s, t)]
    assert not missing, f"{name}: missing tokens {missing}"
    assert len(s.CHIPS) == 7 and len(s.VERDICT_COLOR) == 7, f"{name}: CHIPS/VERDICT_COLOR need all 7 verdicts"
    assert len(s.OKABE_ITO) == 6 and all(HEX.match(c) for c in s.OKABE_ITO), f"{name}: OKABE_ITO"
    assert set(s.CHIPS) == set(theme.VERDICT_SHAPE) == set(s.VERDICT_COLOR), f"{name}: verdict keys differ from VERDICT_SHAPE"
    assert "prefers-reduced-motion" in s.CSS or "animation" not in s.CSS, f"{name}: animation without a reduced-motion override"
    pairs = {"text on page": (s.TEXT, s.CREAM), "text on card": (s.TEXT, s.SURFACE), "muted on page": (s.MUTED, s.CREAM),
             "muted on card": (s.MUTED, s.SURFACE), "link on page": (s.TEAL_DARK, s.CREAM), "link on card": (s.TEAL_DARK, s.SURFACE)}
    pairs.update({f"chip {k}": (fg, bg) for k, (bg, fg) in s.CHIPS.items()})
    bad = {k: round(ratio(*v), 2) for k, v in pairs.items() if ratio(*v) < 4.5}
    assert not bad, f"{name}: text contrast below 4.5:1: {bad}"


def run_page(skin, key, edits=None):
    at = AppTest.from_string(extract.SCRIPT % {"root": ROOT.as_posix(), "key": key}, default_timeout=180)
    at.query_params["skin"] = skin
    at.run()
    for fn in edits or []:
        fn(at)
        at.run()
    return at


def check_judge_paths(skin):
    base = run_page(skin, "Overview")
    assert not base.exception, f"{skin}: Overview raised {base.exception}"
    period = base.selectbox[0]
    other = next(o for o in period.options if o not in (period.value, "Custom range"))
    full = run_page(skin, "Players & Comps")  # Wagered follows the window (the Overview KPIs use full-period verdicts)
    after = run_page(skin, "Players & Comps", [lambda a: a.selectbox[0].select(other)])
    assert not after.exception and after.selectbox[0].value == other, f"{skin}: period change failed"
    assert [m.value for m in after.metric] != [m.value for m in full.metric], f"{skin}: period change did not move any KPI"
    bank = run_page(skin, "Overview", [lambda a: a.selectbox[1].select(a.selectbox[1].options[1])])
    assert not bank.exception and bank.selectbox[1].value == base.selectbox[1].options[1], f"{skin}: bank drill-down failed"
    tier = run_page(skin, "Overview", [lambda a: a.radio[0].set_value(a.radio[0].options[1])])
    assert not tier.exception, f"{skin}: guest-group drill-down raised"
    model = run_page(skin, "Model Test & $100K Plan")
    vals = {m.label: m.value for m in model.metric}
    assert vals.get("Model average miss per day") == "$50,920" and vals.get("Constant baseline miss per day") == "$218,258", f"{skin}: model validation KPIs {vals}"
    assert any(e.label.startswith("Evidence:") for e in model.expander), f"{skin}: no evidence expander on the model page"


if __name__ == "__main__":
    base = json.loads((ROOT / "design" / "baseline" / "numbers.json").read_text(encoding="utf-8"))
    for s in SKINS:
        check_tokens(s)
        d = compare.diff(base, extract.run(s))
        assert not d, f"{s}: page content differs from the baseline: {d}"
        check_judge_paths(s)
        print(f"{s}: tokens, contrast, parity and judge paths OK")
