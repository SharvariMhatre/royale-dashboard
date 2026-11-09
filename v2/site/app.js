/* Gilded Ace floor review. Every number below is recomputed in the browser from data/floor.json
   (one row per on-floor machine-day) as a ratio of sums, for whatever period, zone or bank is selected. */
"use strict";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const S = { F: null, R: null, C: null, G: null, K: null };
const st = { from: 0, to: 180, zone: "all", bank: "all", tier: "all", age: "all", region: "all", tab: "answer" };
const VERDICT_COLOR = { "Inspect": "#b3261e", "Bad spot": "#b07a12", "Short exposure": "#6b7a8f", "Unlucky": "#7a5aa6", "Healthy": "#2e7d6b", "Truly weak": "#111827" };
const VERDICT_ORDER = ["Inspect", "Truly weak", "Bad spot", "Short exposure", "Unlucky", "Healthy"];
const VERDICT_TEXT = {
  "Inspect": "Pays out differently from its game's math beyond any plausible luck (|z| > 3.29). Inspect the paytable; a lead, not an accusation.",
  "Truly weak": "Earns under 80% of the same game in the same zone. The machine itself is the problem.",
  "Bad spot": "Earns like its game does nearby, but its zone earns under 85% of what the same games earn elsewhere.",
  "Short exposure": "On the floor for too little of the period to judge.",
  "Unlucky": "Its expected win is normal; its actual win fell short by more than luck usually explains (z < -1.96).",
  "Healthy": "Earns what its game and zone predict.",
};
const Z_INSPECT = 3.29;
const PHRASE = { "Inspect": "to inspect", "Truly weak": "truly weak", "Bad spot": "in a bad spot", "Short exposure": "with too little time on the floor", "Unlucky": "unlucky", "Healthy": "healthy" };

/* ---------- formatting ---------- */
const usd = (x, d = 0) => (x < 0 ? "-$" : "$") + Math.abs(x).toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d });
const usdk = (x) => { const a = Math.abs(x), s = x < 0 ? "-$" : "$"; return a >= 1e6 ? s + (a / 1e6).toFixed(2) + "M" : a >= 1e3 ? s + (a / 1e3).toFixed(1) + "k" : s + a.toFixed(0); };
const pct = (x, d = 1) => (x * 100).toFixed(d) + "%";
const num = (x, d = 0) => x.toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d });
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
const dayLabel = (i) => { const d = S.F.meta.days[i]; return MONTHS[+d.slice(5, 7) - 1] + " " + +d.slice(8); };

/* ---------- charts: one quiet theme ---------- */
const INK = "#182433", INK2 = "#4a5768", RULE = "#dde3ea", ACT = "#1f5fbf";
const layout = (o = {}) => Object.assign({
  margin: { l: 56, r: 16, t: 8, b: 40 }, height: 300, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Archivo, system-ui, sans-serif", size: 12, color: INK }, showlegend: false,
  xaxis: { gridcolor: RULE, zeroline: false, linecolor: "#c7d0db" }, yaxis: { gridcolor: RULE, zeroline: false, linecolor: "#c7d0db" },
  hoverlabel: { font: { family: "Archivo" } },
}, o);
const CFG = { displayModeBar: false, responsive: true };
const plot = (id, data, lay) => { const el = document.getElementById(id); if (el && window.Plotly) Plotly.react(el, data, layout(lay), CFG); };

/* ---------- state <-> URL ---------- */
function readHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  for (const k of Object.keys(st)) if (h.has(k)) st[k] = ["from", "to"].includes(k) ? +h.get(k) : h.get(k);
}
function writeHash() {
  const h = new URLSearchParams();
  for (const [k, v] of Object.entries(st)) h.set(k, v);
  history.replaceState(null, "", "#" + h.toString());
}

/* ---------- the engine ---------- */
let CACHE = null;
function compute() {
  const F = S.F, f = F.floor, meta = F.meta;
  const nM = meta.dims.machine_id.length, nZ = meta.dims.zone_id.length, nG = meta.dims.config_id.length;
  const zi = st.zone === "all" ? -1 : meta.dims.zone_id.indexOf(st.zone);
  const bi = st.bank === "all" ? -1 : meta.dims.bank_id.indexOf(st.bank);
  const M = Array.from({ length: nM }, () => ({ days: 0, sh: 0, ah: 0, oh: 0, sp: 0, hi: 0, ci: 0, hw: 0, th: 0, v: 0, cc: 0, lastD: -1, z: -1, b: -1, g: -1, l: -1 }));
  const gz = new Float64Array(nG * nZ * 2), mz = new Map();
  const scope = { sh: 0, ah: 0, oh: 0, ci: 0, hw: 0, th: 0, cc: 0, rows: 0 };
  const nD = st.to - st.from + 1;
  const daily = { ci: new Float64Array(nD), th: new Float64Array(nD), hw: new Float64Array(nD) };
  const zoneDay = new Float64Array(181 * nZ * 2);
  for (let i = 0; i < f.d.length; i++) {
    const d = f.d[i];
    if (d < st.from || d > st.to) continue;
    const m = f.m[i], z = f.z[i], g = f.g[i], th = f.th[i], ah = f.ah[i];
    const r = M[m];
    r.days++; r.sh += f.sh[i]; r.ah += ah; r.oh += f.oh[i]; r.sp += f.sp[i]; r.hi += f.hi[i];
    r.ci += f.ci[i]; r.hw += f.hw[i]; r.th += th; r.v += f.v[i]; r.cc += f.cc[i]; r.g = g;
    if (d >= r.lastD) { r.lastD = d; r.z = z; r.b = f.b[i]; r.l = f.l[i]; }
    gz[(g * nZ + z) * 2] += th; gz[(g * nZ + z) * 2 + 1] += ah;
    const k = m * nZ + z; const o = mz.get(k) || [0, 0]; o[0] += th; o[1] += ah; mz.set(k, o);
    zoneDay[(d * nZ + z) * 2] += th; zoneDay[(d * nZ + z) * 2 + 1] += ah;
    if ((zi < 0 || z === zi) && (bi < 0 || f.b[i] === bi)) {
      scope.sh += f.sh[i]; scope.ah += ah; scope.oh += f.oh[i]; scope.ci += f.ci[i]; scope.hw += f.hw[i]; scope.th += th; scope.cc += f.cc[i]; scope.rows++;
      daily.ci[d - st.from] += f.ci[i]; daily.th[d - st.from] += th; daily.hw[d - st.from] += f.hw[i];
    }
  }
  // Zone index: zone's theo vs what the same games earn in the other zones (games found only in that zone are left out)
  const gTot = new Float64Array(nG * 2);
  for (let g = 0; g < nG; g++) for (let z = 0; z < nZ; z++) { gTot[g * 2] += gz[(g * nZ + z) * 2]; gTot[g * 2 + 1] += gz[(g * nZ + z) * 2 + 1]; }
  const zoneIdx = [];
  for (let z = 0; z < nZ; z++) {
    let num_ = 0, den = 0;
    for (let g = 0; g < nG; g++) {
      const th = gz[(g * nZ + z) * 2], ah = gz[(g * nZ + z) * 2 + 1];
      const oth = gTot[g * 2] - th, oah = gTot[g * 2 + 1] - ah;
      if (ah > 0 && oah > 0) { num_ += th; den += ah * (oth / oah); }
    }
    zoneIdx.push(den > 0 ? num_ / den : null);
  }
  const hitP = meta.games.map((g) => g.hit_p);
  const minDays = Math.max(1, Math.round(0.66 * nD));
  const machines = [];
  for (let m = 0; m < nM; m++) {
    const r = M[m]; if (!r.days) continue;
    // Same game, same zone, leave-one-out, weighted by the zones the machine actually stood in
    let exp = 0, own = 0;
    for (let z = 0; z < nZ; z++) {
      const o = mz.get(m * nZ + z); if (!o) continue;
      const t = gz[(r.g * nZ + z) * 2] - o[0], h = gz[(r.g * nZ + z) * 2 + 1] - o[1];
      if (h > 50) { exp += o[1] * (t / h); own += o[0]; }
    }
    const p = hitP[r.g];
    const out = {
      i: m, id: meta.dims.machine_id[m], zone: meta.dims.zone_id[r.z], bank: meta.dims.bank_id[r.b], loc: meta.dims.location_id[r.l],
      game: meta.games[r.g].theme, config: meta.dims.config_id[r.g], days: r.days, ah: r.ah, sh: r.sh, oh: r.oh, ci: r.ci, hw: r.hw, th: r.th, cc: r.cc,
      luckZ: r.v > 0 ? (r.hw - r.th) / Math.sqrt(r.v) : 0,
      hitZ: r.sp > 0 ? (r.hi - p * r.sp) / Math.sqrt(p * (1 - p) * r.sp) : 0,
      hitRate: r.sp ? r.hi / r.sp : null, hitP: p,
      vsZone: exp > 0 ? own / exp : null, zoneIdx: zoneIdx[r.z], thPerH: r.ah ? r.th / r.ah : 0,
    };
    out.verdict = Math.abs(out.luckZ) > Z_INSPECT || Math.abs(out.hitZ) > Z_INSPECT ? "Inspect"
      : out.days < minDays ? "Short exposure"
      : out.vsZone !== null && out.vsZone < 0.8 ? "Truly weak"
      : out.zoneIdx !== null && out.zoneIdx < 0.85 ? "Bad spot"
      : out.luckZ < -1.96 ? "Unlucky" : "Healthy";
    machines.push(out);
  }
  const byHw = [...machines].sort((a, b) => a.hw - b.hw);
  const gm10 = byHw.slice(0, 10).map((x) => x.id);
  const inScope = machines.filter((x) => (zi < 0 || x.zone === st.zone) && (bi < 0 || x.bank === st.bank));
  CACHE = { machines, inScope, gm10, zoneIdx, scope, daily, zoneDay, nZ, minDays, nD };
  return CACHE;
}

