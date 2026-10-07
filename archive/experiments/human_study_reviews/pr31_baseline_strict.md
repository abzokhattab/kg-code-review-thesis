# Review Note — Evidence-Anchored

**Scope:** This PR fixes the predictive variance computation in `BayesianRidge` and `ARDRegression` by centering test features during prediction.

## Problem
1. The change may inadvertently affect other parts of the code that rely on the original behavior of `predict` without centering.
2. The fix is applied to `predict` methods, but there is no explicit check for whether `fit_intercept` is `True` before centering, which could lead to incorrect behavior if `fit_intercept=False`.
3. The documentation update is minimal and may not fully inform users of the change in behavior.
4. The test coverage does not include scenarios where `fit_intercept=False`, which could lead to untested edge cases.

## Evidence
- `sklearn/linear_model/_bayes.py:401` and `sklearn/linear_model/_bayes.py:822`: The lines where `X` is centered by subtracting `self.X_offset_`.
- `sklearn/linear_model/tests/test_bayes.py:189`: New test `test_std_bayesian_ridge_noncentered` added to verify the fix.

## Impact
- **Technical impact:** The change could break existing functionality if other components rely on the previous behavior of `predict` without centering.
- **Regression risk:** There is a risk of regression if `fit_intercept=False` is not handled correctly.
- **Untested scenarios:** The behavior when `fit_intercept=False` is not covered by tests, potentially leading to unhandled edge cases.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Add a condition to check if `fit_intercept` is `True` before centering `X` in the `predict` methods.
2. **Tests:** Add tests for scenarios where `fit_intercept=False` to ensure the behavior is correct in all cases.
3. **Documentation:** Expand the documentation to clearly explain the change in behavior and its implications for users.
4. **Risks:** Review other components or functions that might rely on the previous behavior of `predict` to assess integration risks.

## Traceability
- Code owners: Not specified