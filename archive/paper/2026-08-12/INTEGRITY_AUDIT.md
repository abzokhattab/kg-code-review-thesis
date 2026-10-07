# Integrity audit — do the paper's numbers add up?

**Date:** 2026-08-12. **Method:** every number the paper intends to cite was
recomputed from the raw artefacts (judge-panel JSON, per-judge vote records,
injection judgment files, evidence packs) and compared against the summary
markdown. Reproduce with:

```
python3 paper/2026-08-12/verify_paper_numbers.py
```

**Result: 91 of 91 checks pass.** On the first pass 56 of 60 passed; the
failures were three documentation defects, none of which changed a single
reported result. Every headline number in both experiments reproduces exactly
from raw data.

The check count grew from 60 to 91 in two steps. First, the corrections in §2
added regression guards so the generator configuration cannot silently revert.
Second, once the paper draft existed, §4 added 27 checks that verify the
numbers **written by hand in the paper's prose** against the same artefacts.
That last part matters: the paper's tables and figure are generated from raw
data and so cannot drift, but prose is typed and can. Both are now covered.

---

## 1. What reproduced exactly

### Experiment 1 (era 2) — `results/checklist_evaluation_llm_multi__v2.json`

Recomputed from the 4 000 individual criterion cells, not from the summary
block:

| Quantity | Documented | Recomputed |
|---|---|---|
| baseline mean total / KG-relevant | 9.20 / 4.97 | 9.200 / 4.975 |
| kg | 9.82 / 5.58 | 9.825 / 5.575 |
| rag | 10.07 / 5.40 | 10.075 / 5.400 |
| hybrid | 9.93 / 5.50 | 9.925 / 5.500 |
| kg Δ vs baseline (total / KG-rel) | +0.62 / +0.60 | +0.625 / +0.600 |
| rag Δ | +0.88 / +0.42 | +0.875 / +0.425 |
| hybrid Δ | +0.72 / +0.53 | +0.725 / +0.525 |
| κ mini↔4o | 0.717 | 0.717 (4 000 cells) |
| κ mini↔gemini | 0.590 | 0.590 (3 836 cells) |
| κ 4o↔gemini | 0.713 | 0.713 (3 836 cells) |

Also verified: 160 evaluations = 40 PRs × 4 modes; 25 criteria per
evaluation; the KG-relevant subset is exactly the pre-registered nine
(F3 F4 T1 T2 T3 M1 M3 C2 Q2); every stored `total_score` and
`kg_relevant_score` equals the sum of its criterion scores; and the
majority-vote rule (ties → 0) is applied correctly in **all 4 000 cells**
with zero deviations.

Win attribution (`results/KG_WIN_ATTRIBUTION.md` §1) reproduces exactly:
KG-relevant band 42W/18L, net **+24**; non-KG band 34W/33L, net **+1**. This
is the strongest single piece of mechanism evidence in Experiment 1 and it
holds.

RAG floor effect (`results/FINAL_RESULTS_REPORT.md` §Finding 1): Spearman
r = **−0.577** on n=40 — reproduces to three decimals.

### Experiment 2 — injection study

Detection counts were recomputed **from the individual judge verdict files**
(majority of 3, ties → 0), independently of the harness's own aggregation.
All six arms match:

| Arm | Documented | Recomputed from judge votes |
|---|---:|---:|
| baseline | 0/28 | 0/28 |
| rag | 1/28 | 1/28 |
| hybrid | 12/28 | 12/28 |
| kg (deployed Joern) | 15/28 | 15/28 |
| kg_joern_inherit | 21/28 | 21/28 |
| kg_idealised | 26/28 | 26/28 |

Also verified: n=40 = 28 structural + 12 local control; manifest band mix
`{L1 6, L2 6, S1 9, S2 9, S3 1, S4 6, S5 3}`; the S4 inheritance claim
(deployed kg **2/6** vs kg+inheritance **5/6**, Δ +0.50); placebo parity
kg−baseline on local bands = **−0.0833**, inside the pre-registered
[−0.15, +0.15] window; local-control detection 0.83–1.00 across all arms;
kg−baseline structural = +0.5357, p < 0.0001; inheritance gain +0.2143,
p = 0.07145.

Judge validation arithmetic also checks out: 168 = 28 structural × 6 arms,
and 121/135/156 of 168 give 72 % / 80 % / 93 %. The claim of zero
"detected-without-mention" flags for both OpenAI judges is accurate (Gemini
has 5).

### Dataset

The scored sample is exactly 40 PRs, every one has an evidence pack, and the
repo mix is exactly as documented: grafana 13, kafka 8, scikit-learn 8,
godot 6, jenkins 5. Generated reviews: 160 files, 40 per mode.

