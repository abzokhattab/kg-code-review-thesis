# Pre-registration — scrambled-neighbourhood controls for the KG arm

**Written:** 2026-09-06, before any scrambled evidence pack, review or judge
verdict exists.
**Author:** lab run on `/Users/akhattab/ai`.

Everything below is fixed before data collection. Nothing in this file may be
edited after the first review is generated; corrections go in a dated addendum
at the bottom.

---

## 1. Question

Experiment 1 found that inserting a knowledge-graph block raises rubric
coverage on the nine KG-relevant criteria (Δ +0.60 /9, p = 0.007, d_z +0.47,
n = 40, `results/BOOTSTRAP_STATS_v2.md`). Two things about that effect are
still unexplained.

**Which section carries it?** The block renders three lists: changed files,
related tests, and files that depend on the changes. An ablation was attempted
on 2026-03-05 (`results/ablation_report.md`) and cannot be used: removing tests
*and* dependencies together scored a smaller drop (6.6%) than removing tests
alone (10.6%), which is impossible for real additive effects, and the run
carried no significance test, used a single `gpt-4o-mini` judge, and sat on the
superseded v1 25-PR dataset with an older rubric. It is an Era-1 artefact.

**Does relatedness matter at all?** Three builders spanning a very wide
precision range produce the same effect:

| Builder | Dependency-edge precision | Total Δ |
|---|---:|---:|
| lexical basename grep (headline) | 10.2% | +0.62 |
| unscoped tree-sitter AST | 86.6% | ±0 vs grep (`results/ast_vs_grep_comparison.json`) |
| Joern code property graph | program analysis | +0.63 (`results/BOOTSTRAP_STATS_joern_parity.md`) |

Precision measured in `results/BUILDER_VOLUME_PRECISION.md`. Every one of those
arms contained genuinely related content. The empty-KG control
(`results/KG_EMPTY_PRIMING_CONTROL.md`) contained none, but also removed the
block's volume. **No existing arm holds volume constant while removing
relatedness.**

Both questions are answered by the same manipulation.

## 2. Manipulation

Two new arms. Each takes the v2 evidence pack and replaces **one** rendered
list with the same number of randomly drawn files from the same repository.

| Arm | List replaced | List left intact |
|---|---|---|
| `scrambled_deps` | `dependent_files` | `nearest_tests` |
| `scrambled_tests` | `nearest_tests` | `dependent_files` |

Held constant against the real arm, per pull request:

* the number of paths the formatter displays in the replaced section;
* the file-extension multiset of that displayed list;
* every other section of the block, byte for byte;
* the system prompt, user-prompt template, diff, PR title and body.

Excluded from the draw: the pull request's changed files, its true
`dependent_files`, its `nearest_tests`, and any path already drawn. Draws come
from the repository's tracked files at the checkout used to build the pack.
For `scrambled_tests` the draw is restricted to paths that look like tests by
the same conventions the builder uses, so the section remains plausible.

Seed: **2026**, fixed here. The draw is deterministic given the seed.

Deleting a section was rejected as the manipulation because it shortens the
prompt, which would confound information loss with prompt shortening — an
effect reported in the 2026 context-layer literature and a likely contributor
to the incoherence of the March ablation. Scrambling holds length fixed, so
relatedness is the only factor that varies.

## 3. Eligibility, fixed now

Scrambling an empty list is a no-op, so each arm is restricted to pull requests
whose **rendered** v2 block actually populates the section that arm replaces.
Both sets are computed from committed data before any new data exists, and are
restricted to the locked 40-PR list in `dataset_v2/docs/SELECTION_v2.md`.

`scrambled_deps` — **n = 31**:
```
2, 3, 6, 8, 10, 14, 15, 18, 19, 21, 22, 23, 24, 27, 28, 29, 31, 32,
33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 47, 48
```

`scrambled_tests` — **n = 26**:
```
2, 3, 6, 8, 9, 10, 14, 15, 18, 19, 21, 22, 23, 24, 27, 28, 31, 33,
36, 37, 38, 40, 41, 44, 47, 48
```

The real arm is regenerated over the union of the two sets, **n = 32**.

The two arms are analysed on their own sets rather than on the 25-pull-request
intersection, because each is a separate paired contrast and intersecting would
discard power for no inferential gain.

**Neither list may grow.** No pull request may be added after data collection
for any reason, including a near-threshold p-value.

## 4. Endpoints

Two primary contrasts, each a paired per-pull-request difference against
`kg_real_fresh` generated in the same batch:

* **P1** `kg_real` − `scrambled_deps`, KG-relevant subscale (/9), n = 31.
* **P2** `kg_real` − `scrambled_tests`, KG-relevant subscale (/9), n = 26.

Each is also reported on the **total scale (/25)** as a secondary endpoint.
Four tests in all; p-values are Holm-corrected across the four. The two
KG-relevant contrasts govern the conclusions.

**Not endpoints, reported descriptively only:** per-criterion movement, review
length, each arm's difference against the cached baseline, and the comparison
between P1 and P2 magnitudes.

## 5. Statistical plan

