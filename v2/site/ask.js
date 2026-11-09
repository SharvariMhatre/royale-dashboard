/* Ask the floor: answers come only from the dashboard's verified numbers, recomputed for the current filters.
   Known questions are answered instantly in the browser and move the dashboard to the evidence.
   Other questions go to an optional Claude endpoint (ask-config.js sets window.ASK_ENDPOINT) that receives
   the same verified facts and is instructed to answer only from them. Without an endpoint, nothing leaves the page. */
"use strict";
(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let F;
  const say = (q, html, cite) => {
    const log = $("#ask-log");
    log.insertAdjacentHTML("beforeend", `<div class="q">${esc(q)}</div><div class="a">${html}${cite ? `<cite>${cite}</cite>` : ""}</div>`);
    log.scrollTop = log.scrollHeight;
  };
  const zn = (z) => F.S.F.meta.zone_names[z] || z;

  const INTENTS = [
    { re: /\bm-?(\d{4})\b/i, run: (q, m) => {
        const id = "M-" + m[1], c = F.compute(), x = c.machines.find((r) => r.id === id);
        if (!x) return [`${id} wasn't on the floor in the selected period.`];
        F.openMachine(id);
        const rank = c.gm10.indexOf(id);
        return [`<b>${id}</b> (${esc(x.game)}, ${esc(zn(x.zone))}) is <b>${x.verdict === "Inspect" ? "flagged for inspection" : F.PHRASE[x.verdict]}</b>${rank >= 0 ? `, number ${rank + 1} on the GM's list` : ""}. House win ${F.usd(x.hw)} vs expected ${F.usd(x.th)} (luck z ${x.luckZ.toFixed(2)}); it pays on ${F.pct(x.hitRate)} of spins vs ${F.pct(x.hitP)} configured (z ${x.hitZ.toFixed(1)}); it earns ${x.vsZone ? x.vsZone.toFixed(2) + "x" : "n/a"} the same game in the same zone, and its zone earns ${x.zoneIdx ? x.zoneIdx.toFixed(2) + "x" : "n/a"} what its games earn elsewhere.${id === "M-1158" ? " Its wins are smaller than the game's (2.50x vs 2.85x the bet) and its meters reconcile, so the paytable is the place to look. A lead to inspect, not an accusation." : ""}`, "Recomputed for your filters. Machine view opened. Claims C1, C2."];
      } },
    { re: /(gm|bottom|lowest|worst|ten|10)\b.*(machine|list|replace)|replace/i, run: () => {
        const c = F.compute(), v = {};
        c.gm10.forEach((id) => { const x = c.machines.find((r) => r.id === id); v[x.verdict] = (v[x.verdict] || 0) + 1; });
        F.go("machines", "gm10-panel");
        return [`For this period the GM's ten are: ${Object.entries(v).map(([k, n]) => `${n} ${F.PHRASE[k]}`).join(", ")}. None earns under 80% of the same game in the same zone. Leasing ten replacements ranks ${F.S.R.plan.gm_plan.rank} of ${F.S.R.plan.n_plans} plans and loses money in every simulation.`, "Claims C1, C4, C11."];
      } },
    { re: /back forty|walkway|location|closure|zone/i, run: () => {
        const w = F.S.R.walkway; F.go("demand", "walk-panel");
        return [`Back Forty earns ${F.S.R.q1.zone_index["Z-B40"].toFixed(2)}x what its games earn elsewhere. While its walkway from Main Entrance was closed (Mar 3 to Apr 6) it fell from ${F.pct(w.phase_ratio.before, 0)} to ${F.pct(w.phase_ratio.during, 0)} of the floor rate and recovered to ${F.pct(w.phase_ratio.after, 0)}; that drop is bigger than all ${w.placebo.n} fake closure windows.`, "Claim C3."];
      } },
    { re: /downtime|broken|repair|technician|tech/i, run: () => {
        const d = F.S.R.downtime.total; F.go("downtime");
        return [`Machines were down ${(d.down_h).toFixed(0)} hours, ${F.pct(d.down_h / d.sched_h, 2)} of scheduled time, worth at most ${F.usd(d.lost_theo)} of expected win over six months. Technician shifts fell short of plan in April and May.`, "Claim C6."];
      } },
    { re: /model|forecast|validat|baseline|holdout/i, run: () => {
        const m = F.S.R.model; F.go("forecast", "cv-panel");
        return [`${m.selected} was chosen by rolling-origin cross-validation on January to April only, then scored once on May to June: ${F.usd(m.test_mae[m.selected])} a day of error vs ${F.usd(m.test_mae["Constant mean"])} for a constant baseline. Its 80% band covered ${F.pct(m.interval_80_coverage, 0)} of test days.`, "Claim C10."];
      } },
    { re: /plan|budget|100|fund|spend|action/i, run: () => {
        const p = F.S.R.plan, t = p.top[0]; F.go("plan");
        return [`Of ${p.n_plans} legal plans, the best spends ${F.usd(t.cost)} and keeps ${F.usd(t.keep)}: inspect M-1158, signs for Back Forty, and two promotion weekends. Expected net ${F.usd(t.exp_net)}, gain in ${F.pct(t.p_gain, 0)} of 4,000 simulations.`, "Claims C11, C12."];
      } },
    { re: /comp|loyal|point|reward/i, run: () => {
        const c = F.S.R.comps; F.go("guests", "comp-chart");
        return [`On ${c.change_date} a $1 comp went from ${c.price_before.toFixed(1)} to ${c.price_after.toFixed(1)} points (${F.pct(c.price_change, 0)}) in every tier. Comp cost rose from ${F.pct(c.monthly[0].reinvestment, 2)} to ${F.pct(c.monthly[c.monthly.length - 1].reinvestment, 2)} of expected win; six-month total ${F.usd(c.total_cost)}.`, "Claim C9."];
      } },
    { re: /player|guest|lose|lost|net|concentrat/i, run: () => {
        const g = F.S.R.guests.H1.all; F.go("guests");
        return [`Tracked players wagered ${F.usd(g.coin_in)} and netted ${F.usd(g.net)}; ${F.pct(g.ahead_share)} finished ahead. The top 10% account for ${F.pct(g.top10_losses, 0)} of losses, so we propose nothing that pushes heavy losers to play more.`, "Claim C8."];
      } },
    { re: /luck|unlucky|chance|random/i, run: () => {
        const q = F.S.R.q1.calibration; F.go("machines");
        return [`Luck z-scores across 310 machines have a spread of ${q.luck_z_sd.toFixed(2)} (pure chance gives 1) and don't carry over from Jan to Mar into Apr to Jun (r = ${q.luck_persistence_r.toFixed(2)}). Luck explains noise, not the GM's list.`, "Claim C1."];
      } },
  ];

  function facts() {
    const c = F.compute(), R = F.S.R;
    return { scope: document.querySelector("#scope").textContent, claims: F.S.C.map(({ id, claim, result, alternative, limitation }) => ({ id, claim, result, alternative, limitation })),
      gm10: c.gm10.map((id) => { const x = c.machines.find((r) => r.id === id); return { id, zone: x.zone, verdict: x.verdict, house_win: Math.round(x.hw), theo: Math.round(x.th), luck_z: +x.luckZ.toFixed(2), hit_z: +x.hitZ.toFixed(1) }; }),
      scope_totals: c.scope, plan_top: R.plan.top[0], gm_plan: R.plan.gm_plan };
  }

  async function ask(q) {
    for (const it of INTENTS) { const m = q.match(it.re); if (m) { const [html, cite] = it.run(q, m); return say(q, html, cite); } }
    if (window.ASK_ENDPOINT) {
      say(q, "<span class='muted'>Checking the verified numbers...</span>");
      try {
        const r = await fetch(window.ASK_ENDPOINT, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question: q, facts: facts() }) });
        const j = await r.json().catch(() => ({}));
        $("#ask-log").lastElementChild.innerHTML = j.answer ? esc(j.answer) + "<cite>Answered by Claude from the verified facts on this page.</cite>"
          : "I answer free-form questions only when the assistant is switched on. Try a machine ID (like M-1158), the GM's list, Back Forty, downtime, the forecast, the plan, comps, players or luck.";
      } catch (e) { $("#ask-log").lastElementChild.textContent = "The assistant is offline. Try one of the suggested questions."; }
      return;
    }
    say(q, "I answer only from this page's verified numbers. I can explain any machine (type its ID, like M-1158), the GM's list, Back Forty, downtime, the forecast, the plan, comps, players or luck.");
  }

  document.addEventListener("floor-ready", () => {
    F = window.FLOOR;
    const sugg = ["Why is M-1158 on the GM's list?", "Should we replace the bottom ten?", "What happened when the walkway closed?", "How was the model validated?", "What does the $100,000 plan buy?"];
    $("#ask-sugg").innerHTML = sugg.map((s) => `<button type="button">${esc(s)}</button>`).join("");
    $("#ask-sugg").onclick = (e) => { const b = e.target.closest("button"); if (b) ask(b.textContent); };
    $("#ask-open").onclick = () => { $("#ask").hidden = false; $("#ask-in").focus(); };
    $("#ask-close").onclick = () => { $("#ask").hidden = true; $("#ask-open").focus(); };
    $("#ask-form").onsubmit = (e) => { e.preventDefault(); const q = $("#ask-in").value.trim(); if (q) { ask(q); $("#ask-in").value = ""; } };
  });
})();
