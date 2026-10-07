```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes the issue where `BayesianRidge` and `ARDRegression` models did not center test features before computing predictive variance, leading to incorrect uncertainty estimates.

## Problem
1. The centering of test features before variance computation is not consistently applied across all relevant methods.
2. The fix may not account for all edge cases, such as when `fit_intercept=False`.

## Evidence
- `sklearn/linear_model/_bayes.py:397` and `sklearn/linear_model/_bayes.py:818`: The lines where test features are centered by subtracting `self.X_offset_`.
- `sklearn/linear_model/tests/test_bayes.py:185-200`: The new test added to verify the fix, but it does not cover scenarios where `fit_intercept=False`.

## Impact
- If test features are not correctly centered, the predictive variance will be inaccurate, potentially misleading users about the model's confidence in its predictions.
- The fix might not handle cases where the intercept is not fitted, leading to inconsistent behavior.

## Recommendation (Fix / Tests / Risks)
1. Ensure that the centering logic is conditional on `fit_intercept=True` to avoid unnecessary operations when `fit_intercept=False`.
2. Add additional tests to cover scenarios where `fit_intercept=False` to ensure consistent behavior across different configurations.
3. Review similar centering logic in other models to ensure consistency across the library.

## Traceability
Not specified
```