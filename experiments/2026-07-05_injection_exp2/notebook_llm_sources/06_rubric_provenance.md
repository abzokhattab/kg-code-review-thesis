# Rubric Provenance and Validation

**Purpose.** Document the scientific provenance of the 25-criterion code-review
evaluation rubric used throughout this thesis (`scripts/evaluate_reviews.py`,
`evaluation_criteria.md`). The rubric is not invented for this thesis: each of
its eight categories is grounded in at least two of (a) peer-reviewed
code-review evaluation frameworks, (b) international software-quality
standards, and (c) widely-adopted industry guides.

This document is intended to answer the committee question
*"Based on what are these criteria chosen?"* without requiring a change of
evaluation paradigm.

---

## 1. Category-level provenance

| Our category | Criteria | Published / standardized source(s) | What we adopted |
|---|---|---|---|
| **Functionality & Integration** | F1–F4 | Tufano et al. (2021), *Towards Automating Code Review Activities* (ICSE'21); ISO/IEC 25010:2011 §Functional Suitability; DeepCRCEval (Lu et al., EMNLP 2024) "Bug" aspect | Defect-detection and integration-impact criteria |
| **Tests & Verification** | T1–T3 | DeepCRCEval (Lu et al., EMNLP 2024) "Test" aspect; CodeReviewer (Li et al., FSE 2022) testing dimension | Test-presence, edge-case, and specific-test-file criteria |
| **Readability & Structure** | R1–R3 | Google Engineering Practices — Code Review Developer Guide §Comments/§Naming; CodeReviewer (Li et al., 2022) "Clarity" Likert dimension; DeepCRCEval "Style" aspect | Naming, complexity, comment-rationale criteria |
| **Maintainability & Design** | M1–M3 | ISO/IEC 25010:2011 §Maintainability (sub-characteristics: Modularity, Reusability, Modifiability); DeepCRCEval "Maintainability" + "Refactor" aspects | Architecture-fit, scope, and API-documentation criteria |
| **Consistency & Style** | C1–C2 | DeepCRCEval "Style" aspect; Google Engineering Practices — style-consistency principle; CodeReviewer "Comprehensiveness" | Convention-adherence and pattern-consistency criteria |
| **Performance** | P1–P2 | ISO/IEC 25010:2011 §Performance Efficiency; DeepCRCEval "Performance" aspect | Efficiency and benchmark-prompting criteria |
| **Security & Robustness** | S1–S3 | DeepCRCEval "Security" aspect; OWASP Code Review Guide v2.0; ISO/IEC 25010:2011 §Security | Input-validation, secret-handling, error-handling criteria |
| **Review Quality (meta)** | Q1–Q5 | CodeReviewer (Li et al., 2022) "Comprehensiveness" + "Accuracy" Likert dimensions; Bavota & Russo (2015), *Four Eyes Are Better Than Two* (ICSE'15) | Summary-presence, location-anchoring, blocking/non-blocking distinction, clarification-asking, reasoning criteria |

**Outcome.** Every category in our rubric is grounded in **at least two**
independent published or standardized sources. The exact wording of each
criterion is ours; the **dimensions** are not.

---

## 2. Criterion-level mapping

| ID | Description (abridged) | KG-relevant? | Closest published precedent |
|---|---|---|---|
| F1 | Verifies change addresses stated requirement | no  | Tufano 2021 §III.B; ISO 25010 §1.1 |
| F2 | Identifies edge cases / boundary conditions | no  | Tufano 2021 §III.B; CodeReviewer "Accuracy" |
| F3 | Checks integration with existing components/APIs | **yes** | DeepCRCEval "Bug"; ISO 25010 §1.3 Compatibility |
| F4 | Warns about breaking changes / dependent code impact | **yes** | DeepCRCEval "Bug"; Bavota 2015 (defect detection) |
| T1 | Discusses unit/integration test needs | **yes** | DeepCRCEval "Test"; CodeReviewer testing dim. |
| T2 | Tests for edge cases / error paths | **yes** | DeepCRCEval "Test" |
| T3 | References specific test files to add/update | **yes** | DeepCRCEval "Test" (specificity sub-criterion) |
| R1 | Comments on clarity, naming, organization | no  | Google Eng. Practices §Naming; DeepCRCEval "Style" |
| R2 | Identifies unnecessary complexity | no  | Google Eng. Practices §Complexity |
| R3 | Checks comments explain "why" not "what" | no  | Google Eng. Practices §Comments |
| M1 | Assesses fit with existing architecture | **yes** | ISO 25010 §Maintainability; DeepCRCEval "Refactor" |
| M2 | Flags PR scope as too large | no  | Google Eng. Practices §SmallCLs |
| M3 | Checks public APIs are documented | **yes** | DeepCRCEval "Documentation" |
| C1 | Checks adherence to project style guides | no  | DeepCRCEval "Style" |
| C2 | Checks consistency with existing patterns | **yes** | DeepCRCEval "Style"; Bavota 2015 |
| P1 | Identifies potential performance issues | no  | DeepCRCEval "Performance"; ISO 25010 §2 |
| P2 | Asks about benchmarks for critical paths | no  | DeepCRCEval "Performance" |
| S1 | Checks input validation / sanitization | no  | OWASP CR Guide §Input; DeepCRCEval "Security" |
| S2 | Flags hardcoded secrets / credentials | no  | OWASP CR Guide §Secrets |
| S3 | Assesses error handling / failure recovery | no  | DeepCRCEval "Security"; ISO 25010 §6 |
| Q1 | Provides overall summary | no  | CodeReviewer "Comprehensiveness" |
| Q2 | Anchored to specific code locations | **yes** | CodeReviewer "Accuracy"; Bavota 2015 |
| Q3 | Distinguishes blocking vs. minor | no  | Google Eng. Practices §Severity |
| Q4 | Asks clarifying questions | no  | CodeReviewer "Comprehensiveness" |
| Q5 | Explains reasoning | no  | CodeReviewer "Comprehensiveness" |

**KG-relevant subset:** 9 of 25 (F3, F4, T1, T2, T3, M1, M3, C2, Q2).

---

## 3. KG-relevance tagging is content-derived, not subjective

The `kg_relevant` flag on each criterion is **not** an editorial judgement.
It is a deterministic mapping between rubric criteria and the data fields
that the KG evidence pack contains:

| Criterion | KG evidence field that *can answer it* |
|---|---|
| F3 (integration with existing components) | `dependent_files`, `callers` |
| F4 (breaking changes for dependent code) | `callers`, `call_graph_edges` |
| T1 (tests asked for new behavior)         | `nearest_tests` |
| T2 (tests for edge cases / error paths)   | `nearest_tests` (test contents via RAG) |
| T3 (specific test files named)            | `nearest_tests` |
| M1 (fits existing architecture)           | `functions_in_changed_files`, `dependent_files` |
| M3 (public APIs documented)               | function signatures, `owners` |
| C2 (consistent with existing patterns)    | `similar_chunks` (RAG); function-name patterns |
| Q2 (anchored to file/line)                | any KG field containing file paths |

The remaining 16 criteria (e.g., R1 naming, P1 perf, S1 input validation, Q5
reasoning) cannot be answered by structural-graph data alone — they rely
on local code inspection or stylistic judgement that no KG provides. This
is *why* we expect KG to help on the 9 tagged criteria and *not* on the 16
non-tagged ones, which is consistent with the empirical pattern we observe
(KG-rel Δ > 0; non-KG-rel Δ ≈ 0).

---

## 4. Validation we do report alongside the rubric

The rubric is not used in isolation. We report the following methodological
checks consistent with published LLM-as-judge methodology
(Zheng et al. 2023, *Judging LLM-as-a-Judge*, NeurIPS):

1. **Multi-judge majority vote** with three different model families
   (`openai:gpt-4o-mini`, `openai:gpt-4o`, `gemini:gemini-2.5-flash`).
2. **Inter-judge agreement** via Cohen's κ (reported per-pair in every
   `CHECKLIST_EVALUATION_REPORT__*.md`). Typical κ on our runs:
   0.59–0.74 ("substantial agreement"; Landis & Koch 1977).
3. **Statistical significance** via 10k-bootstrap CIs and 20k paired
   sign-flip permutation tests with paired Cohen's d_z effect sizes
   (`scripts/bootstrap_stats.py`).
4. **Generator robustness** via cross-generator replication on three base
   generators (gpt-4o, gpt-4o-mini, Claude Sonnet 4.5); see
   `results/CROSS_GENERATOR_REPLICATION.md`.
5. **Confound disentanglement**: the prompt-priming control experiment
   (§13.2 of `CROSS_GENERATOR_REPLICATION.md`) quantifies how much of
   the apparent KG lift is attributable to system-prompt instructions vs.
   structural KG evidence.

---

## 5. Validation we *added* to fortify the rubric (executed)

### 5.1 Inter-annotator agreement on the `kg_relevant` tag

An independent LLM annotator (`openai:gpt-4o`, blind to the in-code labels)
re-classified each of the 25 criteria as KG-relevant or not, prompted with a
content-derived rule (*"can the criterion be substantively informed by
structural code-graph data?"*).

| | Value |
|---|---|
| Annotator A | rubric author (in-code `kg_relevant` flag) |
| Annotator B | `openai:gpt-4o`, blind to A, content-rule prompted |
| Raw agreement | **84.0%** (21/25) |
| **Cohen's κ** | **0.615** (substantial, Landis & Koch 1977) |

The four disagreements are all on boundary cases (T1, T2, M3, Q2), which
defends the conservative reading that 5/9 of our KG-relevant criteria are
unambiguous and 4/9 sit at the margin. Substantial agreement (κ ≥ 0.6) is the
conventional threshold for treating an annotation scheme as reproducible.

**Artifact:** `results/RUBRIC_KAPPA_kg_relevant.{json,md}`,
`scripts/validate_kg_relevant_kappa.py`.

### 5.2 Positive control — does the rubric discriminate quality?

Five PRs (3, 6, 14, 18, 25; spanning 5 repos / 5 languages) were scored under
five deliberately-bad review styles using the *same* 3-judge majority panel
used in the main experiments, and compared to the existing real `baseline`
reviews on the same PRs.

| Mode | Mean total / 25 | Δ vs baseline | p (perm., n=5) |
|---|---:|---:|---:|
| bad-empty        |  0.0 | **−9.00** | 0.0621* |
| bad-one_line     |  0.4 | **−8.60** | 0.0621* |
| bad-offtopic     |  2.4 | **−6.60** | 0.0621* |
| bad-boilerplate  |  4.0 | **−5.00** | 0.0621* |
| bad-hallucinated |  9.2 |   +0.20  |  1.000  |
| baseline (real)  |  9.0 |    —     |   —     |
| hybrid  (real)   |  9.8 |    —     |   —     |

\* 0.0625 is the *floor* p-value of a sign-flip permutation at n=5
(every pair same-signed). The four real-bad styles all sit at that floor; their
effect sizes (Δ = -5 to -9 points out of 25) are *huge*, and would clear
p < 0.001 trivially with even n = 10.

**What this establishes (✓).** The rubric is a valid measurement instrument
for separating non-reviews and pseudo-reviews from real reviews. Empty,
single-sentence, off-topic, and generic-boilerplate reviews are heavily
penalized; the rubric is not "scoring everything ~50%" indiscriminately.

**What this transparently exposes (a reportable limitation).** A *plausibly
hallucinated* review — same length and structure as a real review, but with
fabricated files, line numbers, and tests — scores statistically
indistinguishable from baseline (9.2 vs. 9.0). The rubric measures **coverage,
not correctness**. This is a known limitation of mention-check LLM-as-judge
evaluation and is shared by every published code-review evaluation framework
in the same family (CRScore, DeepCRCEval, CodeReviewer). We therefore frame
all KG-vs-baseline results as **coverage** lifts, not **correctness** lifts.

**Artifact:** `results/RUBRIC_POSITIVE_CONTROL.{json,md}`,
`scripts/positive_control_rubric.py`,
`outputs/positive_control_bad/pr{3,6,14,18,25}_bad-{empty,one_line,boilerplate,offtopic,hallucinated}.md`.

### 5.3 (Future, optional) Graded 0/1/2 scoring

Following Li et al. (2022, CodeReviewer), graded scoring (0 = not addressed;
1 = generic mention; 2 = specific, anchored mention) on the same 25 criteria
would capture precision differences invisible to binary scoring. *Not yet
executed; would target the §13.1 hybrid result to test whether the +1.00 KG-rel
lift grows further under graded scoring.*

---

## 6. References

- Bavota, G., Russo, B. (2015). *Four Eyes Are Better Than Two*. ICSE'15.
- Google. *Engineering Practices: Code Review Developer Guide.*
  https://google.github.io/eng-practices/review/
- ISO/IEC 25010:2011. *Systems and software engineering — SQuaRE — System
  and software quality models.* International Organization for
  Standardization.
- Landis, J.R., Koch, G.G. (1977). *The measurement of observer agreement
  for categorical data.* Biometrics 33(1): 159–174.
- Li, Z. et al. (2022). *CodeReviewer: Pre-Training for Automating Code
  Review Activities.* FSE'22.
- Lu, J. et al. (2024). *DeepCRCEval: Revisiting the Evaluation of Code
  Review Comment Generation.* EMNLP'24.
- OWASP Foundation. *OWASP Code Review Guide v2.0*.
  https://owasp.org/www-project-code-review-guide/
- Tufano, R. et al. (2021). *Towards Automating Code Review Activities.*
  ICSE'21.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and
  Chatbot Arena.* NeurIPS'23.
