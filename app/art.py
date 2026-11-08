"""Original SVG illustrations for the dashboard (drawn in code: no external images, no third-party art).
Decorative art is aria-hidden; anything that carries meaning also has text next to it."""
from theme import NAVY, TEAL, TEAL_DARK, SEAFOAM, CREAM, VERDICT_COLOR

_A = 'aria-hidden="true" focusable="false"'

# ---------------------------------------------------------------- verdict icons (14px, stroke icons; text label always shown beside them)
_ICON_PATHS = {
    "Inspect": '<circle cx="6" cy="6" r="4"/><path d="M9 9l4 4"/>',                                          # magnifier
    "Bad spot": '<path d="M7 13s-4-4.2-4-7a4 4 0 0 1 8 0c0 2.8-4 7-4 7z"/><circle cx="7" cy="6" r="1.4"/>',   # map pin
    "Short exposure": '<path d="M3 1.5h8M3 12.5h8M4 1.5c0 4 6 4 6 5.5S4 8.5 4 12.5M10 1.5c0 4-6 4-6 5.5s6 1.5 6 5.5"/>',  # hourglass
    "Unlucky": '<rect x="1.5" y="1.5" width="11" height="11" rx="2"/><circle cx="4.5" cy="4.5" r=".9"/><circle cx="9.5" cy="9.5" r=".9"/><circle cx="7" cy="7" r=".9"/>',  # die
    "Healthy": '<path d="M2.5 7.5l3 3 6-7"/>',                                                               # check
    "Broken": '<path d="M9.5 1.5a3 3 0 0 0-3.3 4L1.8 9.9a1.3 1.3 0 0 0 1.9 1.9l4.4-4.4a3 3 0 0 0 4-3.3l-1.8 1.8-1.8-.4-.4-1.8z"/>',  # wrench
    "Truly bad": '<path d="M3 3l8 8M11 3l-8 8"/>',                                                           # cross
}


def verdict_icon(verdict: str, color: str = NAVY) -> str:
    p = _ICON_PATHS.get(verdict, "")
    return (f'<svg {_A} width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="{color}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:4px">{p}</svg>') if p else ""


# ---------------------------------------------------------------- hero illustration: line-art casino floor, Back Forty dimmed
def hero_floor() -> str:
    def slots(x, y, cols, rows, col=SEAFOAM, op=0.9):
        out = []
        for r in range(rows):
            for c in range(cols):
                out.append(f'<rect x="{x + c * 11}" y="{y + r * 13}" width="8" height="10" rx="1.5" fill="{col}" opacity="{op}"/>')
        return "".join(out)
    zones = [  # (label, x, y, w, h, cols, rows, highlight)
        ("Hotel Corridor", 120, 8, 92, 40, 7, 2, False), ("High-Limit", 236, 30, 70, 34, 5, 2, False),
        ("Main Entrance", 14, 70, 82, 44, 6, 2, False), ("Center Pit", 118, 66, 100, 50, 8, 3, False),
        ("Bar Row", 236, 84, 76, 44, 6, 2, False), ("Back Forty", 14, 148, 86, 40, 6, 2, True),
        ("Garage", 248, 150, 70, 38, 5, 2, False)]
    g = []
    for lab, x, y, w, h, c, r, hi in zones:
        stroke = "#E69F00" if hi else TEAL
        fill = "#E69F0022" if hi else "none"
        dash = 'stroke-dasharray="5 4"' if hi else ""
        g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5" {dash}/>')
        g.append(slots(x + 8, y + 10, c, r, "#E69F00" if hi else SEAFOAM, 0.85 if hi else 0.55))
        g.append(f'<text x="{x + w / 2}" y="{y + h + 12}" text-anchor="middle" font-family="Inter, sans-serif" font-size="9" '
                 f'font-weight="{800 if hi else 600}" fill="{"#F5C26B" if hi else SEAFOAM}">{lab}</text>')
    walk = (f'<path d="M57 130 L 57 148" stroke="{CREAM}" stroke-width="2" stroke-dasharray="3 3" fill="none" opacity=".8"/>'
            f'<circle cx="57" cy="139" r="6.5" fill="{NAVY}" stroke="#F5C26B" stroke-width="1.5"/>'
            f'<path d="M54.2 136.2l5.6 5.6M59.8 136.2l-5.6 5.6" stroke="#F5C26B" stroke-width="1.5"/>')
    return (f'<svg class="hero-art" {_A} viewBox="0 0 330 214" width="330" height="214">{"".join(g)}{walk}'
            f'<text x="108" y="210" font-family="Inter, sans-serif" font-size="8.5" fill="{SEAFOAM}" opacity=".85">walkway closed: Back Forty play fell</text></svg>')