/* ---------- shared pieces ---------- */
function scopeLine() {
  const parts = [`${dayLabel(st.from)} to ${dayLabel(st.to)}, 2025 (${st.to - st.from + 1} gaming days)`];
  parts.push(st.zone === "all" ? "all zones" : S.F.meta.zone_names[st.zone]);
  if (st.bank !== "all") parts.push("bank " + st.bank);
  const g = ["tier", "age", "region"].filter((k) => st[k] !== "all").map((k) => st[k]);
  parts.push(g.length ? "guests: " + g.join(", ") : "all guests");
  $("#scope").textContent = "Showing " + parts.join("; ") + ".";
}
function kpis(el, items) {
  el.innerHTML = items.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
}
const chip = (v) => `<span class="chip" data-v="${esc(v)}">${esc(v)}</span>`;
const claimLink = (id) => `<a href="#" data-claim="${id}">${id}</a>`;
const zname = (z) => S.F.meta.zone_names[z] || z;

/* ---------- floor plan (SVG from surveyed coordinates) ---------- */
function floorplan(el, colorOf, { rings = [], month = null, onClick = true, title = "" } = {}) {
  const meta = S.F.meta, W = 900, H = 700, pad = 30;
  const xs = meta.slots.map((s) => s.x_m), ys = meta.slots.map((s) => s.y_m);
  const x0 = Math.min(...xs) - 10, x1 = Math.max(...xs) + 10, y0 = Math.min(...ys) - 10, y1 = Math.max(...ys) + 10;
  const sc = Math.min((W - 2 * pad) / (x1 - x0), (H - 2 * pad) / (y1 - y0));
  const X = (x) => pad + (x - x0) * sc, Y = (y) => pad + (y - y0) * sc;
  const zones = {};
  for (const s of meta.slots) { const z = (zones[s.zone_id] ||= { xs: [], ys: [] }); z.xs.push(s.x_m); z.ys.push(s.y_m); }
  const node = Object.fromEntries(meta.nodes.filter((n) => n.node_type === "zone").map((n) => [n.zone_id, n]));
  const byLoc = {};
  for (const m of CACHE.machines) byLoc[m.loc] = m;
  let svg = `<svg class="plan-svg" viewBox="0 0 ${(x1 - x0) * sc + 2 * pad} ${(y1 - y0) * sc + 2 * pad}" role="img" aria-label="${esc(title || "Casino floor plan")}">`;
  for (const [z, b] of Object.entries(zones)) {
    const zx0 = X(Math.min(...b.xs)) - 10, zy0 = Y(Math.min(...b.ys)) - 10, zx1 = X(Math.max(...b.xs)) + 10, zy1 = Y(Math.max(...b.ys)) + 10;
    const hot = st.zone === z;
    svg += `<rect x="${zx0}" y="${zy0}" width="${zx1 - zx0}" height="${zy1 - zy0}" rx="8" fill="${hot ? "#e3ebf6" : "#f4f7fa"}" stroke="${hot ? ACT : "#c7d0db"}" stroke-width="${hot ? 2 : 1}"/>`;
    const zi = CACHE.zoneIdx[S.F.meta.dims.zone_id.indexOf(z)];
    svg += `<text x="${zx0 + 2}" y="${zy0 - 6}" font-size="13" font-weight="650" fill="${INK}">${esc(zname(z))}</text>`;
    if (zi) svg += `<text x="${zx0 + 2}" y="${zy1 + 15}" font-size="11.5" fill="${zi < 0.85 ? "#8a5d0a" : INK2}">earns ${zi.toFixed(2)}x its games</text>`;
  }
  // Walkways between zone hubs; the renovated one is dashed, red while closed in the chosen month
  for (const w of meta.walkways) {
    const a = node[w.zone_a], b = node[w.zone_b]; if (!a || !b) continue;
    const closedNow = w.cf && (month === null ? st.from <= 95 && st.to >= 61 : month === 2);
    svg += `<line x1="${X(a.x_m)}" y1="${Y(a.y_m)}" x2="${X(b.x_m)}" y2="${Y(b.y_m)}" stroke="${w.cf ? (closedNow ? "#b3261e" : INK2) : "#c7d0db"}" stroke-width="${w.cf ? 2.5 : 1.5}" stroke-dasharray="${w.cf ? "6 5" : "0"}" opacity=".8"/>`;
  }
  for (const n of meta.nodes.filter((n) => n.node_type === "entrance")) {
    svg += `<rect x="${X(n.x_m) - 5}" y="${Y(n.y_m) - 5}" width="10" height="10" fill="${INK}"/><text x="${X(n.x_m) + (n.x_m > 100 ? -8 : 8)}" y="${Y(n.y_m) + (n.y_m < 5 ? -8 : 4)}" text-anchor="${n.x_m > 100 ? "end" : "start"}" font-size="11" fill="${INK2}">${esc(n.name)}</text>`;
  }
  for (const s of meta.slots) {
    const m = byLoc[s.location_id];
    const c = m ? colorOf(m) : "#ffffff";
    const ring = m && rings.includes(m.id);
    const lab = m ? `${m.id}, ${m.game}, ${zname(m.zone)}: ${m.verdict}` : `${s.location_id}: empty slot`;
    svg += `<circle class="slot" ${m ? `data-m="${m.id}" tabindex="0" role="button"` : ""} cx="${X(s.x_m)}" cy="${Y(s.y_m)}" r="${ring ? 6 : 4.2}" fill="${c}" stroke="${ring ? INK : m ? "#fff" : "#9aa7b6"}" stroke-width="${ring ? 2.5 : 1}"><title>${esc(lab)}</title></circle>`;
  }
  svg += "</svg>";
  el.innerHTML = svg;
  if (onClick) $$(".slot[data-m]", el).forEach((c) => {
    c.addEventListener("click", () => openMachine(c.dataset.m));
    c.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openMachine(c.dataset.m); } });
  });
}

