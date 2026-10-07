```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes the predictive variance computation in `BayesianRidge` and `ARDRegression` by centering test features during prediction.

## Problem
1. The centering of test features in the `predict` method is not conditionally checked against `fit_intercept`, which could lead to incorrect behavior if `fit_intercept=False`.
2. The new test `test_std_bayesian_ridge_noncentered` does not cover scenarios where `fit_intercept=False`, potentially missing edge cases.

## Evidence
- `sklearn/linear_model/_bayes.py:397` and `sklearn/linear_model/_bayes.py:818`: The lines where test features are centered without checking `fit_intercept`.
- `sklearn/linear_model/tests/test_bayes.py:185-199`: The new test added does not include cases for `fit_intercept=False`.

## Impact
- If `fit_intercept=False`, centering the test features could lead to incorrect variance predictions, as the model would not have been trained with centered features.
- Lack of test coverage for `fit_intercept=False` means potential bugs in this configuration might go unnoticed, affecting model reliability in certain use cases.

## Recommendation (Fix / Tests / Risks)
1. Add a conditional check for `fit_intercept` before centering test features in the `predict` method.
2. Extend the test `test_std_bayesian_ridge_noncentered` to include cases where `fit_intercept=False` to ensure comprehensive test coverage.
3. Review other parts of the codebase where similar centering logic might be applied to ensure consistency and correctness.

## Traceability
- Code Owners: sklearn/linear_model team
- Related Teams: sklearn/testing team
```