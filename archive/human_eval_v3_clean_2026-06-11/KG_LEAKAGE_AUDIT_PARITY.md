# KG-signal leakage — PARITY reviews

Same metric as `KG_LEAKAGE_AUDIT.md` (buggy run), but on the parity reviews.
Reports both rates side-by-side so we can see whether adding the PR body to
the prompt shifts how often the LLM surfaces caller/dependent symbols.

## Summary

- Reviews audited: **35** (parity vs buggy, same 35 PRs)
- PRs with ≥1 caller signal in evidence: **33**

**Binary citation rate (≥1 signal cited in review):**

- Parity: **20 / 33** = **61%**
- Buggy : **22 / 33** = **67%**

**Aggregate signal density (total cited / total available):**

- Parity: **35 / 3586** = **1.0%**
- Buggy : **34 / 3586** = **0.9%**

**Parity − buggy delta in symbols cited: +1** (parity surfaces more)

## Per-PR detail

| PR | Signals available | Parity cited | Buggy cited | Δ (parity − buggy) |
|---:|---:|---:|---:|---:|
| 10 | 15 | 0 | 2 | -2 |
| 12 | 38 | 1 | 1 | +0 |
| 13 | 42 | 2 | 2 | +0 |
| 14 | 19 | 0 | 0 | +0 |
| 15 | 2490 | 0 | 1 | -1 |
| 18 | 57 | 0 | 0 | +0 |
| 19 | 45 | 2 | 3 | -1 |
| 1 | 5 | 0 | 0 | +0 |
| 20 | 0 | 0 | 0 | +0 |
| 21 | 37 | 1 | 1 | +0 |
| 22 | 11 | 0 | 0 | +0 |
| 23 | 19 | 0 | 0 | +0 |
| 24 | 32 | 2 | 1 | +1 |
| 28 | 12 | 1 | 1 | +0 |
| 29 | 10 | 0 | 0 | +0 |
| 2 | 81 | 1 | 1 | +0 |
| 30 | 0 | 0 | 0 | +0 |
| 31 | 22 | 2 | 2 | +0 |
| 32 | 37 | 2 | 1 | +1 |
| 33 | 49 | 1 | 2 | -1 |
| 34 | 4 | 2 | 2 | +0 |
| 38 | 19 | 1 | 1 | +0 |
| 39 | 10 | 0 | 0 | +0 |
| 3 | 19 | 3 | 2 | +1 |
| 40 | 6 | 0 | 0 | +0 |
| 41 | 15 | 0 | 0 | +0 |
| 42 | 36 | 1 | 1 | +0 |
| 43 | 9 | 2 | 2 | +0 |
| 44 | 27 | 1 | 1 | +0 |
| 45 | 37 | 0 | 0 | +0 |
| 46 | 32 | 0 | 0 | +0 |
| 47 | 212 | 4 | 2 | +2 |
| 48 | 54 | 2 | 2 | +0 |
| 6 | 18 | 1 | 1 | +0 |
| 8 | 67 | 3 | 2 | +1 |

## Reading

If parity cites *fewer* caller signals than buggy, that supports the claim
that PR body and KG context are partially substitutable: when the body is
available, the LLM leans on body content and surfaces less of the caller
graph.

If the rates are similar, the LLM has stable surfacing habits and the
body acts as a *separate* source rather than a substitute. In that case the
d_z drop from +0.58 to +0.30 is still real but the redundancy mechanism
isn't load-bearing — the bug just inflated the buggy number for some other
reason (e.g., baseline judges scored body-less reviews more harshly).
