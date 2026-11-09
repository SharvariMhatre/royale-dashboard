// Vercel function behind "Ask the floor" (same site, so no CORS). The Anthropic key lives only in the
// Vercel environment variable ANTHROPIC_API_KEY. Facts are loaded from this site's own published data,
// never from the request, and Claude is told to answer only from them and cite claim IDs.
// Without the key it returns 503 and the page falls back to its built-in verified answers.

const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-5-5";
const hits = new Map(); // best-effort per-instance rate limit: 20 questions per 10 minutes per IP

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Use POST." });
  if (!process.env.ANTHROPIC_API_KEY) return res.status(503).json({ error: "The assistant isn't configured; try a suggested question." });
  const ip = (req.headers["x-forwarded-for"] || "anon").split(",")[0].trim();
  const win = Math.floor(Date.now() / 600000), key = `${ip}:${win}`;
  const n = (hits.get(key) || 0) + 1; hits.set(key, n);
  if (n > 20) return res.status(429).json({ error: "Too many questions; try again in a few minutes." });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const question = String(body.question || "").slice(0, 400);
  const scope = String(body.facts?.scope || "").slice(0, 300);
  if (!question) return res.status(400).json({ error: "Ask a question." });

  const base = `https://${req.headers.host}`;
  const [claims, results] = await Promise.all([fetch(`${base}/data/claims.json`).then((r) => r.json()), fetch(`${base}/data/results.json`).then((r) => r.json())]);
  const facts = {
    claims,
    gm10: results.q1.gm10.map((id) => { const m = results.q1.machines.find((x) => x.machine_id === id); return { id, zone: m.zone, verdict: m.verdict, house_win: Math.round(m.house_win), theo: Math.round(m.theo), luck_z: +m.luck_z.toFixed(2), hit_z: +m.hit_z.toFixed(1) }; }),
    zone_index: results.q1.zone_index, plan_top: results.plan.top.slice(0, 3), gm_plan: results.plan.gm_plan, per_action: results.plan.per_action,
    model: { selected: results.model.selected, cv_mae: results.model.cv_mae, test_mae: results.model.test_mae, coverage_80: results.model.interval_80_coverage },
  };
  const system = `You are the analyst on a dashboard about a FICTIONAL casino (synthetic data). Answer only from the FACTS JSON. If the facts don't contain the answer, say so in one sentence and suggest a question they can answer. Cite claim IDs like (C2). Never accuse anyone: unusual payouts are leads to inspect. Never suggest targeting heavy losers. Two to four plain sentences. The viewer's current filter: ${scope}.\nFACTS: ${JSON.stringify(facts)}`;
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": process.env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: MODEL, max_tokens: 400, system, messages: [{ role: "user", content: question }] }),
  });
  if (!r.ok) return res.status(502).json({ error: "The assistant is unavailable right now." });
  const j = await r.json();
  return res.status(200).json({ answer: (j.content || []).map((c) => c.text || "").join("").trim() });
}