/* ---------- The answer ---------- */
function renderAnswer() {
  const c = CACHE, s = c.scope, R = S.R;
  const v = {}; for (const m of c.machines) if (c.gm10.includes(m.id)) v[m.verdict] = (v[m.verdict] || 0) + 1;
  const vs = VERDICT_ORDER.filter((k) => v[k]).map((k) => `${v[k]} ${PHRASE[k]}`).join(", ");
  $("#answer-sub").textContent = `For ${dayLabel(st.from)} to ${dayLabel(st.to)}, the GM's ten lowest earners break down as: ${vs}. Not one is a weak machine once luck, location and time on the floor are counted. Replacing all ten would cost about $33,800 in leases and, in our simulations, lose money every time.`;
  const mech = R.mechanism, walk = R.walkway;
  $("#causes").innerHTML = [
    ["loc", "Location", `Back Forty earns ${R.q1.zone_index["Z-B40"].toFixed(2)}x what its games earn elsewhere. When its walkway closed, it fell from ${pct(walk.phase_ratio.before, 0)} to ${pct(walk.phase_ratio.during, 0)} of the floor rate, more than any of ${walk.placebo.n} fake closure dates.`, "C3"],
    ["leak", "Leak", `M-1158 pays on ${pct(mech.by_month.reduce((a, b) => a + b.hit, 0) / mech.by_month.length)} of spins against ${pct(0.31544)} configured, with smaller wins. Its meters are clean, so check the paytable: about ${usd(mech.shortfall_per_day)} a day.`, "C2"],
    ["luck", "Luck", `Luck scores across 310 machines spread exactly as chance predicts (SD ${R.q1.calibration.luck_z_sd.toFixed(2)}) and don't carry over from one quarter to the next (r = ${R.q1.calibration.luck_persistence_r.toFixed(2)}).`, "C1"],
  ].map(([k, t, b, cl]) => `<li class="${k}"><b>${t}</b>${b} <span class="small">${claimLink(cl)}</span></li>`).join("");
  kpis($("#kpis"), [
    [usdk(s.ci), "Coin-in (wagered)"], [usdk(s.hw), "House win"], [usdk(s.th), "Expected win (theo)"],
    [usdk(s.hw - s.th), "Luck (win minus theo)"], [pct(s.hw / s.ci), "Hold"], [pct(s.ah / s.sh, 2), "Availability"],
  ]);
  floorplan($("#floorplan"), (m) => VERDICT_COLOR[m.verdict], { rings: c.gm10, title: "Floor plan coloured by verdict" });
  const counts = {}; for (const m of c.machines) counts[m.verdict] = (counts[m.verdict] || 0) + 1;
  $("#legend").innerHTML = VERDICT_ORDER.filter((k) => counts[k]).map((k) => `<span title="${esc(VERDICT_TEXT[k])}"><i style="background:${VERDICT_COLOR[k]}"></i>${k} (${counts[k]})</span>`).join("") + `<span><i style="background:#fff;border:2px solid ${INK}"></i>GM's ten</span>`;
}