### Builder sensitivity (Joern) — better than expected

`results/BOOTSTRAP_STATS_joern.md` reproduces (kg Δ total **+1.171**,
KG-relevant **+0.686** on n=35), and two things came out *in the paper's
favour*:

- **The judge panel is the same as era 2** (gpt-4o-mini, gpt-4o,
  gemini-2.5-flash), despite `results/ERA_GUIDE.md` and
  `reports/2026-07-13/ERA_DECISION_MEMO.md` both stating that era 3 changed
  the panel to gpt-4o + gemini-2.5-flash + gemini-2.0-flash. That claim
  describes the *other* Joern analysis (the re-based /6 one in
  `FINAL_RESULTS_REPORT.md`), not this file. So the grep-vs-Joern builder
  comparison holds the panel constant.
- **It is scored on the original 25-criterion rubric** (/25 and /9), so no
  post-hoc re-basing is involved.

One caveat to state in the paper: in this file **only the `kg` arm is
Joern-built**. Its own metadata says the baseline/rag/hybrid arms were
"carried from grep headline ... (rag/hybrid are NOT Joern-built)" and that
"clean comparison is baseline vs kg". `BOOTSTRAP_STATS_joern.md` does **not**
disclose this — it presents all four modes as if they were one run. The
paper must cite only the baseline-vs-kg contrast from it, and say so.

---

## 2. Issues found

### I1 — Generator temperature was misdocumented — FIXED 2026-08-12

**Severity: high** — it is a reproducibility claim a reviewer can check.

**Outcome: the two experiments run at different temperatures, and neither is
0.4.** Experiment 1 generates at **T = 0.0**; Experiment 2 generates at
**T = 0.3**, hardcoded. Both were documented as 0.4. Corrected in
`thesis-context/CLAUDE.md` (rule 7), `thesis-context/CODE_INDEX.md`,
`thesis-context/README.md`, `dataset_v2/docs/STATUS.md` (+ bundle copy),
`results/INJECTION_EXP2_RESULTS.md` (+ bundle copy),
`experiments/2026-07-05_injection_exp2/DECISIONS.md`, and
`reports/2026-07-13/EXPERIMENT_1_SUMMARY.md` (as a dated correction note
rather than a silent edit, since that document was sent to the supervisor).

`thesis-context/CLAUDE.md` §"The thesis in one paragraph" and the
supervisor-facing `reports/2026-07-13/EXPERIMENT_1_SUMMARY.md` both state
generation was **gpt-4o, T = 0.4, seed = 42**. The code and artefacts say
otherwise:

| Evidence | Says |
|---|---|
| `dataset_v2/scripts/regenerate_reviews_v2.py` arg default | `--temperature` default **0.0** |
| same file, docstring line 24 | "reviews on gpt-4o @ **temperature 0**" |
| `prnote/llm.py:32` | `temperature: float = 0.0` |
| `results/checklist_evaluation_llm_multi__joern.json` metadata | `"generator": "openai:gpt-4o T=0.0"` |
| `results/DATA_MANIFEST.md:39` (v1 reviews) | "generated with gpt-4o @ temperature 0.0" |

There is **no run log for the canonical generation** — `logs/` contains only
the 2026-05-13 scoped-AST sensitivity pipeline, and that one *did* run at
T = 0.4 (`logs/step3_regen.log`, output dir
`outputs/luca_prs_v2_scoped_ast`, 2 modes, 80 reviews). So T = 0.4 was in use
somewhere in that era, which is probably how it got into the prose — but it
was the sensitivity variant, not the headline run.

**Best available reading: the canonical 160 reviews were generated at
T = 0.0.** The Joern run records `T=0.0` explicitly, so the grep-vs-Joern
builder comparison is temperature-matched, which removes the confound I
flagged mid-audit. Caveat to keep in mind: because no run log survives for
the canonical generation, T = 0.0 rests on the pipeline default plus the
script's own docstring rather than on a recorded invocation.

**Experiment 2 is a separate and unambiguous case.** It generates through
`prnote/note.py::generate_review_direct`, which **hardcodes
`temperature=0.3`** and exposes no temperature parameter, so no invocation
could have produced 0.4. Verified by parsing the AST of that function. The
same function truncates the diff at 12 000 characters; this is not binding
for Experiment 2, where an injected-defect diff is a few lines, but it is
worth stating because Experiment 1 used a 50 000-character cap.

No result changes from either correction: every mode within a run shared the
same setting, so all contrasts are internally valid.

### I2 — The documented generation seed was never sent to the API — FIXED

