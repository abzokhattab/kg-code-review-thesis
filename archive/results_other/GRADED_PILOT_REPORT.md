# Graded 0-3 Scale Pilot — Results

**Date:** 2026-06-01
**PRs:** 35  |  **Judges:** gemini:gemini-2.5-flash, gemini:gemini-2.5-pro
**Criteria:** F3, F4, P1, R2, T3 (clean subscale, graded 0-3 with anchors)

---

## Motivation

Binary 0/1 scoring cannot distinguish a review that vaguely mentions integration
from one that names 3 exact callers with file:line references. This pilot replaces
binary judgment with anchored 0-3 descriptors to test whether a richer signal
increases effect size (d_z).

---

## Results

### joern_kg vs baseline

**Aggregate (5 criteria, /15):** Δ=+3.981  95%CI=[+3.11, +4.85]  p=0.0000***  **d_z=+1.724**  W/T/L=26/0/1

| Criterion | Δ mean | 95% CI | p | d_z | W/T/L |
|---|---:|---:|---:|---:|---:|
| F3 — Integration awareness — how the cha | +1.074 | [+0.72, +1.43] | 0.0000*** | +1.133 | 19/8/0 |
| F4 — Broken contracts — potential breaki | +0.963 | [+0.57, +1.37] | 0.0001*** | +0.882 | 18/6/3 |
| P1 — Performance issues — identifies pot | +0.111 | [-0.09, +0.37] | 0.2525 | +0.170 | 2/23/2 |
| R2 — Complexity — identifies unnecessary | +0.648 | [+0.19, +1.11] | 0.0083** | +0.508 | 11/14/2 |
| T3 — Specific test files — names exact t | +1.185 | [+0.80, +1.59] | 0.0000*** | +1.075 | 22/3/2 |

---

## Anchor Definitions (0-3)

### F3 — Integration awareness — how the change interacts with callers/dependents

- **0:** No mention of integration or impact on other components.
- **1:** Vaguely notes that integration may be affected, but names no specific component.
- **2:** Names at least one specific caller, module, or dependent file that is affected.
- **3:** Names multiple specific callers or dependent components with file paths or function names, and explains the concrete integration risk for each.

### F4 — Broken contracts — potential breaking changes or impact on dependent code

- **0:** No mention of breaking changes or API contract violations.
- **1:** Generically warns that callers or API consumers may be affected, without specifics.
- **2:** Identifies at least one specific API contract or caller expectation that could break.
- **3:** Identifies multiple specific contract violations with file/function references and explains exactly what downstream behavior would change.

### P1 — Performance issues — identifies potential inefficiencies in the changed code

- **0:** No mention of performance.
- **1:** Generic comment that performance could be affected (e.g., 'this might be slow').
- **2:** Identifies a specific operation, loop, or data structure that introduces a performance concern, with a brief explanation.
- **3:** Identifies multiple specific performance issues with code references, explains the complexity or bottleneck, and suggests a concrete alternative or fix.

### R2 — Complexity — identifies unnecessary complexity or suggests simplification

- **0:** No comment on complexity or code structure.
- **1:** Generic remark that the code is complex or could be simplified.
- **2:** Points to a specific function or block that is unnecessarily complex and suggests a concrete simplification.
- **3:** Identifies multiple instances of unnecessary complexity with code-level references, explains why each is problematic, and offers specific refactoring suggestions.

### T3 — Specific test files — names exact test files that should be added or updated

- **0:** No mention of test files, or only says 'add tests' generically.
- **1:** Mentions that tests should exist but does not name a file (e.g., 'the test suite').
- **2:** Names at least one specific test file path from the repository.
- **3:** Names multiple specific test file paths, references the exact test scenarios or functions within those files that need coverage, and explains what edge cases are currently missing.
