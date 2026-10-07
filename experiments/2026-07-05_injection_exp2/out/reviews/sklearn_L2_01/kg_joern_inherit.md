```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `_kmeans` function in `sklearn/cluster/_kmeans.py` by modifying the condition that checks the `x_squared_norms` parameter.

## Problem
1. The logic of the condition for `x_squared_norms` appears inverted, which may lead to incorrect behavior.
2. Lack of test coverage for the scenario where `x_squared_norms` is provided as `None`.

## Evidence
- `sklearn/cluster/_kmeans.py:159`: The condition `if x_squared_norms is not None:` should likely be `if x_squared_norms is None:` to maintain the original logic.
- No new tests are added to verify the behavior of `_kmeans` when `x_squared_norms` is `None` or not `None`.

## Impact
- The inversion of the condition could lead to incorrect calculation of `x_squared_norms`, potentially affecting clustering results.
- Without adequate test coverage, there is a risk of undetected bugs in scenarios where `x_squared_norms` is `None`, which might propagate errors to dependent modules like `_bicluster.py` and `_spectral.py`.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the logic of the condition on `x_squared_norms` to ensure it aligns with the intended functionality.
2. Add unit tests to cover both cases where `x_squared_norms` is `None` and when it is not, to ensure the function behaves as expected.
3. Verify the integration with dependent files to ensure no unintended side effects occur due to this change.

## Traceability
- Code Owners: sklearn/cluster module maintainers (specific owners not specified)
```