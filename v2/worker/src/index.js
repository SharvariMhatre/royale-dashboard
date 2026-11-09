// Cloudflare Worker behind "Ask the floor". Holds the Anthropic key as a secret; never in the browser.
// It loads the verified facts from the published site itself (not from the request), so a visitor
// can't feed it numbers, and tells Claude to answer only from those facts and cite claim IDs.
// Deploy: cd v2/worker && npx wrangler deploy && npx wrangler secret put ANTHROPIC_API_KEY
// Then set window.ASK_ENDPOINT in v2/site/ask-config.js to the worker URL.

const MODEL = "claude-haiku-5-5";
const MAX_Q = 400;

export default {
  async fetch(req, env) {
    const origin = req.headers.get("origin") || "";
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
    const cors = { "access-control-allow-origin": allowed.includes(origin) ? origin : allowed[0] || "", "access-control-allow-methods": "POST", "access-control-allow-headers": "content-type" };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST" || !allowed.includes(origin)) return json({ error: "Not allowed." }, 403, cors);

    // Simple per-visitor rate limit: 20 questions per 10 minutes (KV optional)
    const ip = req.headers.get("cf-connecting-ip") || "anon";
    if (env.RATE) {
      const k = `r:${ip}:${Math.floor(Date.now() / 600000)}`;
      const n = +(await env.RATE.get(k)) || 0;
      if (n >= 20) return json({ error: "Too many questions; try again in a few minutes." }, 429, cors);
      await env.RATE.put(k, String(n + 1), { expirationTtl: 700 });
    }

    let body;
    try { body = await req.json(); } catch { return json({ error: "Bad request." }, 400, cors); }
    const question = String(body.question || "").slice(0, MAX_Q);
    const scope = String(body.facts?.scope || "").slice(0, 300);
    if (!question) return json({ error: "Ask a question." }, 400, cors);

    const site = env.SITE_URL.replace(/\/$/, "");
    const [claims, results] = await Promise.all([
      fetch(`${site}/data/claims.json`, { cf: { cacheTtl: 600 } }).then((r) => r.json()),
      fetch(`${site}/data/results.json`, { cf: { cacheTtl: 600 } }).then((r) => r.json()),
    ]);
    const facts = {
      claims,
      gm10: results.q1.gm10.map((id) => { const m = results.q1.machines.find((x) => x.machine_id === id); return { id, zone: m.zone, verdict: m.verdict, house_win: Math.round(m.house_win), theo: Math.round(m.theo), luck_z: +m.luck_z.toFixed(2), hit_z: +m.hit_z.toFixed(1), vs_same_game_zone: m.vs_same_game_zone && +m.vs_same_game_zone.toFixed(2) }; }),
      zone_index: results.q1.zone_index, plan_top: results.plan.top.slice(0, 3), gm_plan: results.plan.gm_plan, per_action: results.plan.per_action,
      model: { selected: results.model.selected, cv_mae: results.model.cv_mae, test_mae: results.model.test_mae, coverage_80: results.model.interval_80_coverage },
    };
    const system = `You are the analyst on a dashboard about a FICTIONAL casino (synthetic data). Answer only from the FACTS JSON. If the facts don't contain the answer, say so in one sentence and suggest a question they can answer. Cite claim IDs like (C2). Never accuse anyone: unusual payouts are leads to inspect. Never suggest targeting heavy losers. Two to four plain sentences. The viewer's current filter: ${scope}.\nFACTS: ${JSON.stringify(facts)}`;
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: env.MODEL || MODEL, max_tokens: 400, system, messages: [{ role: "user", content: question }] }),
    });
    if (!r.ok) return json({ error: "The assistant is unavailable right now." }, 502, cors);
    const j = await r.json();
    return json({ answer: (j.content || []).map((c) => c.text || "").join("").trim() }, 200, cors);
  },
};

const json = (o, status, headers) => new Response(JSON.stringify(o), { status, headers: { ...headers, "content-type": "application/json" } });
