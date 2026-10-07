```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes the issue where `BayesianRidge` and `ARDRegression` models incorrectly compute predictive variance by centering test features during prediction.

## Problem
1. The centering of test features in the `predict` method is applied unconditionally, which may not be appropriate for all scenarios.
2. The test coverage for the new behavior is limited to a specific scenario and may not cover edge cases or different data distributions.

## Evidence
- `sklearn/linear_model/_bayes.py:line 401` and `line 823`: The test features are centered by subtracting `self.X_offset_` without checking if `fit_intercept` is `True`.
- `sklearn/linear_model/tests/test_bayes.py:line 192`: The test only checks a specific case with a small dataset and may not account for other potential edge cases.

## Impact
- Unconditional centering of test features could lead to incorrect variance calculations if `fit_intercept` is `False`, potentially causing misleading predictions.
- Limited test coverage increases the risk of regression or unhandled edge cases in different data scenarios.

## Recommendation (Fix / Tests / Risks)
1. Add a condition to check if `fit_intercept` is `True` before centering the test features in the `predict` method.
2. Expand test cases to include scenarios where `fit_intercept` is `False` and with different data distributions to ensure robustness.
3. Consider adding tests for edge cases, such as when `X_offset_` is zero or when the input data has varying scales.

## Traceability
Not specified
```