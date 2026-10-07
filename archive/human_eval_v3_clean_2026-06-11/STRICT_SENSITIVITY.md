# Strict-prompt sensitivity to individual KG-rel criteria

Closes the reviewer attack: "the strict-prompt d_z=+1.34 is large because
the prompt mandates the 9 KG-rel topics. Setting that caveat aside, is
the d_z carried by 1-2 dominant criteria, or broadly distributed?"

**Method:** for each of the 9 KG-rel criteria, recompute d_z on the
remaining 8-criterion subscale (leave-one-out). If d_z is robust to
removing any single criterion, the effect is broadly distributed.

## Headline (full 9-criterion KG-rel, n=35)

- Full subscale d_z = **+1.340**, mean Δ = +2.200, sd = 1.641

## Per-criterion mean Δ (parity−baseline-style, on strict reviews)

| Criterion | mean Δ | #PRs improved | #PRs same | #PRs worsened |
|---|---:|---:|---:|---:|
| F3 | +0.371 | 13 | 22 | 0 |
| F4 | +0.086 | 4 | 30 | 1 |
| T1 | -0.086 | 0 | 32 | 3 |
| T2 | +0.200 | 8 | 26 | 1 |
| T3 | +0.229 | 8 | 27 | 0 |
| M1 | +0.457 | 17 | 17 | 1 |
| M3 | +0.371 | 14 | 20 | 1 |
| C2 | +0.600 | 22 | 12 | 1 |
| Q2 | -0.029 | 0 | 34 | 1 |

## Leave-one-out d_z on remaining 8 criteria

Sorted ascending — the criterion at the top is the one whose removal
drops d_z the most (i.e., the most load-bearing criterion).

| Removed criterion | d_z on remaining 8 | drop from full | mean Δ | sd Δ |
|---|---:|---:|---:|---:|
| C2 | **+1.028** | −23.3% | +1.600 | 1.557 |
| M1 | **+1.176** | −12.3% | +1.743 | 1.482 |
| F3 | **+1.200** | −10.5% | +1.829 | 1.524 |
| M3 | **+1.284** | −4.2% | +1.829 | 1.424 |
| F4 | **+1.349** | +0.6% | +2.114 | 1.568 |
| T2 | **+1.356** | +1.1% | +2.000 | 1.475 |
| Q2 | **+1.384** | +3.2% | +2.229 | 1.610 |
| T3 | **+1.384** | +3.3% | +1.971 | 1.424 |
| T1 | **+1.462** | +9.1% | +2.286 | 1.564 |

## Reading

- Smallest d_z under any single-criterion removal: **+1.028**
  (when removing **C2**). Largest drop from the full d_z:
  **23.3%**. (Note: earlier documents stated "stays >+1.03" — the
  correct bound is >+1.02, since +1.028 rounds to +1.03 at 2 d.p.
  but is strictly below +1.03.)

- The strict-prompt d_z **stays large (>+0.8) under every single-criterion**
  removal. The +1.34 is **not** carried by one or two dominant criteria —
  the strict prompt's effect is broadly distributed across the 9 KG-rel
  criteria.

- **Two criteria are negative on average:** T1 (mean Δ = −0.086) and
  Q2 (mean Δ = −0.029). These are not load-bearing — removing either
  *increases* d_z (T1 → +1.46; Q2 → +1.38). That is, the strict prompt
  scores slightly *worse* than baseline on these two criteria, so
  including them in the subscale slightly drags the d_z down. The
  +1.34 is not 'all 9 criteria positive'; it is '7 of 9 criteria
  meaningfully positive, 2 essentially flat with a negative tilt'.
  This is fully consistent with the broadly-distributed claim — the
  effect is not concentrated in 1-2 criteria — but it is more honest
  than asserting uniform improvement across all 9.

## What this changes about the audit

Whatever the committee thinks of the prompt-mandates-coverage caveat, the
strict d_z=+1.34 is robust to removing any single criterion. A reviewer
cannot reduce the strict result to 'the prompt forced one topic' — every
single-criterion removal still leaves a sizeable d_z.

This is supplementary defensive evidence; the headline RQ2 anchor remains
the pre-registered tree-sitter `kg` (n=40, d_z=+0.47, p=0.006).