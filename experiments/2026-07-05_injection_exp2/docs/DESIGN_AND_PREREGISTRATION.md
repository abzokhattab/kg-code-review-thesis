# Experiment 2 — Controlled cross-file defect injection

**Status:** DESIGN + PRE-REGISTRATION (no code, no API calls yet).
Decisions in §13 need user sign-off before the harness is built.
**Date:** 2026-07-05.
**Folder:** `experiments/2026-07-05_injection_exp2/`.

**Why this document exists.** This is the pre-registration that protects
Experiment 2 from the same "you cherry-picked / you rigged it" objections
that `dataset_v2/docs/SELECTION_v2.md` and
`human_eval_v3/docs/ANALYSIS_PLAN.md` protect Experiment 1 from. Every
decision rule below is fixed *before* any injection is generated or judged.

---

## 1. What this experiment is (and is not)

### Is
A **second, co-equal experiment** for the thesis, complementary to the
40-PR rubric study (Experiment 1). It measures, under **known ground
truth**, whether repository context lets an LLM reviewer detect a
*hidden, cross-file* defect that the diff alone does not reveal.

### Is not
- A replacement for Experiment 1. The 40-PR rubric result remains the
  headline for review *quality*.
- A new research programme. It answers the *same* thesis question
  ("does scoped structural context help LLM code review?") from the
  opposite methodological direction.
- A defect-detection / F1 benchmark that discards the rubric. Detection
  is scored with the **same 3-judge panel** used in Experiment 1, so the
  two experiments compose rather than compete.

### Relationship to the prototype
This scales the finished sandbox probe in
`exceptional test/prototype/` (`FINDINGS_SCALE.md`,
`THESIS_SUBSECTION.md`). The prototype established the mechanism on
**8 rename injections** in one repo; this experiment broadens it into a
defensible experiment (more injections, multiple repos, a defect
taxonomy, and a **control band the KG is expected to lose on**).

---

## 2. Why two experiments is stronger (the triangulation argument)

| | **Experiment 1** — 40-PR rubric | **Experiment 2** — injection (this) |
|---|---|---|
| Validity strength | External (real merged PRs, 5 repos) | Internal (causal, known ground truth) |
| Weakness it carries | No causal proof; rubric = coverage, LLM-judged | Synthetic defects; narrow slice |
| Question | Does context improve review *quality*? | Does context catch a *known hidden* defect? |
| Ground truth | Rubric applied by judges | The injected defect + its dependent sites |

The two experiments cover each other's principal weakness. When an
observational study on real PRs and a controlled study with ground truth
point the same direction, the joint conclusion is substantially harder
to attack than either alone.

---

## 3. Research question

> **RQ2b (causal).** On a defect whose blast radius is *known by
> construction* to be cross-file, does KG-augmented context let the
> reviewer name the true dependent breakage that a diff-only baseline
> cannot see — and does this advantage **disappear on local defects**,
> as a complementarity account predicts?

The second clause is the credibility clause. A KG that "wins everywhere"
would be suspicious; the pre-registered prediction is that KG wins on
the cross-file bands and is **at parity on the local-defect control
band**.

---

## 4. Defect taxonomy (the core credibility device)

Injections are stratified into **structural** bands (KG is hypothesised
to help) and a **local control** band (KG is hypothesised *not* to help).
The local band is not a throwaway — it is the placebo that shows the
result is a genuine structural effect, not a "more context always scores
higher" artefact. This mirrors the placebo-band logic already used in
`scripts/attribute_kg_wins.py` (Experiment 1).

| Band | Operator | Edit site | Breaks at | Edge a reviewer must traverse | KG hypothesis |
|---|---|---|---|---|---|
| S1 | symbol rename | file A | importers of A | `IMPORTS` | KG wins |
| S2 | function signature change | file A | callers in file B | `CALLS` | KG wins |
| S3 | return-type / contract change | file A | consumers in file B | `CALLS` + dataflow | KG wins |
| S4 | base-class / mixin change | file A | subclasses in file B | `INHERITS_FROM` | KG wins **iff** inheritance edges present |
| S5 | import removal / relocation | file A | modules importing A | `IMPORTS` | KG wins |
| **L1 (control)** | off-by-one / wrong operator | file A | **same file A** | none (local) | **parity — KG should NOT help** |
| **L2 (control)** | removed null / bounds check | file A | **same file A** | none (local) | **parity — KG should NOT help** |

S4 is deliberately included because the prototype showed the **deployed
Joern KG is blind to inheritance edges** (`FINDINGS_SCALE.md` §CRITICAL):
every Joern miss was a base-class/mixin rename. S4 is where the
inheritance-edge augmentation (§8) is expected to move the needle.

Operators are drawn from the mutation-testing literature (PIT / Major /
Defects4J-style) so the "are these defects realistic?" objection has a
cited answer. `[TODO: confirm we cite the mutation-testing operator
source in bibliography.bib]`

---

## 5. Injection targets — repos, languages, counts

