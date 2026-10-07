# Review Note — Evidence-Anchored

**Scope:** This pull request fixes an issue in `BayesianRidge` and `ARDRegression` where `predict(return_std=True)` incorrectly computed predictive variance by not centering test features when `fit_intercept=True`.

## Problem
1.  **Incomplete test coverage for `predict(return_std=True)` across `fit_intercept` configurations.** The new test `test_std_bayesian_ridge_noncentered` specifically addresses the bug for `fit_intercept=True`. However, there is no explicit test case in `sklearn/linear_model/tests/test_bayes.py` that verifies the correct behavior of `predict(return_std=True)` when `fit_intercept=False`. Additionally, while the existing `test_return_std` in the same file covers `return_std=True`, its assertions might not be robust enough to catch subtle changes in variance calculation, especially if its data generation implicitly centered the data previously.
2.  **Potential for `AttributeError` if `predict` is called before `fit`.** The `predict` methods in `BayesianRidge` and `ARDRegression` now access `self.X_offset_` directly. If `predict` is called on an unfitted estimator, this would result in an `AttributeError` instead of the more informative `NotFittedError` typically raised by scikit-learn estimators. This is a general robustness concern, not introduced by this PR, but highlighted by the added access to `self.X_offset_`.

## Evidence
*   `sklearn/linear_model/_bayes.py:397` (Addition of `X = X - self.X_offset_` in `BayesianRidge.predict`)
*   `sklearn/linear_model/_bayes.py:818` (Addition of `X = X - self.X_offset_` in `ARDRegression.predict`)
*   `sklearn/linear_model/tests/test_bayes.py:185` (New test `test_std_bayesian_ridge_noncentered` explicitly uses `Estimator(fit_intercept=True)`)
*   `sklearn/linear_model/tests/test_bayes.py::test_return_std` (Existing test for `predict(return_std=True)`)
*   `tests/test_ridge.py::test_ridge_classifier_multilabel_array_api` (Caller of `_bayes.py::predict`)
*   `tests/test_ridge.py::custom_multioutput_scorer` (Caller of `_bayes.py::predict`)

## Impact
*   **Problem 1:** Potential for future regressions in `predict(return_std=True)` behavior when `fit_intercept=False` to go unnoticed. Existing tests might not fully validate the corrected variance calculation across all relevant scenarios, leading to subtle bugs in uncertainty estimation.
*   **Problem 2:** Calling `predict` on an unfitted `BayesianRidge` or `ARDRegression` estimator will result in a less helpful `AttributeError` instead of a `NotFittedError`, potentially confusing users or making debugging harder.

## Recommendation (Fix / Tests / Risks)
1.  **Enhance Test Coverage for `fit_intercept=False`:** Add a new test case within `sklearn/linear_model/tests/test_bayes.py` (e.g., extending `test_std_bayesian_ridge_noncentered` or a new dedicated test) that explicitly initializes `BayesianRidge` and `ARDRegression` with `fit_intercept=False`, fits them, and then calls `predict(return_std=True)` to assert that `X_offset_` is correctly handled (i.e., no centering occurs, as `X_offset_` should be `0.0`).
2.  **Review and Strengthen `test_return_std`:** Re-evaluate the assertions in `sklearn/linear_model/tests/test_bayes.py::test_return_std` to ensure they are robust enough to validate the corrected variance calculation, especially for cases where `fit_intercept=True` and data is not centered around zero. Consider adding more specific assertions about the relative magnitudes of `y_std` at different `X` values, similar to the new `test_std_bayesian_ridge_noncentered`.
3.  **Add `NotFittedError` checks:** Implement `_check_is_fitted` at the beginning of the `predict` methods in both `BayesianRidge` and `ARDRegression` within `sklearn/linear_model/_bayes.py` to ensure `self.X_offset_` and other attributes are initialized, providing a more informative `NotFittedError` if `predict` is called before `fit`.

## Traceability
Not specified