# HANDOFF: three-skin restyle of The Gilded Ace dashboard

Last updated: **2026-11-08** (early morning). Deadline for the restyle: **2026-11-08 12:00 (noon)**.
Branch `feature/ui-improvement`, HEAD `8901dd9`. **Nothing committed, nothing pushed, nothing deployed.** The live site is unchanged.
Check: `git status --short` shows `M app/art.py`, `M app/pages.py`, `M app/theme.py`, and `??` for `HANDOFF.md`, `app/skins/`, `design/`, `tests/test_skins.py`.

## Resume here
Phases 0 to 4 are done and verified locally (see `design/VERIFY.md`). **The user first chose paper (C), then changed it to noir (A) as the default** (2026-11-08). Done locally: `DEFAULT_SKIN = "noir"` in `app/theme.py` (a bare URL and any link without `&skin=` now show noir; `?skin=default` is the original Ocean Depths look; `SKIN_Q` is empty for noir). Noir borders (new `EDGE` token, in `noir.py` only) and the marquee (now 2 loops) are FIXED and Lighthouse accessibility is 100 on two pages. The cream-slab bars are FIXED with a `CHART_MARK` token in `theme.py`, all four skins and two `pages.py` call sites (user approved "Bar fix only"). Still open and needing the user's approval to edit `app/pages.py`: the mobile floor-map legend clip (proposal: `columns=alt.expr(...)` plus `pad_x` 6 to 12, which also shifts the desktop map in every skin); both diffs are in `C:\\Users\\Fr33s\\.claude\\projects\\C--dev-source-repos-royale-dashboard\\005eab98-f564-4454-8e99-ae83645ec663\\subagents\\workflows\\wf_eaa9b2eb-fee\\journal.jsonl`; `tests/test_skins.py` passes every skin explicitly; `tests/test_theme.py` now imports `skins.default` (it checks the Ocean Depths roles). All four test scripts exit 0. Waiting on the user for: **approval by name** of commit, push, deploy, and whether to change `.streamlit/config.toml` (still a static light theme). Do none of these on your own. Optional next: run `design/HUMAN_TEST.md`; fix the open issues listed in `VERIFY.md` section 9 (most need a seam change the user has not approved).

Read first: this file, `design/VERIFY.md`, `design/DIRECTIONS.md`, project `CLAUDE.md`. The approved plan is at `C:\Users\Fr33s\.claude\plans\goal-the-gilded-ace-indexed-shore.md` (local to the original Windows profile; decisions are summarised below if it is missing).

## What exists now
| Item | Where | Status |
|---|---|---|
| Skin seam: `theme.py` loads `app/skins/<name>.py` at import; `?skin=<default|noir|control|paper>` wins, then `st.session_state["skin"]`, then default; unknown names fall back to default | `app/theme.py` top | Done, tested |
| `default` skin = old tokens and CSS verbatim (+ a few literal hexes turned into tokens with the same values) | `app/skins/default.py` | Byte-identical CSS and tokens (VERIFY 2) |
| `noir` (A, dark), `control` (B, mid-tone), `paper` (C, light) | `app/skins/{noir,control,paper}.py` | Built, refined in a browser, reviewed; parity and tests pass |
| New-session links keep the skin | `theme.py` (gm card href) and `pages.py` (zoomcard href): `{SKIN_Q}` appended for non-default skins | Done |
| `art.py` literal hexes -> tokens | `app/art.py` | Done |
| New test: tokens, contrast, parity, 4 judge paths for all 4 skins | `tests/test_skins.py` | Exit 0 |
| Parity harness | `design/harness/extract.py` (writes JSON), `compare.py` (ignores the CSS entry) | Done |
| Reports | `design/VERIFY.md`, `design/HUMAN_TEST.md` (written, NOT run), `design/DIRECTIONS.md`, `design/BASELINE.md` | Done |
| Screenshots | `design/{noir,control,paper}/`, `design/baseline/`; Lighthouse in `design/lighthouse_default/`, `design/lighthouse_paper/` | Some skin shots predate their final CSS edit |

Run a skin locally: `.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.port 8610`, then open `http://localhost:8610/?skin=noir` (or `control`, `paper`). Tests (each must exit 0): `.venv\Scripts\python.exe -I tests/test_budget.py`, `test_validate_contracts.py`, `test_theme.py`, `test_skins.py`.

## Worktrees (scratch, uncommitted work only)
Three git worktrees exist under the session scratchpad (`...\scratchpad\wt\{noir,control,paper}`) on branches `skin/noir`, `skin/control`, `skin/paper`. They hold **no commits** (still at `8901dd9`); their skin files were **copied** into `app/skins/` in the main tree. The main-tree copies are canonical (they include later fixes: noir calendar, paper and control heading fonts). Nothing to merge. Remove with `git worktree remove --force <path>` and `git branch -D skin/<name>` when no longer wanted (needs the user's go).

## Decisions made by the user (do not re-ask)
| Decision | Value |
|---|---|
| Checkpoints | Stopped after Phase 0 and Phase 1 (both passed; user said "Approve all three") |
| Dark skins | Exactly one dark (noir) |
| Worktrees | One per parallel build agent (done) |
| `.venv` install | Approved and done |
| Tiers | Tier 1 = three CSS skins (done). Tier 2 (React/TS islands via Component v2) was NOT started; stretch only, would need npm approval and a Cloud preview deploy |
| Full Streamlit replacement | Rejected for this deadline |
| Winner policy | Winner becomes default (user still has to pick the winner) |
| Fonts via Google `@import`; chart-colour lightness nudges count as presentation-only | Taken as approved with "Approve all three"; the user did not answer those two sub-questions separately |

## Approvals still required (by name, each time)
Commit; push; open/update PR; deploy; edit `requirements.txt`; edit `.streamlit/config.toml`; any new npm dependency (Tier 2); merging or deleting worktree branches. Before any commit show `git status --short`, `git diff --stat`, and a file-by-file summary, then wait.

## Known open issues (full table in VERIFY.md section 9)
Single-series bars use the text colour (huge cream bars in noir, near-black in control; needs a chart-mark token); blue/sky colours close in lightness; input borders under 3:1 in noir and control; noir marquee has no pause control; mobile floor-map legend clipped; skins depend on Streamlit 1.67.0 `data-testid` names and `!important` overrides because `config.toml` is a static light theme; standalone axe-core was blocked by the auto-mode classifier (Lighthouse a11y 100 for default and paper, noir and control not run).

## Adjacent issues (listed, not fixed; unchanged from before)
- `p3_claims` has 5 of 7 rows with unfilled "EDIT:" text (hidden by the app); `p3_actions` has an "EDIT: weakest zone" target, so Q2 has no team claim on the Evidence page.
- `PLAN_EVIDENCE` keyword matching (`pages.py:534`) silently empties evidence if claim text changes.
- `config.toml` `font = "sans serif"` is not a documented value; dead `_CHROME_HIDE` in `theme.py`.
- Every page footer shows "no _meta sidecar (version unknown)" warnings for team files.
- Hardcoded constants in `pages.py` ("181 days", "Back Forty", month keys).
- Streamlit's heading font overrides the default skin's `.ph h1` "Inter Tight" (pre-existing).

## If you are a new session under a different Claude login
Conversation memory will not include the prior session. Connectors belong to the account; none are needed to continue. The repo files above are the only state that matters.