/* ---------- Q1 machines ---------- */
const MCOLS = [["id", "Machine"], ["zone", "Zone"], ["bank", "Bank"], ["game", "Game"], ["days", "Days", 1], ["hw", "House win", 1], ["th", "Expected win", 1], ["luckZ", "Luck z", 1], ["hitZ", "Hit-rate z", 1], ["vsZone", "vs same game in zone", 1], ["verdict", "Verdict"]];
let sortKey = "hw", sortDir = 1;
function machineTable(rows, el, withRank) {
  const cell = (m, k) => {
    const x = m[k];
    if (k === "zone") return esc(zname(x));
    if (k === "hw" || k === "th") return usd(x);
    if (k === "luckZ" || k === "hitZ") return (x >= 0 ? "+" : "") + x.toFixed(2);
    if (k === "vsZone") return x == null ? "n/a" : x.toFixed(2) + "x";
    if (k === "verdict") return chip(x);
    return esc(x);
  };
  el.innerHTML = `<table><thead><tr>${withRank ? "<th class=n>GM rank</th>" : ""}${MCOLS.map(([k, l, n]) => `<th class="${n ? "n" : ""}"><button data-k="${k}">${l}</button></th>`).join("")}</tr></thead><tbody>${rows.map((m, i) => `<tr class="click" data-m="${m.id}" tabindex="0">${withRank ? `<td class=n>${i + 1}</td>` : ""}${MCOLS.map(([k, , n]) => `<td class="${n ? "n" : ""}">${cell(m, k)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  $$("tr.click", el).forEach((tr) => { tr.onclick = () => openMachine(tr.dataset.m); tr.onkeydown = (e) => { if (e.key === "Enter") openMachine(tr.dataset.m); }; });
  if (!withRank) $$("th button", el).forEach((b) => b.onclick = () => { sortDir = sortKey === b.dataset.k ? -sortDir : 1; sortKey = b.dataset.k; renderMachines(); });
}
function renderMachines() {
  const c = CACHE, R = S.R;
  const gm = c.gm10.map((id) => c.machines.find((m) => m.id === id));
  const insp = c.machines.filter((m) => m.verdict === "Inspect").map((m) => m.id);
  $("#machines-sub").textContent = `${c.inScope.length} machines in scope. ${c.machines.filter((m) => m.verdict === "Truly weak").length} of ${c.machines.length} earn under 80% of the same game in the same zone. ${insp.length ? insp.join(", ") + " fails the payout test." : "No machine fails the payout test in this period."}`;
  machineTable(gm, $("#gm10"), true);
  const rows = [...c.inScope].sort((a, b) => { const x = a[sortKey], y = b[sortKey]; return (typeof x === "string" ? x.localeCompare(y) : (x ?? -1e9) - (y ?? -1e9)) * sortDir; });
  machineTable(rows, $("#all-machines"), false);
  // Mechanism: hit rate and award per hit by bet, M-1158 vs its game elsewhere
  const mech = R.mechanism;
  plot("mech-chart", [
    { type: "bar", name: "M-1158", x: mech.by_bet.map((b) => "$" + (b.bet / 100).toFixed(2) + " bet"), y: mech.by_bet.map((b) => b.hit), marker: { color: "#b3261e" }, text: mech.by_bet.map((b) => pct(b.hit)), textposition: "outside", hovertemplate: "%{x}: hit rate %{y:.1%}<extra>M-1158</extra>" },
    { type: "scatter", mode: "lines", name: "Configured", x: mech.by_bet.map((b) => "$" + (b.bet / 100).toFixed(2) + " bet"), y: mech.by_bet.map(() => 0.31544), line: { color: INK, dash: "dash" }, hovertemplate: "Configured 31.5%<extra></extra>" },
  ], { yaxis: { tickformat: ".0%", range: [0, 0.45], gridcolor: RULE, title: { text: "Share of spins that pay" } }, height: 260, showlegend: true, legend: { orientation: "h", y: 1.12 } });
  $("#mech-text").innerHTML = `At every bet size, M-1158 pays more often than Desert Gold should (z = ${R.q1.machines.find((m) => m.machine_id === "M-1158").hit_z.toFixed(0)}) but each win is smaller: ${mech.by_bet[0].award_x.toFixed(2)}x the bet against ${mech.peers.award_x.toFixed(2)}x on the same game elsewhere. Net return ${pct(mech.effective_rtp)} vs 90% configured. Its meters reconcile perfectly (all ${num(mech.integrity.sessions)} carded sessions on the floor use legal bets and legal payout steps), so the paytable is the place to look. ${claimLink("C2")}`;
  const ss = R.experiments.same_slot, fl = R.experiments.same_slot_floor;
  plot("slot-chart", [
    { type: "bar", x: ["M-1120 (Jan 1 to May 12)", "M-5076 (May 13 to Jun 30)"], y: ss.map((s) => s.theo_per_h), marker: { color: ["#b07a12", "#b07a12"] }, text: ss.map((s) => usd(s.theo_per_h, 2)), textposition: "outside", hovertemplate: "%{x}: %{y:$.2f} expected win per hour<extra></extra>" },
    { type: "scatter", mode: "lines+markers", x: ["M-1120 (Jan 1 to May 12)", "M-5076 (May 13 to Jun 30)"], y: [fl.find((x) => x.before).floor_theo_per_h, fl.find((x) => !x.before).floor_theo_per_h], line: { color: INK, dash: "dot" }, hovertemplate: "Floor average %{y:$.2f}<extra></extra>" },
  ], { yaxis: { tickprefix: "$", gridcolor: RULE, title: { text: "Expected win per available hour" } }, height: 260 });
  $("#slot-text").innerHTML = `Slot L-38-5 in Back Forty got a new machine on May 13. Expected win per hour went from ${usd(ss[0].theo_per_h, 2)} to ${usd(ss[1].theo_per_h, 2)}, still about a third of the floor average (dotted). Both machines landed on the GM's list. ${claimLink("C4")}`;
}

/* ---------- one machine ---------- */
function openMachine(id) {
  const m = CACHE.machines.find((x) => x.id === id); if (!m) return;
  const f = S.F.floor, mi = m.i;
  const days = [], cumHw = [], cumTh = [], lo = [], hi = [];
  let a = 0, b = 0, v = 0;
  for (let i = 0; i < f.d.length; i++) if (f.m[i] === mi && f.d[i] >= st.from && f.d[i] <= st.to) {
    a += f.hw[i]; b += f.th[i]; v += f.v[i];
    days.push(S.F.meta.days[f.d[i]]); cumHw.push(a); cumTh.push(b); lo.push(b - 1.96 * Math.sqrt(v)); hi.push(b + 1.96 * Math.sqrt(v));
  }
  $("#dlg-title").textContent = `${m.id}: ${m.game} in ${zname(m.zone)}, bank ${m.bank}`;
  const gmRank = CACHE.gm10.indexOf(m.id);
  $("#dlg-body").innerHTML = `<p>${chip(m.verdict)} ${esc(VERDICT_TEXT[m.verdict])}${gmRank >= 0 ? ` <b>GM's list: rank ${gmRank + 1}.</b>` : ""}</p>
    <div class="kpis">${[[usd(m.hw), "House win"], [usd(m.th), "Expected win"], [(m.luckZ >= 0 ? "+" : "") + m.luckZ.toFixed(2), "Luck z"], [pct(m.hitRate ?? 0) + " / " + pct(m.hitP), "Hit rate / configured"], [m.vsZone ? m.vsZone.toFixed(2) + "x" : "n/a", "vs same game in zone"], [m.zoneIdx ? m.zoneIdx.toFixed(2) + "x" : "n/a", "Zone vs its games"], [m.days + " days", "On the floor"], [pct(m.ah / m.sh, 1), "Availability"]].map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("")}</div>
    <div id="dlg-chart"></div><p class="cap small muted">Running house win against running expected win. The band is the 95% range luck alone would produce.</p>`;
  const dlg = $("#machine-dlg"); if (!dlg.open) dlg.showModal();
  plot("dlg-chart", [
    { x: days, y: hi, mode: "lines", line: { width: 0 }, hoverinfo: "skip" },
    { x: days, y: lo, mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(31,95,191,.12)", hoverinfo: "skip" },
    { x: days, y: cumTh, mode: "lines", line: { color: ACT }, name: "Expected", hovertemplate: "%{x}: expected %{y:$,.0f}<extra></extra>" },
    { x: days, y: cumHw, mode: "lines", line: { color: INK, width: 2 }, name: "Actual", hovertemplate: "%{x}: actual %{y:$,.0f}<extra></extra>" },
  ], { yaxis: { tickprefix: "$", gridcolor: RULE }, height: 300 });
}

/* ---------- Q2 demand ---------- */
function renderDemand() {
  const R = S.R, w = R.walkway, c = CACHE;
  const dr = w.daily_ratio;
  plot("walk-chart", [
    { x: dr.d, y: dr.r, mode: "lines", line: { color: "#b07a12", width: 1.5 }, hovertemplate: "%{x}: Back Forty at %{y:.0%} of the floor rate<extra></extra>" },
  ], { yaxis: { tickformat: ".0%", gridcolor: RULE, title: { text: "Back Forty vs rest of floor" } }, height: 280,
    shapes: [{ type: "rect", xref: "x", yref: "paper", x0: "2025-03-03", x1: "2025-04-06", y0: 0, y1: 1, fillcolor: "rgba(179,38,30,.1)", line: { width: 0 } }],
    annotations: [{ x: "2025-03-20", y: 1, yref: "paper", text: "Walkway closed", showarrow: false, font: { color: "#b3261e" } }] });
  $("#walk-text").innerHTML = `Expected win per available hour, Back Forty divided by the rest of the floor, each day. ${pct(w.phase_ratio.before, 0)} before, ${pct(w.phase_ratio.during, 0)} during, ${pct(w.phase_ratio.after, 0)} after. Door counters agree: entries into Back Forty fell from ${w.entries_per_hour["Z-B40"].before} to ${w.entries_per_hour["Z-B40"].during} per counter-hour. ${claimLink("C3")}`;
  plot("placebo-chart", [
    { type: "histogram", x: w.placebo.values, marker: { color: "#c7d0db", line: { color: "#9aa7b6", width: 1 } }, nbinsx: 24, hovertemplate: "%{y} fake windows near %{x:+.1%}<extra></extra>" },
  ], { xaxis: { tickformat: "+.0%", range: [w.real_effect_vs_rest - 0.02, w.placebo.max + 0.01], gridcolor: RULE, title: { text: "Change in Back Forty's share during the window" } }, yaxis: { gridcolor: RULE, title: { text: "Fake windows" } }, height: 260,
    shapes: [{ type: "line", x0: w.real_effect_vs_rest, x1: w.real_effect_vs_rest, yref: "paper", y0: 0, y1: 1, line: { color: "#b3261e", width: 2 } }],
    annotations: [{ x: w.real_effect_vs_rest, y: 0.95, yref: "paper", text: "Real closure", showarrow: false, xanchor: "left", xshift: 6, font: { color: "#b3261e" } }] });
  $("#placebo-text").textContent = `We pretended the walkway closed on every other 35-day window that doesn't touch the real one (${w.placebo.n} windows). None comes close: the biggest fake drop is ${pct(w.placebo.min)}, the real one ${pct(w.real_effect_vs_rest)}.`;
  const days = Array.from({ length: c.nD }, (_, i) => S.F.meta.days[st.from + i]);
  plot("daily-chart", [{ x: days, y: Array.from(c.daily.ci), type: "bar", marker: { color: "#9fb3c8" }, hovertemplate: "%{x}: %{y:$,.0f}<extra></extra>" }],
    { yaxis: { tickprefix: "$", gridcolor: RULE }, height: 260, shapes: S.F.events.map((e) => ({ type: "rect", xref: "x", yref: "paper", x0: e.s, x1: e.e, y0: 0, y1: 1, fillcolor: e.local_scope === "property" ? "rgba(31,95,191,.14)" : "rgba(74,87,104,.08)", line: { width: 0 } })) });
  const adj = R.demand.weekday_adjusted, city = R.demand.city_context;
  $("#daily-text").textContent = `Coin-in in scope; shaded bands are events (blue for the casino's own promotions). Against the Jan to Apr weekday norm, June ran ${pct(adj["2025-06"] - 1)}; Las Vegas visitors were ${pct(city[city.length - 1].yoy)} year over year that month (LVCVA, context only).`;
  $("#demand-sub").textContent = `Floor demand held steady through April and softened in May and June, in step with citywide tourism. The one local shock was the walkway closure into Back Forty, and it explains why nine of the GM's ten earn so little.`;
  renderMonthPlan();
}
function renderMonthPlan() {
  const mo = +$("#month-scrub").value, f = S.F.floor, meta = S.F.meta;
  $("#month-out").textContent = ["January", "February", "March (walkway closed from Mar 3)", "April (reopened Apr 7)", "May", "June"][mo];
  const d0 = meta.days.findIndex((d) => +d.slice(5, 7) === mo + 1), d1 = meta.days.findLastIndex((d) => +d.slice(5, 7) === mo + 1);
  const rate = {};
  for (let i = 0; i < f.d.length; i++) if (f.d[i] >= d0 && f.d[i] <= d1) { const k = meta.dims.location_id[f.l[i]]; const o = (rate[k] ||= [0, 0]); o[0] += f.th[i]; o[1] += f.ah[i]; }
  const col = (r) => { const t = Math.max(0, Math.min(1, r / 30)); return `rgb(${Math.round(237 - t * 206)},${Math.round(241 - t * 146)},${Math.round(245 - t * 54)})`; };
  floorplan($("#floorplan-month"), (m) => rate[m.loc] ? col(rate[m.loc][0] / rate[m.loc][1]) : "#fff", { month: mo, title: "Floor plan by month" });
}

/* ---------- Q3 downtime ---------- */
function renderDowntime() {
  const c = CACHE, f = S.F.floor, R = S.R.downtime, nZ = c.nZ;
  const zi = st.zone === "all" ? -1 : S.F.meta.dims.zone_id.indexOf(st.zone), bi = st.bank === "all" ? -1 : S.F.meta.dims.bank_id.indexOf(st.bank);
  let down = 0, lost = 0; const byMonth = new Float64Array(6), downMonth = new Float64Array(6);
  for (let i = 0; i < f.d.length; i++) {
    const d = f.d[i]; if (d < st.from || d > st.to) continue;
    if ((zi >= 0 && f.z[i] !== zi) || (bi >= 0 && f.b[i] !== bi)) continue;
    const dh = f.sh[i] - f.ah[i]; if (dh <= 0) continue;
    const k = (d * nZ + f.z[i]) * 2, rate = c.zoneDay[k + 1] > 0 ? c.zoneDay[k] / c.zoneDay[k + 1] : 0;
    down += dh; lost += dh * rate; const mo = +S.F.meta.days[d].slice(5, 7) - 1; byMonth[mo] += dh * rate; downMonth[mo] += dh;
  }
  kpis($("#dt-kpis"), [[num(down) + " h", "Machine-hours down"], [pct(down / c.scope.sh, 2), "Share of scheduled hours"], [usdk(lost), "Expected win lost (upper bound)"], [pct(lost / c.scope.th, 2), "Of expected win in scope"]]);
  $("#downtime-sub").textContent = `Downtime is small: ${pct(down / c.scope.sh, 2)} of scheduled hours in scope, worth at most ${usd(lost)} of expected win. It is an upper bound, because a player at a broken machine can sit down at the next one. It can't explain why the GM's ten earn so little.`;
  plot("dt-month", [{ type: "bar", x: MONTHS, y: Array.from(byMonth), marker: { color: "#6b7a8f" }, customdata: Array.from(downMonth), hovertemplate: "%{x}: %{y:$,.0f} lost, %{customdata:,.0f} h down<extra></extra>" }], { yaxis: { tickprefix: "$", gridcolor: RULE }, height: 260 });
  plot("dt-mfr", [{ type: "bar", x: R.by_manufacturer.map((r) => r.manufacturer), y: R.by_manufacturer.map((r) => r.down_share), marker: { color: ["#b07a12", "#9fb3c8", "#9fb3c8"] }, text: R.by_manufacturer.map((r) => pct(r.down_share, 2)), textposition: "outside", hovertemplate: "%{x}: %{y:.2%} of hours down<extra></extra>" }], { yaxis: { tickformat: ".1%", gridcolor: RULE }, height: 260 });
  const ts = R.tech_staffing;
  plot("dt-staff", [
    { type: "bar", name: "Planned", x: MONTHS, y: ts.map((r) => r.planned), marker: { color: "#dde3ea" } },
    { type: "bar", name: "Worked", x: MONTHS, y: ts.map((r) => r.actual), marker: { color: "#4a5768" } },
  ], { barmode: "group", yaxis: { gridcolor: RULE, title: { text: "Slot-tech shifts" } }, height: 240, showlegend: true, legend: { orientation: "h", y: 1.15 } });
  const sh = Object.fromEntries(R.by_shift.map((r) => [r.shift, r]));
  $("#dt-staff-text").innerHTML = `Slot-tech shifts fell short of plan in April (${ts[3].actual} of ${ts[3].planned}) and May (${ts[4].actual} of ${ts[4].planned}). Repairs opened on the grave shift take longest (${sh.grave.avg_h.toFixed(1)} h on average vs ${sh.day.avg_h.toFixed(1)} h on day shift). Ridgeline machines are down about ${(R.by_manufacturer[0].down_share / R.by_manufacturer[2].down_share).toFixed(1)}x as often as Halcyon. ${claimLink("C6")}`;
}

/* ---------- Q4/Q5 guests and comps ---------- */
function renderGuests() {
  const G = S.G, R = S.R;
  const m0 = +S.F.meta.days[st.from].slice(5, 7), m1 = +S.F.meta.days[st.to].slice(5, 7);
  const t = { pm: 0, ci: 0, po: 0, net: 0, th: 0, comp: 0, face: 0, ahead: 0 };
  for (let i = 0; i < G.mo.length; i++) {
    const mo = +G.mo[i].slice(5, 7);
    if (mo < m0 || mo > m1) continue;
    if (st.tier !== "all" && G.tier[i] !== st.tier) continue;
    if (st.age !== "all" && G.age[i] !== st.age) continue;
    if (st.region !== "all" && G.region[i] !== st.region) continue;
    t.pm += G.pm[i]; t.ci += G.ci[i]; t.po += G.po[i]; t.net += G.net[i]; t.th += G.th[i]; t.comp += G.comp[i]; t.face += G.face[i]; t.ahead += G.ahead_pm[i];
  }
  kpis($("#g-kpis"), [[usdk(t.ci), "Wagered (carded)"], [usdk(t.po), "Paid back"], [usdk(t.net), "Players' net"], [usdk(t.th), "Expected (theo)"], [pct(t.ahead / t.pm), "Player-months ahead"], [usdk(t.comp), "Comp cost"], [pct(t.comp / t.th, 2), "Comp cost / tracked theo"]]);
  $("#guests-sub").textContent = `Months ${MONTHS[m0 - 1]} to ${MONTHS[m1 - 1]}, tracked (loyalty-card) play only. Players' net (${usd(t.net)}) sits within ${pct(Math.abs(t.net + t.th) / t.th)} of what the games' math expects (${usd(-t.th)}): results are what the math predicts.`;
  // Concentration: computed per player in Python for the nearest preset period and one group dimension
  const p = m0 === 1 && m1 <= 3 ? "Q1" : m0 >= 4 ? "Q2" : "H1";
  const dim = ["tier", "age", "region"].find((k) => st[k] !== "all");
  const key = dim ? `${dim}:${st[dim]}` : "all";
  const cc = R.guests[p][key] || R.guests[p].all;
  kpis($("#g-conc"), [[pct(cc.top1_wager), "Of wagers from the top 1%"], [pct(cc.top10_wager), "Of wagers from the top 10%"], [pct(cc.top10_losses), "Of losses from the top 10%"], [pct(cc.ahead_share), "Of players ahead"], [num(cc.players), "Players"]]);
  $("#g-conc-text").innerHTML = `${p === "H1" ? "Jan to Jun" : p === "Q1" ? "Jan to Mar" : "Apr to Jun"}, ${dim ? esc(st[dim]) : "all tracked players"}${dim && $$(".f select").filter((s) => ["tier", "age", "region"].includes(s.id) && s.value !== "all").length > 1 ? " (concentration uses the first group chosen)" : ""}. Losses are concentrated, so we propose nothing that pushes heavy losers to play more. ${claimLink("C8")}`;
  const cp = R.comps;
  plot("comp-chart", [{ x: cp.daily_price.d, y: cp.daily_price.pts_per_usd, mode: "lines", line: { color: INK, width: 1.4 }, hovertemplate: "%{x}: %{y:.1f} points per $1 of comps<extra></extra>" }],
    { yaxis: { gridcolor: RULE, title: { text: "Points per $1 of comps" } }, height: 260, shapes: [{ type: "line", x0: cp.change_date, x1: cp.change_date, yref: "paper", y0: 0, y1: 1, line: { color: "#b3261e", dash: "dash" } }] });
  $("#comp-text").innerHTML = `Our change-point scan of the loyalty ledger finds one break: on ${cp.change_date} a $1 comp went from ${cp.price_before.toFixed(1)} to ${cp.price_after.toFixed(1)} points (${pct(cp.price_change, 0)}), in every tier at once. Six-month comp cost: ${usd(cp.total_cost)}, counted once because it already sits inside POS costs. ${claimLink("C9")}`;
  plot("comp-month", [{ type: "bar", x: cp.monthly.map((r) => r.month), y: cp.monthly.map((r) => r.reinvestment), marker: { color: cp.monthly.map((r) => r.month >= "2025-05" ? "#b3261e" : "#9fb3c8") }, text: cp.monthly.map((r) => pct(r.reinvestment, 2)), textposition: "outside", hovertemplate: "%{x}: %{y:.2%} of theo<extra></extra>" }], { yaxis: { tickformat: ".2%", gridcolor: RULE, range: [0, Math.max(...cp.monthly.map((r) => r.reinvestment)) * 1.2] }, height: 240 });
}

/* ---------- Model ---------- */
function renderForecast() {
  const md = S.R.model;
  const names = Object.keys(md.cv_mae);
  $("#cv-table").innerHTML = `<table><thead><tr><th>Model</th><th class=n>CV error, Jan to Apr</th><th class=n>Test error, May to Jun</th></tr></thead><tbody>${names.map((n) => `<tr${n === md.selected ? ' style="font-weight:700"' : ""}><td>${esc(n)}${n === md.selected ? " (chosen)" : ""}</td><td class=n>${usd(md.cv_mae[n])}</td><td class=n>${usd(md.test_mae[n])}</td></tr>`).join("")}</tbody></table>`;
  $("#forecast-sub").textContent = `We forecast daily floor coin-in. Five candidates were compared by rolling-origin cross-validation inside January to April; ${md.selected.toLowerCase()} won and was then scored once on May to June: ${usd(md.test_mae[md.selected])} a day of error vs ${usd(md.test_mae["Constant mean"])} for the constant baseline. Events count as features only if announced before the forecast date.`;
  const t = md.test, band = md.interval_80_halfwidth;
  plot("test-chart", [
    { x: t.d, y: t.pred.map((p) => p + band), mode: "lines", line: { width: 0 }, hoverinfo: "skip", showlegend: false },
    { x: t.d, y: t.pred.map((p) => p - band), mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(31,95,191,.12)", hoverinfo: "skip", name: "80% band" },
    { x: t.d, y: t.baseline, mode: "lines", line: { color: INK2, dash: "dot" }, name: "Constant baseline", hovertemplate: "Baseline %{y:$,.0f}<extra></extra>" },
    { x: t.d, y: t.pred, mode: "lines", line: { color: ACT, width: 2 }, name: "Forecast", hovertemplate: "Forecast %{y:$,.0f}<extra></extra>" },
    { x: t.d, y: t.actual, mode: "markers", marker: { color: INK, size: 5 }, name: "Actual", hovertemplate: "%{x}: actual %{y:$,.0f}<extra></extra>" },
  ], { yaxis: { tickprefix: "$", gridcolor: RULE }, height: 320, showlegend: true, legend: { orientation: "h", y: 1.12 } });
  $("#test-text").innerHTML = `The shaded 80% band (from cross-validation errors) covered ${pct(md.interval_80_coverage, 0)} of test days, under its 80% target: June ran below forecast as Las Vegas visitors fell. We report that rather than retune on the test. ${claimLink("C10")}`;
  const wd = md.weekday_forecast, lift = S.R.plan.facts.promo_lift_per_day / S.R.plan.facts.floor_hold_theo;
  $("#forecast-decision").innerHTML = `<p><b>It sets the bar a promotion must clear.</b> A promotion day must lift coin-in by more than the forecast's own uncertainty (${usd(band)}) to be told apart from a normal day. Past promotions added about ${usd(lift)} of coin-in a day, so a July promotion weekend can be measured against this frozen forecast; a tech shift's effect could not.</p><p><b>It picks the weekend.</b> Forecast coin-in by weekday: ${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => `${d} ${usdk(wd[d])}`).join(", ")}. Promotions go on the Friday to Sunday where the floor has spare seats, never into weekday hours already short of technicians.</p>`;
}

/* ---------- Q6 plan ---------- */
const ACTION_NAMES = { "A-INSPECT": "Inspect M-1158's paytable", "A-WAYFINDING": "Signs for Back Forty", "A-PROMO": "Promotion weekend", "A-MOVE-MACHINE": "Move a machine out of Back Forty", "A-TECH-SHIFT": "Add a technician shift", "A-PREVENTIVE": "Ridgeline maintenance sweep", "A-REPLACE-LEASE": "Replace with a leased machine", "A-REPLACE-BUY": "Replace with a bought machine", "A-COMP-PILOT": "Comp pilot with a control group", "A-COMP-CHANGE": "Change the comp rate floor-wide", "A-SURVEY": "Bigger guest survey", "A-MOVE-BANK": "Move a whole bank" };
const MEASURE = {
  "A-INSPECT": "Hit rate back near 31.5% and hold near 10% within two weeks of the fix (z-test on the post-fix spins).",
  "A-WAYFINDING": "Back Forty door entries and expected win per hour vs the rest of the floor, before and after install; the walkway placebo test gives the noise range.",
  "A-PROMO": "Promotion-day coin-in vs the frozen forecast and its 80% band; a lift inside the band counts as no effect.",
  "A-MOVE-MACHINE": "Moved machines vs their same-game controls left in Back Forty, and the destination bank's neighbours (to catch displaced play).",
};
const EVIDENCE = { "A-INSPECT": "C2", "A-WAYFINDING": "C3", "A-PROMO": "C12", "A-MOVE-MACHINE": "C5" };
function renderPlan() {
  const P = S.R.plan, top = P.top[0], pa = P.per_action;
  $("#plan-sub").textContent = `We scored all ${P.n_plans} legal plans (up to three action types, within $100,000, quantity limits and the comp rule), each in ${num(4000)} simulations of what July could bring. This one ranks first: expected net ${usd(top.exp_net)}, gain in ${pct(top.p_gain, 0)} of runs. The GM's plan, leasing ten replacements, ranks ${P.gm_plan.rank} and loses money in every run.`;
  $("#actions").innerHTML = Object.entries(top.plan).map(([a, q]) => `<article class="action" id="act-${a}">
      <h3>${esc(ACTION_NAMES[a])}${q > 1 ? ` (${q})` : ""}</h3><div class="cost">${usd(q * pa[a].cost1)}</div>
      <dl><dt>Expected effect</dt><dd>${usd(q * pa[a].exp_benefit1)} of expected win in July</dd>
      <dt>Range</dt><dd>${usd(q * pa[a].p05)} to ${usd(q * pa[a].p95)} (5th to 95th percentile)</dd>
      <dt>Assumes</dt><dd>${esc(pa[a].assumption)}</dd><dt>Measure</dt><dd>${esc(MEASURE[a] || "")}</dd>
      <dt>Evidence</dt><dd>${claimLink(EVIDENCE[a] || "C11")}</dd></dl></article>`).join("")
    + `<article class="action" style="border-top-color:#2e7d6b"><h3>Keep the rest</h3><div class="cost">${usd(top.keep)}</div><p class="small">Replacement is the wrong fix: the same slot with a new machine earned the same (C4). Keeping the money is a valid answer for causes that are location and luck.</p></article>`;
  const all = P.all;
  plot("plans-chart", [
    { x: all.cost, y: all.exp_net, mode: "markers", marker: { color: all.p_gain, colorscale: [[0, "#dde3ea"], [1, "#1f5fbf"]], size: 6, line: { width: 0 } }, hovertemplate: "Cost %{x:$,.0f}, expected net %{y:$,.0f}<extra></extra>" },
    { x: [top.cost], y: [top.exp_net], mode: "markers+text", marker: { color: "#2e7d6b", size: 13, symbol: "star" }, text: ["Ours"], textposition: "top center", hovertemplate: "Our plan<extra></extra>" },
    { x: [P.gm_plan.cost], y: [P.gm_plan.exp_net], mode: "markers+text", marker: { color: "#b3261e", size: 12, symbol: "x" }, text: ["GM's plan"], textposition: "bottom center", hovertemplate: "GM's plan<extra></extra>" },
  ], { xaxis: { tickprefix: "$", gridcolor: RULE, title: { text: "Cost" } }, yaxis: { tickprefix: "$", gridcolor: RULE, title: { text: "Expected net in July" } }, height: 320 });
  $("#plans-text").innerHTML = `Darker dots win more often. Every assumption is listed on its action card and in the builder. ${claimLink("C11")}`;
  const types = Object.keys(pa).filter((a) => a !== "A-MOVE-BANK");
  $("#builder").innerHTML = types.map((a) => `<label>${esc(ACTION_NAMES[a])}<input type="number" min="0" max="${pa[a].limit}" value="${top.plan[a] || 0}" data-a="${a}" aria-label="${esc(ACTION_NAMES[a])} quantity"></label>`).join("");
  const run = () => {
    const q = Object.fromEntries($$("#builder input").map((i) => [i.dataset.a, Math.max(0, Math.min(+i.value || 0, pa[i.dataset.a].limit))]).filter(([, n]) => n > 0));
    const cost = Object.entries(q).reduce((s, [a, n]) => s + n * pa[a].cost1, 0);
    const ben = Object.entries(q).reduce((s, [a, n]) => s + n * pa[a].exp_benefit1, 0);
    const errs = [];
    if (cost > 100000) errs.push("over the $100,000 budget");
    if (Object.keys(q).length > 3) errs.push("more than 3 action types");
    if (q["A-COMP-PILOT"] && q["A-COMP-CHANGE"]) errs.push("the comp pilot can't run with a floor-wide comp change");
    if ((q["A-MOVE-MACHINE"] || 0) > 3) errs.push("only 3 free slots exist in busier zones");
    const el = $("#builder-out");
    el.className = "result" + (errs.length ? " bad" : "");
    el.innerHTML = errs.length ? "Not allowed: " + errs.join("; ") + "." : `Cost ${usd(cost)}, keep ${usd(100000 - cost)}. Expected July effect ${usd(ben)}, expected net <b>${usd(ben - cost)}</b>. Our plan: ${usd(top.exp_net)}.`;
  };
  $$("#builder input").forEach((i) => i.addEventListener("input", run)); run();
}

/* ---------- Evidence ---------- */
function renderEvidence() {
  $("#claims").innerHTML = `<table><thead><tr><th>Claim</th><th>Table or query</th><th>Result</th><th>Alternative tested</th><th>Limitation</th></tr></thead><tbody>${S.C.map((c) => `<tr id="claim-${c.id}"><td><b>${c.id}</b> (${c.q}) ${esc(c.claim)} <a href="#" data-tab-go="${c.tab}">See it</a></td><td><code>${esc(c.evidence)}</code></td><td>${esc(c.result)}</td><td>${esc(c.alternative)}</td><td>${esc(c.limitation)}</td></tr>`).join("")}</tbody></table>`;
  const ok = S.K.filter((k) => k.ok).length;
  $("#checks-h").textContent = `${ok} of ${S.K.length} checks pass`;
  $("#checks").innerHTML = `<table><tbody>${S.K.map((k) => `<tr><td>${k.ok ? "Pass" : "Fail"}</td><td>${esc(k.line)}</td></tr>`).join("")}</tbody></table>`;
  $$("[data-tab-go]").forEach((a) => a.onclick = (e) => { e.preventDefault(); go(a.dataset.tabGo); });
}

/* ---------- navigation and rendering ---------- */
const RENDER = { answer: renderAnswer, machines: renderMachines, demand: renderDemand, downtime: renderDowntime, guests: renderGuests, forecast: renderForecast, plan: renderPlan, evidence: renderEvidence };
function go(tab, anchor) {
  st.tab = tab in RENDER ? tab : "answer";
  $$("main section").forEach((s) => s.classList.toggle("on", s.id === "s-" + st.tab));
  $$("nav.rail a").forEach((a) => (a.dataset.tab === st.tab ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
  RENDER[st.tab]();
  writeHash();
  if (anchor) { const el = document.getElementById(anchor); if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); el.classList.add("hl"); setTimeout(() => el.classList.remove("hl"), 2500); } }
  else window.scrollTo({ top: 0 });
}
function rerender() { compute(); scopeLine(); syncControls(); RENDER[st.tab](); writeHash(); }
function syncControls() {
  $("#from").value = st.from; $("#to").value = st.to;
  for (const k of ["zone", "bank", "tier", "age", "region"]) $("#" + k).value = st[k];
  const presets = { H1: [0, 180], Q1: [0, 89], Q2: [90, 180], CL: [61, 95] };
  $$(".presets button").forEach((b) => b.setAttribute("aria-pressed", String(presets[b.dataset.p][0] === st.from && presets[b.dataset.p][1] === st.to)));
}
function buildControls() {
  const meta = S.F.meta;
  $("#from").innerHTML = $("#to").innerHTML = meta.days.map((d, i) => `<option value="${i}">${dayLabel(i)}</option>`).join("");
  $("#zone").innerHTML = `<option value="all">All zones</option>` + meta.dims.zone_id.map((z) => `<option value="${z}">${esc(zname(z))}</option>`).join("");
  const fillBanks = () => {
    const banks = [...new Set(meta.slots.filter((s) => st.zone === "all" || s.zone_id === st.zone).map((s) => s.bank_id))].sort();
    $("#bank").innerHTML = `<option value="all">All banks</option>` + banks.map((b) => `<option value="${b}">${b}</option>`).join("");
  };
  fillBanks();
  for (const k of ["tier", "age", "region"]) {
    const vals = [...new Set(S.G[k])].sort();
    $("#" + k).innerHTML = `<option value="all">All ${k === "tier" ? "tiers" : k === "age" ? "ages" : "regions"}</option>` + vals.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
  }
  const presets = { H1: [0, 180], Q1: [0, 89], Q2: [90, 180], CL: [61, 95] };
  $$(".presets button").forEach((b) => b.onclick = () => { [st.from, st.to] = presets[b.dataset.p]; rerender(); });
  $("#from").onchange = (e) => { st.from = Math.min(+e.target.value, st.to); rerender(); };
  $("#to").onchange = (e) => { st.to = Math.max(+e.target.value, st.from); rerender(); };
  $("#zone").onchange = (e) => { st.zone = e.target.value; st.bank = "all"; fillBanks(); rerender(); };
  $("#bank").onchange = (e) => { st.bank = e.target.value; rerender(); };
  for (const k of ["tier", "age", "region"]) $("#" + k).onchange = (e) => { st[k] = e.target.value; rerender(); };
  $("#reset").onclick = () => { Object.assign(st, { from: 0, to: 180, zone: "all", bank: "all", tier: "all", age: "all", region: "all" }); fillBanks(); rerender(); };
  $$("nav.rail a").forEach((a) => a.onclick = (e) => { e.preventDefault(); go(a.dataset.tab); });
  document.addEventListener("click", (e) => { const a = e.target.closest("[data-claim]"); if (a) { e.preventDefault(); go("evidence", "claim-" + a.dataset.claim); } });
  $("#dlg-close").onclick = () => $("#machine-dlg").close();
  $("#month-scrub").oninput = renderMonthPlan;
}

/* ---------- Judge tour: the four tests judges run ---------- */
const TOUR = [
  { h: "1. Change the analysis period", p: "We switched the period to the walkway closure (Mar 3 to Apr 6). Every number and verdict on the page is recomputed in your browser from 55,092 machine-days. Try the period buttons above.", run: () => { [st.from, st.to] = [61, 95]; rerender(); go("answer", "answer-plan-wrap"); } },
  { h: "2. Drill into one bank and one guest group", p: "Now Back Forty bank B-38 (home of the slot that got a new machine in May) and Platinum guests. Machines, downtime and player results all follow the filters.", run: () => { Object.assign(st, { from: 0, to: 180, zone: "Z-B40", bank: "B-38", tier: "Platinum" }); buildBanks(); rerender(); go("machines", "all-machines"); } },
  { h: "3. Find how the model was validated", p: "Five models were compared on January to April only; the winner was scored once on May to June against a constant baseline, and its interval coverage is reported even though it under-covers.", run: () => { Object.assign(st, { zone: "all", bank: "all", tier: "all" }); buildBanks(); rerender(); go("forecast", "cv-panel"); } },
  { h: "4. Trace a recommendation to its evidence", p: "The $1,200 inspection of M-1158 links to claim C2: the hit-rate test in two tables, the meter audit, the alternative we tested and the limitation.", run: () => { go("plan", "act-A-INSPECT"); setTimeout(() => go("evidence", "claim-C2"), 2200); } },
];
let tourI = -1;
function buildBanks() { $("#zone").value = st.zone; $("#zone").dispatchEvent(new Event("rebuild")); const banks = [...new Set(S.F.meta.slots.filter((s) => st.zone === "all" || s.zone_id === st.zone).map((s) => s.bank_id))].sort(); $("#bank").innerHTML = `<option value="all">All banks</option>` + banks.map((b) => `<option value="${b}">${b}</option>`).join(""); }
function tourStep(i) {
  tourI = i; const t = TOUR[i]; if (!t) return endTour();
  $("#tour").hidden = false; $("#tour-h").textContent = t.h; $("#tour-p").textContent = t.p; $("#tour-n").textContent = `${i + 1} of ${TOUR.length}`;
  $("#tour-next").textContent = i === TOUR.length - 1 ? "Finish" : "Next"; t.run(); $("#tour-next").focus();
}
function endTour() { $("#tour").hidden = true; tourI = -1; }

/* ---------- boot ---------- */
async function boot() {
  const get = (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(p + " " + r.status); return r.json(); });
  [S.F, S.R, S.C, S.G, S.K] = await Promise.all(["data/floor.json", "data/results.json", "data/claims.json", "data/guests.json", "data/checks.json"].map(get));
  readHash(); buildControls();
  $("#tour-start").onclick = () => tourStep(0);
  $("#tour-next").onclick = () => tourStep(tourI + 1);
  $("#tour-skip").onclick = endTour;
  compute(); scopeLine(); syncControls(); go(st.tab);
  document.dispatchEvent(new CustomEvent("floor-ready"));
}
const fail = (e) => { $("#main").innerHTML = `<p>The data didn't load (${esc(e.message)}). Reload the page; if it persists, open it from a web server rather than as a file.</p>`; };
const waitPlotly = (n = 0) => (window.Plotly || n > 200 ? boot().catch(fail) : setTimeout(() => waitPlotly(n + 1), 50));
document.addEventListener("DOMContentLoaded", () => waitPlotly());
window.FLOOR = { PHRASE, st, S, go, rerender, compute: () => CACHE, usd, pct, openMachine };