**Severity: medium** (reproducibility wording).

"seed = 42" appears in the canonical paragraph and the supervisor summary,
but no `seed=` argument is passed to any model call anywhere in `prnote/`
(the only `random.seed` is in `prnote/rag.py:133`, for chunk sampling). The
**statistics** seed 2026 is real and correctly used by the bootstrap and
permutation code.

"seed = 42" has been removed from the generation descriptions. The paper will
state that generation was not seeded and that determinism for Experiment 1
rests on T = 0.0. Seed 2026 remains, correctly, as the bootstrap and
permutation seed.

### I3 — "Django" was listed as a dataset repository — FIXED

**Severity: medium** (a committee member would catch it immediately).

`thesis-context/README.md` §Dataset listed the five repositories as "Apache
Kafka, Django, Grafana, scikit-learn, Jenkins/Grafana go". Django is not in
the dataset; the audit resolved the true mix from the evidence packs as
grafana 13, kafka 8, scikit-learn 8, godot 6, jenkins 5. Corrected, with the
counts included so the line is self-checking. (`STATE_OF_THE_THESIS.md` §2.3
believed this error had already been fixed everywhere; it had only been fixed
in `CLAUDE.md`.)

### I4 — One extra evidence pack, explained not orphaned

**Severity: cosmetic.**

`data/luca_prs_v2/` holds 41 packs. `pr50_evidence.json` was built on
2026-07-13 by the Joern "Option B" out-of-dataset probe
(`experiments/2026-05-15_joern_kg_main/progress.json` records `cpg_pr50`
through `evidence_pr50`), so it is deliberately outside the scored 40 and has
no generated reviews. Left in place; the audit now asserts that the only
extra pack is this known one, which guards against a future stray pack
silently entering a directory glob.

---

## 3. Not verifiable from artefacts

- **The "RAG 5/28" figure** you mentioned from an independent run. Every
  artefact says 1/28 and no file in the repository contains 5/28. Cannot be
  cited until the run's output exists.
- **p-values and bootstrap CIs** were not re-derived; I verified the point
  estimates, the n's, the vote aggregation, and the two correlation/κ
  statistics. Re-running B = 20 000 permutations was out of scope for a
  first pass and the stats code is seeded and deterministic.
- **The re-based /6 Joern numbers** (`+1.743/6`) were not audited, because
  the plan excludes them from the paper.

---

## 4. Paper prose verification (added 2026-08-12, after drafting)

`audit_paper_prose()` reads `paper/2026-08-12/draft/main.tex` and re-derives
every quantitative claim in the running text. It covers the six structural
detection counts, the kg contrast and its interval, the placebo delta, the
four win-attribution nets, the aggregate delta range, three quoted $p$-values,
both builder-sensitivity movements, the three inter-judge kappas and the
Gemini judge's usable cell count, the three judge-validation percentages, and
the five per-repository pull request counts. It also re-asserts the bans
inside the paper itself: no era-1 numbers, no 25-PR dataset, no 14-criterion
rubric, no `+1.743`, no generation seed, and no citation placeholder left in
body text rather than in a comment.

Two claims in the prose are deliberately *not* machine-checked because they
are qualitative readings rather than numbers: the characterisation of the
kappa values as "substantial for two pairs and moderate for the third", and
the statement that the Java repository's misses included cases where the
correct edges were present. Both trace to
`experiments/2026-07-05_injection_exp2/out/RESULTS.md` and
`results/INJECTION_EXP2_RESULTS.md` §"Honest notes".

## 5. Bottom line

The data adds up. Both experiments' headline numbers survive recomputation
from raw votes, the placebo and control bands behave as pre-registered, the
mechanism evidence (win concentration, S4 inheritance, local-band parity) is
intact, and the dataset composition is exactly as claimed.

Everything that was wrong was documentation, and all of it is now corrected:
the generation temperatures (I1), the generation seed (I2), and the Django
repository error (I3). One disclosure sentence still has to make it into the
paper's prose — that in the Joern file only the `kg` arm is Joern-built, so
only the baseline-versus-kg contrast may be cited from it.

**Configuration the paper's Methods section must state:**

| | Experiment 1 | Experiment 2 |
|---|---|---|
| Generator | gpt-4o | gpt-4o |
| Temperature | 0.0 | 0.3 (hardcoded) |
| Generation seed | none sent | none sent |
| Diff cap | 50 000 chars | 12 000 chars (not binding) |
| Judges | gpt-4o-mini, gpt-4o, gemini-2.5-flash | same three |
| Aggregation | majority of 3, ties → 0 | majority of 3, ties → 0 |
| Stats seed | 2026 | 2026 |