Injections are auto-discovered by AST (top cross-file-fanout symbols),
not hand-picked, extending the `run_scale.py` auto-discovery to more
repos. All repos are already cloned at their PR-head SHAs
(`luca_repos/`), matching Experiment 1's substrate.

**Target (subject to §13 sign-off):**

| Repo | Language | Structural injections (S1–S5) | Local control (L1–L2) |
|---|---|---:|---:|
| scikit-learn | Python | 12 | 4 |
| apache/kafka | Java | 12 | 4 |
| grafana | Go/TS | 12 | 4 |
| **Total** | | **36** | **12** |

- **N = 48** injections total (36 structural + 12 control).
- 3 languages → guards against a Python-only artefact (the prototype was
  scikit-learn only).
- Per-band N within each repo is balanced as far as the AST-discovered
  symbol supply allows; shortfalls are reported, not back-filled by
  hand. `[TODO: confirm 48 is the right N given the ~$ / time budget —
  see §12]`

Selection is **direction-blind**: targets are chosen by structural
fanout *before* any review is generated, identical in discipline to
`dataset_v2/docs/SELECTION_v2.md`.

---

## 6. Ground truth and oracle

For each injection the manifest records (extending the prototype's
`out/manifest.json` schema):

- edit site (file, symbol, operator),
- the **true dependent sites** (AST-resolved `ImportFrom` / call edges),
- the KG edge type a reviewer must traverse to reach them,
- the detection criterion (a review "detects" iff it names ≥ 1 true
  dependent breakage, judged by the panel).

**Two-tier ground truth:**
1. **Structural (all injections).** AST-verified real dependents exist.
   This is the minimum bar and is deterministic.
2. **Behavioural oracle (where feasible).** The injected defect provably
   breaks a test / import, c-CRAB-style — as done in the toy repo
   (`toy_repo/check.py`). For large repos where running the full suite
   is impractical, we record whether an oracle was obtained per
   injection and report the coverage honestly. `[TODO: decide oracle
   scope — see §13]`

---

## 7. Modes compared

To keep Experiment 2 directly comparable to Experiment 1, the **primary
comparison uses the same four deployed modes**:

- `baseline` (diff only)
- `kg` (deployed **Joern CPG** builder — the same one behind the 40-PR
  headline)
- `rag` (thesis-faithful `top_k = 10`, query = first 2 KB of changed file)
- `hybrid` (Joern KG + RAG)

Two **ablation arms** (secondary, for the mechanism story):

- `kg-idealised` — symbol-level AST import resolver (the 8/8 ceiling in
  the prototype). Shows the gap between deployed and ideal.
- `kg-joern+inherit` — **the augmentation**: deployed Joern KG plus
  statically-resolved `INHERITS_FROM` and import edges. Pre-registered
  prediction: recovers the S4 (inheritance) band that plain Joern misses,
  moving deployed KG toward the ceiling. This is the concrete engineering
  contribution of Experiment 2.

Generator held fixed at **gpt-4o, T = 0.4, seed = 42** (matches
Experiment 1). Prompts are the production `prnote` templates.

---

## 8. Metric and scoring

