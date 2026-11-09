// Browser engine parity: the dashboard's in-browser numbers must match the Python pipeline.
// Usage: serve v2/site on :8790, then node v2/tests/browser_parity.cjs [plotly.min.js path]
const { chromium } = require("playwright"); const fs = require("fs");
const R = JSON.parse(fs.readFileSync(__dirname + "/../site/data/results.json"));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const pl = process.argv[2]; if (pl) await p.route(/plotly/, (r) => r.fulfill({ body: fs.readFileSync(pl), contentType: "application/javascript" }));
  await p.route(/fonts\./, (r) => r.abort());
  await p.goto("http://localhost:8790/"); await p.waitForFunction(() => window.FLOOR && window.FLOOR.compute());
  const js = await p.evaluate(() => window.FLOOR.compute().machines.map((m) => ({ id: m.id, v: m.verdict, lz: m.luckZ, hz: m.hitZ, vz: m.vsZone, th: m.th })));
  let bad = 0; const py = Object.fromEntries(R.q1.machines.map((m) => [m.machine_id, m]));
  for (const m of js) {
    const q = py[m.id]; const d = Math.abs(m.lz - q.luck_z) + Math.abs(m.hz - q.hit_z) + Math.abs((m.vz ?? 0) - (q.vs_same_game_zone ?? 0));
    if (m.v !== q.verdict || d > 0.01 || Math.abs(m.th - q.theo) > 1) { bad++; if (bad < 6) console.log("MISMATCH", m, { v: q.verdict, lz: q.luck_z, hz: q.hit_z, vz: q.vs_same_game_zone, th: q.theo }); }
  }
  const gm = await p.evaluate(() => window.FLOOR.compute().gm10);
  if (JSON.stringify(gm) !== JSON.stringify(R.q1.gm10)) { bad++; console.log("GM10 differs", gm); }
  console.log(`${js.length} machines compared, ${bad} mismatches`); await b.close(); process.exit(bad ? 1 : 0);
})();
