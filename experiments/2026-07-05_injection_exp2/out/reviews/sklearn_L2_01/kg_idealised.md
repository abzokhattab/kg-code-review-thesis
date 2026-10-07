```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `_kmeans` function by altering the condition for checking `x_squared_norms`.

## Problem
1. The logic for setting `x_squared_norms` appears to be inverted, which might lead to incorrect behavior.
2. The change lacks corresponding updates in test cases to verify the new logic.

## Evidence
- `sklearn/cluster/_kmeans.py:159`: The condition `if x_squared_norms is not None` suggests that `x_squared_norms` will be recalculated even when it is already provided, which seems contrary to the intended optimization.
- No test files have been modified to reflect the change in logic, indicating a lack of test coverage for this specific refactor.

## Impact
- The inversion of the condition could lead to unnecessary recalculation of `x_squared_norms`, impacting performance.
- Without test updates, there is a risk that this change could introduce bugs that go undetected, affecting clustering results.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the logic to ensure that `x_squared_norms` is only recalculated when it is `None`, preserving the original intent of the optimization.
2. Add or update test cases to cover scenarios where `x_squared_norms` is both `None` and not `None` to ensure the logic behaves as expected.
3. Review the integration of this function with other parts of the codebase to ensure that this change does not introduce unexpected side effects.

## Traceability
- Code Owner: sklearn/cluster team
```