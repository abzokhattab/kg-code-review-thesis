```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes the issue where `BayesianRidge` and `ARDRegression` models did not center test features during prediction, affecting the computation of predictive variance.

## Problem
1. The centering of test features is applied directly in the `predict` method without checking if `fit_intercept` is set to `True`.
2. The subtraction of `self.X_offset_` assumes that `X_offset_` is always available, which may not be the case if the model was not fit with `fit_intercept=True`.

## Evidence
- `sklearn/linear_model/_bayes.py:397`: The line where `X` is centered without checking `fit_intercept`.
- `sklearn/linear_model/_bayes.py:818`: Similar issue in the `ARDRegression` predict method.

## Impact
- If `fit_intercept=False`, the subtraction of `self.X_offset_` could lead to incorrect predictions or runtime errors if `X_offset_` is not initialized.
- This could result in misleading predictive variance outputs, potentially affecting downstream applications relying on uncertainty estimates.

## Recommendation (Fix / Tests / Risks)
1. Add a condition to check if `fit_intercept` is `True` before centering `X` in both `BayesianRidge` and `ARDRegression` predict methods.
2. Ensure that `self.X_offset_` is initialized only when `fit_intercept=True` to avoid potential attribute errors.
3. Extend test coverage to include scenarios where `fit_intercept=False` to verify that the fix does not introduce new issues.

## Traceability
Not specified
```