"""Parity compare: python -I design/harness/compare.py BASELINE.json OTHER.json
Exit 0 only if every page's metrics, tables, headers, captions, widgets, alerts and markdown are identical.
The injected <style> block shows up in AppTest as a markdown entry (tag-stripped CSS); it is the one thing a skin may change, so it is skipped."""
import json, sys


def strip_css(md):
    return [m for m in md if not m.startswith("@import url(")]


def diff(a, b):
    out = []
    for page in sorted(set(a) | set(b)):
        if page not in a or page not in b:
            out.append(f"{page}: page missing"); continue
        for k in sorted(set(a[page]) | set(b[page])):
            x, y = a[page].get(k), b[page].get(k)
            if k == "markdown":
                x, y = strip_css(x), strip_css(y)
            if x != y:
                out.append(f"{page}.{k}: differs")
    return out


if __name__ == "__main__":
    d = diff(json.load(open(sys.argv[1], encoding="utf-8")), json.load(open(sys.argv[2], encoding="utf-8")))
    print("PARITY OK" if not d else "PARITY FAIL:\n" + "\n".join(d))
    sys.exit(1 if d else 0)