- **Detection** per (injection × mode): binary, majority of the same
  3-judge panel (`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`), ties → 0
  (strict side, matching Experiment 1's aggregation rule).
- Judges are asked only whether the review names a genuinely broken
  dependent file/symbol for that injection. Per-judge verdicts are
  stored so results can be re-aggregated under any rule.
- **Primary endpoint:** detection rate per mode, reported **separately
  per band** (structural S1–S5 vs local control L1–L2).

---

## 9. Objective judge validation (bonus — de-risks RQ3)

Because the ground truth is known, Experiment 2 **also validates the LLM
judge without humans**: we compare each judge's detected/not-detected
verdict against the manifest ground truth and report accuracy /
false-positive rate per judge. This is an objective complement to the
human-study judge validation (RQ3) and reduces the thesis's dependence
on the stalled human study.

---

## 10. Pre-registered decision rules

Fixed before any data is generated. Detection rate = fraction of
injections in a band a mode detects.

### 10.1 Primary (structural bands, KG vs baseline)
| Outcome | Verdict |
|---|---|
| `kg` detection − `baseline` detection ≥ +0.30 on structural bands, paired perm p < 0.05 | **Supports RQ2b** — structural context catches hidden cross-file breakage |
| +0.10 ≤ Δ < +0.30, or p ≥ 0.05 | **Weak / underpowered** — report Δ + CI, discuss N |
| Δ < +0.10 | **Null** — reported honestly as a negative result |

### 10.2 Control-band sanity (the credibility check)
| Outcome | Verdict |
|---|---|
| On L1–L2, `kg` − `baseline` detection ∈ [−0.15, +0.15] | **Expected** — confirms the effect is structural, not a context-volume artefact |
| `kg` beats `baseline` on local defects by > +0.15 | **Red flag** — the KG advantage is not purely structural; investigate and report (possible verbosity/context artefact) |

### 10.3 Inheritance-edge augmentation (S4 band)
| Outcome | Verdict |
|---|---|
| `kg-joern+inherit` − `kg` (Joern) ≥ +0.30 on the S4 band | **Supports the engineering contribution** — inheritance edges recover the blind spot |
| smaller | report as-is; the blind spot is intrinsic or the model under-uses the edge |

### 10.4 RAG contrast
Report RAG detection and, as in the prototype, the **retrieval
diagnostic** (how many true dependents RAG surfaced, e.g. the prototype's
3/24) so a RAG miss is shown to be a ranking/completeness limit, not a
config artefact.

---

## 11. Statistical plan

Identical machinery to Experiment 1 (`scripts/bootstrap_stats.py`):
- Bootstrap 95 % CIs (B = 10 000) on per-mode, per-band detection rates.
- Paired permutation tests (B = 20 000, seed = 2026) for `kg` vs
  `baseline`, `hybrid` vs `baseline`, and `kg-joern+inherit` vs `kg` on
  the S4 band.
- All numbers reported **per band**; no aggregate that hides the local
  control band.

---

## 12. Cost / wall-clock / files (pre-flight — NOT yet run)

Per the lab pre-experiment checklist. **No API call is made until this
summary is confirmed with real numbers at run time.**

```
Estimated cost:      ~$15–30  [TODO: confirm at harness-ready time]
                     (48 injections × 6 arms × 3 judges generation+judging;
                      RAG index builds are $0 embeddings-cached where possible)
Estimated wall-clock: ~2–4 h  [TODO: confirm]
Will create:         experiments/2026-07-05_injection_exp2/{manifest.json,
                     mutants/, diffs/, reviews/, results/, RESULTS.md}
Will read:           luca_repos/{scikit-learn,kafka,grafana} at PR-head SHAs;
                     prnote/ pipeline; deployed Joern KG builder
Will overwrite:      nothing outside this dated folder
Idempotent:          yes — skips injections/reviews already on disk,
                     resumes through 429s (same discipline as
                     dataset_v2/scripts/regenerate_reviews_v2.py)
```

Nothing outside `experiments/2026-07-05_injection_exp2/` is touched. The
real `data/` and `results/` of Experiment 1 are never written.

---

## 13. Open decisions needing sign-off

1. **N and split.** 48 total (36 structural + 12 control) across 3 repos
   — or larger/smaller? (Drives cost in §12.)
2. **Repos.** scikit-learn + kafka + grafana — or a different trio?
   (Joern support per language must be confirmed; the deployed builder
   was validated on the 40-PR set.) `[TODO: confirm Joern coverage for
   Go/TS in grafana]`
3. **Behavioural oracle scope.** Structural-only ground truth (cheap,
   deterministic) vs. also running tests to confirm breakage (stronger,
   slower, flaky on big repos). Recommend: oracle where a targeted test
   exists; structural elsewhere; report coverage.
4. **Ablation arms.** Include both `kg-idealised` and
   `kg-joern+inherit`, or only the augmentation?
5. **Human study (RQ3).** Recommended: downgrade to a supporting
   judge-validation check (Experiment 2 now validates the judge
   objectively). Confirm you are content to *not* invest further in the
   rater-UX problem for now.

---

## 14. What we will NOT do (anti-goalpost-moving)

- Not drop the local control band after seeing results.
- Not drop a defect band or repo from the headline after seeing
  per-band breakdowns.
- Not re-tune the RAG or KG builder after seeing detection numbers
  (the deployed config is frozen to match Experiment 1; the augmentation
  arm is a *pre-declared* ablation, not a post-hoc fix).
- Not report a structural-only aggregate that hides the control band.

---

## 15. Prototype evidence this builds on

From `exceptional test/prototype/FINDINGS_SCALE.md` (8 rename
injections, scikit-learn, 3-judge panel — the mechanism this experiment
scales):

| Mode / builder | Detection (n = 8) |
|---|---|
| baseline (diff only) | 0/8 |
| rag (top_k = 10) | 1/8 |
| KG — grep-stem | 2/8 |
| KG — Joern CPG (deployed) | 4/8 |
| KG — idealised import-level | 8/8 |

Key prototype finding this experiment is designed to confirm at scale
and across languages: **detection tracks whether the builder supplied a
true dependent**, and the deployed Joern KG's misses are all
**inheritance** edges it does not encode.

---

## 16. Pipeline stages (for the harness, once §13 is signed off)

```
A. discover_targets.py   AST auto-discovery of top-fanout symbols per repo,
                         stratified into S1–S5 + L1–L2         ($0)
B. inject.py             apply operators, write manifest + mutants + diffs,
                         verify each defect (structural + oracle where avail) ($0)
C. run_modes.py          generate baseline/kg/rag/hybrid (+ ablation arms)
                         reviews via prnote for each mutant PR   (paid)
D. judge.py              3-judge detection scoring, per-judge stored (paid)
E. stats.py              per-band bootstrap CIs + paired perm tests ($0)
                         → RESULTS.md + results.json
F. validate_judge.py     judge verdicts vs manifest ground truth  ($0)
```

Scripts land in this folder; any promoted to reusable go to `scripts/`
with a one-line `CODE_INDEX.md` entry per lab rule.
