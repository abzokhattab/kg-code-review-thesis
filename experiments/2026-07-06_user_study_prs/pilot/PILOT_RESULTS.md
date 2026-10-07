# Pilot run — 2026-07-06 (rater: `pilot_agent`, EXCLUDE from analysis)

> **Superseded evidence aid:** this excluded AI pilot used green `verified`
> badges that later source audit found conflated module imports with behavioral
> affectedness. Its preferences are not an expected-effect estimate for the
> final neutral-evidence instrument and must not drive PR selection.

> Note: the scripted UI run covered the first 4 PRs (101–104). PRs 105 and
> 106 were added afterwards and judged by the same assistant directly on the
> review texts + answer key + source verification (not via the UI); appended
> below on 2026-07-06 so all 6 stimuli have a pilot judgment.

Completed by the research assistant (AI) to validate the instrument, not a
human subject. Sheet rows are tagged `study_id=human_eval_pilot_py_v1`,
`rater_id=pilot_agent`. Raw ratings: `pilot_agent_responses.json`.

## Verdict: the instrument works

- Full flow runs end to end: welcome → consent → demographics → briefing →
  tasks (4 PRs) → feedback → completion. No UI errors.
- Every criterion was **answerable without codebase knowledge**. The deciding
  evidence in 3 of 4 PRs was the file-reference answer key: the green
  "verified" badges made the KG review's off-diff references trustworthy at a
  glance, which was exactly the failure mode of the v3 study (raters could
  not check reference claims in sklearn/kafka/jenkins).
- Difficulty self-ratings: 2, 2, 3, 3 of 5 — vs. "really hard to answer and
  follow" on the v3 stimuli.

## Blind judgments (mode revealed post hoc)

| PR | overall winner | deciding factor |
|---|---|---|
| flask #5637 | **kg** | verified off-diff dependents (logging.py, sessions.py) + concrete test-file suggestion |
| click #3493 | **kg** | verified callers (core.py, termui.py); baseline had a dubious match-statement/Python-version claim |
| requests #7433 | **kg** | verified callers (sessions.py, api.py); reviews otherwise near-identical |
| requests #7328 | **tie** | baseline named concrete test functions from diff context; kg named verified dependents — offsetting strengths |
| flask #5799 | **kg** | `templating.py` is a direct caller (`stream_template` wraps `stream_with_context`) — the single most useful pointer in either review; `blueprints.py` ref is hedged/weaker |
| click #3578 | **kg** (weakest win) | `types.py` ref is load-bearing (`Choice.get_metavar` produces the brackets `make_metavar` double-wrapped); but `parser.py` ref is padding — real file, no metavar involvement |

Full-6 tally: **kg 5, tie 1, baseline 0** on overall preference; criterion-level
wins still concentrate on F3*.

## Additional observation from source-verifying PRs 105/106

The "verified" badge guarantees the file exists and imports the changed
module — it does NOT guarantee the *stated relationship* is precise. Two KG
references embellish the mechanism ("`parser.py` relies on metavar
formatting" — it doesn't; "`blueprints.py` may use `stream_with_context`" —
module-level import only). The badge legend and rater instructions already
say "imports/uses the changed code", which is accurate; but analysis of the
"why" texts should check whether raters over-credit embellished relationship
claims. Worth one sentence in the thesis limitations.

Per-criterion pattern: kg wins concentrate on F3* (components/APIs affected),
exactly the criterion family the 40-PR LLM-judge experiment found KG-sensitive.
Convergent, but n=1 non-independent rater — directional only.

## Observations for the real study

1. PR 104 (requests #7328) is the "hard tie" stimulus — good to keep, it
   tests whether raters use "about the same" honestly.
2. The baseline review for click #3493 contains a plausible-but-dubious claim
   (match statements failing on "older Python"). Consider whether to keep it
   (realistic LLM behavior worth measuring) — recommend keep.
3. Average task time will be well above the 7 s/PR of this scripted run;
   budget the advertised 15–20 min.
