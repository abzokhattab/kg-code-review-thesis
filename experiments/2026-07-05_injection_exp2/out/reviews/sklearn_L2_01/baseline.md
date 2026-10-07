```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `_kmeans` function in `sklearn/cluster/_kmeans.py` by altering a conditional check related to `x_squared_norms`.

## Problem
1. The logic of the conditional check for `x_squared_norms` has been reversed, which may lead to incorrect behavior.
2. The change does not include any updates to test cases to verify the new behavior.

## Evidence
- `sklearn/cluster/_kmeans.py:159`: The condition `if x_squared_norms is None:` was changed to `if x_squared_norms is not None:`, altering the intended logic.

## Impact
- The reversal of the conditional logic could lead to incorrect initialization of `x_squared_norms`, potentially causing errors in downstream computations within the KMeans algorithm.
- Without corresponding test updates, there is a risk that this change introduces a regression or unintended behavior that is not caught by the current test suite.

## Recommendation (Fix / Tests / Risks)
1. Review the logic change to ensure it aligns with the intended functionality of the `_kmeans` method.
2. Add or update test cases to cover scenarios where `x_squared_norms` is both `None` and not `None` to ensure the new logic behaves as expected.
3. Consider adding comments or documentation to clarify the purpose of this logic change for future maintainers.

## Traceability
Not specified
```