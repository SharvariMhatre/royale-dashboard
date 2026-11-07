"""WCAG 2.1 contrast checks for the Ocean Depths tokens. Run: python -I tests/test_theme.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import theme as T

def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def blend(fg, bg, a):  # fg at opacity a over bg
    f = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * a + y * (1 - a)):02X}" for x, y in zip(f, b))

text_pairs = {  # normal-size text: >= 4.5
    "body on cream": (T.TEXT, T.CREAM), "body on card": (T.TEXT, T.SURFACE), "muted on cream": (T.MUTED, T.CREAM),
    "muted on card": (T.MUTED, T.SURFACE), "link (dark teal) on cream": (T.TEAL_DARK, T.CREAM), "link on card": (T.TEAL_DARK, T.SURFACE),
    "sidebar cream on navy": (T.CREAM, T.NAVY), "sidebar cream on raised navy": (T.CREAM, T.NAVY_RAISED),
    "navy on seafoam (answer, table header)": (T.NAVY, T.SEAFOAM), "navy on note panel": (T.NAVY, blend(T.SEAFOAM, T.CREAM, 0.2)),
}
text_pairs.update({f"chip {k}": (fg, bg) for k, (bg, fg) in T.CHIPS.items()})
bad = {k: round(ratio(*v), 2) for k, v in text_pairs.items() if ratio(*v) < 4.5}
assert not bad, f"text contrast below 4.5:1: {bad}"
assert ratio(T.TEAL, T.CREAM) >= 3.0, "teal must pass 3:1 for large text on cream"
assert ratio(T.TEAL, T.NAVY) >= 3.0, "active-nav marker (teal on navy) must pass 3:1"
assert ratio(T.TEAL, T.CREAM) < 4.5, "teal is documented as large-text only; if this fails the note in theme.py is out of date"
# graphics (lines/bars) need 3:1 against cream; Okabe-Ito orange is the known exception (mitigated by dashes, legend text, tooltips, tables)
g = {c: round(ratio(c, T.CREAM), 2) for c in T.OKABE_ITO + [T.NAVY, T.TEAL]}
low = {c: r for c, r in g.items() if r < 3.0}
assert set(low) <= {"#E69F00", "#56B4E9"}, f"unexpected low-contrast chart colours: {low}"
print("theme: text contrast OK; chart colours below 3:1 (known, mitigated):", low)