* Paired two-sided permutation test, sign-flip over pull requests,
  B = 200 000, seed 2026 — matching `scripts/bootstrap_stats.py`.
* 95% bootstrap CI on each paired mean, B = 200 000, same seed.
* Cohen's d_z.
* α = 0.05 after Holm correction across the four tests.
* One analysis, run once, after all 89 reviews and all 267 judge verdicts are
  complete. No interim looks, no optional stopping.

Generator: `gpt-4o`, temperature 0.0, one draw per cell. Judges: the canonical
panel `gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`, majority of three, ties to 0.

**Power**, simulated at the observed paired sd of each eligible set:

| Contrast | n | sd | whole effect | three quarters | half |
|---|---:|---:|---:|---:|---:|
| P1 dependencies | 31 | 1.15 | 93% | 73% | 40% |
| P2 tests | 26 | 1.30 | 88% | 63% | 35% |

Adequate for the primary hypothesis and, importantly, adequate for a null to be
interpretable. This is why these contrasts are funded and the field-level 2×2
ablation is not: that design reached only 27% power for a plausible component
effect, so its null would have carried no information.

## 6. Interpretation rules

Fixed in advance, per contrast. Whichever obtains is what gets reported.

**Rule 1 — real significantly above scrambled.** That section's relatedness
carries part of the effect. The graph supplies usable content, not merely a
well-shaped block, and the low measured precision of the lexical builder
understates how much of its output does work.

**Rule 2 — indistinguishable.** The effect does not depend on that section's
files being related to the change. Combined with the flat result across three
builders, the mechanism is that a list of repository paths redirects the
model's attention toward ripple effects largely regardless of which paths. This
is the outcome the existing evidence predicts and will be reported as the
mechanism finding, not as a negative result.

**Rule 3 — scrambled significantly above real.** Unexpected. Would indicate
plausible-but-wrong specifics mislead the reviewer more than arbitrary ones do.
Reported as-is, with per-criterion inspection to locate the harm.

**If P1 and P2 disagree**, the section that shows Rule 1 is the one carrying
content value, and that is the answer to the ablation question the March run
failed to deliver. The difference between the two magnitudes is descriptive
only — this design is not powered to test it.

A null under Rule 2 will **not** be described as evidence that the knowledge
graph is useless: the KG arm beats the diff-only baseline either way, and the
empty-KG control already separates the block's presence from its content.

## 7. Secondary analysis, declared in advance

The real arm is regenerated rather than reusing the cached
`outputs/luca_prs_v2/pr*_kg.md`, because those were produced months earlier
against the floating `gpt-4o` alias and drift would confound the controls.

That regeneration yields a free by-product: fresh versus cached scores on
byte-identical inputs measure **single-draw generation noise**. Reported in
`results/GENERATION_VARIANCE.md` as the mean absolute per-pull-request score
difference with a bootstrap CI. It is an estimate from one replicate, not a
variance component, and will be described as such.

## 8. What is produced

```
dataset_v2/docs/PRE_REGISTRATION_scrambled.md    (this file, first)
scripts/build_scrambled_kg_evidence.py
scripts/analyze_scrambled_neighbourhood.py
data/luca_prs_v2_scrambled_deps/pr*_evidence.json    (31)
data/luca_prs_v2_scrambled_tests/pr*_evidence.json   (26)
outputs/luca_prs_v2_scrambled_deps/pr*_kg.md         (31)
outputs/luca_prs_v2_scrambled_tests/pr*_kg.md        (26)
outputs/luca_prs_v2_kg_regen/pr*_kg.md               (32)
results/SCRAMBLED_NEIGHBOURHOOD.{md,json}
results/GENERATION_VARIANCE.{md,json}
```

Nothing existing is overwritten. The headline panel
`results/checklist_evaluation_llm_multi__v2.json` and `outputs/luca_prs_v2/`
are read-only for this run.

Estimated cost ~$9. Idempotent: generation skips existing review files, judging
is cached per review.

---

## Addenda

### 2026-09-06, at build time, before any review was generated

`scrambled_tests` is built on **25** pull requests, not the pre-registered 26.
PR22 could not be built and is dropped.

Cause, recorded in full because it is a deviation. PR22's displayed "Related
Tests" are four `.xml` checkstyle configuration files and two `.yml` GitHub
workflow files — the lexical builder matched them because their filenames
contain the word "test". A fair scramble must draw the same extension multiset
from test-looking paths in the same repository, and `apache_kafka` tracks
exactly four test-looking `.xml` files, all four of which are the true edges and
therefore excluded from the draw. No fair replacement exists.

The alternative — relaxing the extension match or the exclusion rule for this
one pull request — was rejected because it would make the control weaker for
PR22 than for the other 25 in a way that could not be reported in a single
sentence. Dropping it is the honest handling.

No other pull request was affected; `scrambled_deps` built on all 31. The
eligibility rule itself is unchanged and no pull request was added. Power for P2
at n = 25 rather than 26 is 87% rather than 88% for a whole-effect collapse,
which does not change the design's adequacy.

This entry was written before generation started, so it cannot have been
motivated by any outcome.
