# Human-eval pilot — clean Joern + normal prompt (2026-06-11)

**Status:** side-by-side pilot. Not deployed. Not connected to the live
Google Sheet. Run locally to decide if this design is better than the
strict-prompt study in `human_eval_v3/`.

---

## What's different from `human_eval_v3/`

| | `human_eval_v3/` (live, strict) | This folder (pilot, clean) |
|---|---|---|
| KG arm | `joern` under STRICT prompt | `joern_normal` under SYSTEM_PROMPT_KG |
| Baseline arm | `baseline_strict` (strict prompt, no KG) | `baseline` (normal prompt, no KG) |
| Aligns with thesis headline? | No (prompt confound) | **Yes** (same prompt as the n=35 clean Joern run) |
| LLM-judge KG-rel d_z | +1.34 (inflated) | +0.58 (clean) |
| 6 PRs, KG-rel W/T/L distribution | 2W/2T/2L drawn from a 31W/4T/0L pool | 2W/2T/2L drawn from a 21W/8T/6L pool |
| Webhook → Google Sheet | Live | **Disabled** (backup-only) |
| `localStorage` namespace | `heval4_*` | `heval5c_*` (separate, no collision) |

The reviews in this pilot are visibly less templated — the strict-prompt
study forced both arms into the same 9-section scaffold, which is why
raters reported "the reviews are similar." Under the normal prompt, the
two arms diverge in prose and structure, so unique-sentence highlighting
in the UI actually has something to shade.

## The 6 PRs

Source run: `experiments/2026-06-11_joern_normal_prompt/`

| PR | Repo | Δ KG-rel | Δ Total | Role |
|---:|---|---:|---:|---|
| 31 | scikit-learn | +3 | +4 | Large win |
| 15 | grafana | +3 | +3 | Large win |
| 22 | kafka | +1 | +3 | Small win, big total |
| 38 | grafana | +1 | 0 | Near-tie |
| 47 | jenkins | −1 | 0 | Small loss |
| 20 | grafana | −2 | −3 | Large loss |

4 of 6 (31, 22, 38, 47) overlap with the strict-prompt study; their KG-arm
review *content* is regenerated, but PR metadata + diff + body + baseline
text are reused (verified the same).

Length-ratio sanity check (joern_normal / baseline characters):

```
PR15: 1.38   PR38: 1.18   PR22: 1.15   PR20: 1.14   PR47: 1.11   PR31: 1.09
```

Five of six pass the pre-registered length-disparity threshold (<1.2×).
PR15 is over because Joern actually finds more callers there — that's
signal, not noise, but flag it in the length-controlled sensitivity.

## Run locally

```bash
cd human_eval_v3_clean_2026-06-11/
python3 -m http.server 8000
# open http://localhost:8000/
```

Responses go to `localStorage` and the "Download my responses (.json)"
button on the completion screen. Nothing is uploaded.

## Files

| Path | What |
|---|---|
| `index.html` | Copy of `human_eval_v3/index.html` with namespace + webhook patched |
| `study_data.json` | 6 PRs × 2 modes (`baseline`, `joern_normal`) |
| `README.md.original` | Original `human_eval_v3/README.md` for reference |

## Decision pending

Try this side-by-side against the live study (open both, rate the same
PR in each). If the differences are easier to spot here, replace
`human_eval_v3/study_data.json` and update `docs/ANALYSIS_PLAN.md` §1
to point the comparison at `baseline` (normal) vs `joern_normal`.