# ---------------------------------------------------------------- slot machine illustration for the case file
def slot_machine(verdict: str) -> str:
    vc = VERDICT_COLOR.get(verdict, TEAL)
    sym = {"Inspect": "?", "Bad spot": "&#9873;", "Short exposure": "&#8987;", "Unlucky": "7", "Healthy": "&#10003;"}.get(verdict, "&#9824;")
    reels = "".join(f'<rect x="{14 + i * 18}" y="26" width="15" height="22" rx="2" fill="{CREAM}"/>'
                    f'<text x="{21.5 + i * 18}" y="42" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="{NAVY}">{sym}</text>'
                    for i in range(3))
    return (f'<svg class="slot-art" {_A} viewBox="0 0 82 96" width="82" height="96">'
            f'<rect x="6" y="8" width="62" height="80" rx="8" fill="{NAVY}"/><rect x="6" y="8" width="62" height="12" rx="6" fill="{vc}"/>'
            f'{reels}<rect x="14" y="56" width="46" height="8" rx="2" fill="{TEAL_DARK}"/>'
            f'<rect x="20" y="70" width="34" height="10" rx="3" fill="{SEAFOAM}" opacity=".6"/>'
            f'<path d="M68 30 h6 v22" stroke="{NAVY}" stroke-width="3" fill="none" stroke-linecap="round"/><circle cx="74" cy="26" r="5" fill="{vc}"/></svg>')


# ---------------------------------------------------------------- poker chips for the $100K plan (1 chip = $10,000)
def chip_stacks(spent: float, budget: float = 100000) -> str:
    n = 10
    spent_chips = min(n, round(spent / (budget / n) + 0.4999)) if spent > 0 else 0
    kept = n - spent_chips

    def stack(x, count, fill, label, sub):
        chips = []
        for i in range(count):
            y = 92 - i * 7
            chips.append(f'<ellipse cx="{x}" cy="{y + 3}" rx="26" ry="8" fill="{NAVY}" opacity=".25"/>'
                         f'<ellipse cx="{x}" cy="{y}" rx="26" ry="8" fill="{fill}" stroke="{NAVY}" stroke-width="1.2"/>'
                         f'<ellipse cx="{x}" cy="{y}" rx="17" ry="5" fill="none" stroke="{CREAM}" stroke-width="1.6" stroke-dasharray="4 3"/>')
        if not count:
            chips.append(f'<ellipse cx="{x}" cy="92" rx="26" ry="8" fill="none" stroke="{NAVY}" stroke-dasharray="3 3" opacity=".4"/>')
        return ("".join(chips) + f'<text x="{x}" y="118" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="{NAVY}">{label}</text>'
                f'<text x="{x}" y="132" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#4A5568">{sub}</text>')
    return (f'<svg class="chips-art" {_A} viewBox="0 0 220 140" width="220" height="140">'
            + stack(60, spent_chips, NAVY if spent <= budget else "#B42318", f"${spent:,.0f}", "spent")
            + stack(160, kept, SEAFOAM, f"${max(budget - spent, 0):,.0f}", "kept")
            + "</svg>")
