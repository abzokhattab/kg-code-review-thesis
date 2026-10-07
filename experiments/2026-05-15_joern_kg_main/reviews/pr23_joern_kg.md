# Review Note — Evidence-Anchored

**Scope:** This PR performs cleanup for the 1.1 release, including transforming certain warnings into errors, completing the deprecation cycle for positional arguments in specific functions, and hardening estimator checks.

## Problem
1.  **Integration Regression for `SequentialFeatureSelector`:** The removal of the `"requires_y": True` tag from `SequentialFeatureSelector`'s `_more_tags` method, combined with the updated `check_requires_y_none` in `estimator_checks.py`, will cause `SequentialFeatureSelector` to fail `check_estimator`. `SequentialFeatureSelector` inherently requires `y` for fitting, but without the tag, `check_requires_y_none` will incorrectly assume it does not, leading to a test failure when `fit(X, None)` raises an expected `ValueError`.
2.  **Missing Test Coverage for `TargetRegressor`:** The new explicit `ValueError` raised in `TargetRegressor.fit` when `y is None` introduces a new failure mode. While this is a correct behavior, there is no corresponding test case to verify this specific error is raised as expected.
3.  **Unused Utility Function with Updated Version:** The `_deprecate_positional_args` utility function is stated to have no current usage in the codebase, yet its default `version` parameter is updated. Keeping an unused function with an updated version string can lead to confusion or maintenance overhead if its purpose is not clearly documented or if it's truly dead code.

## Evidence
*   **Integration Regression:**
    *   `sklearn/feature_selection/_sequential.py:306-307`: Removal of `"requires_y": True` from `_more_tags`.
    *   `sklearn/utils/estimator_checks.py:3665-3683`: `check_requires_y_none` now directly raises a `ValueError` if `fit(X, None)` raises an unexpected error, or if it *doesn't* raise an error when `requires_y` is `True`. Since `SequentialFeatureSelector`'s `_more_tags` will now implicitly return `False` for `requires_y`, `check_requires_y_none` will expect `fit(X, None)` *not* to raise an error.
    *   `SequentialFeatureSelector.fit` (implicitly via `check_array(y)`) will raise a `ValueError` when `y` is `None`.
    *   Related test file: `sklearn/feature_selection/tests/test_sequential.py` (will likely fail `check_estimator` for `SequentialFeatureSelector`).
*   **Missing Test Coverage:**
    *   `sklearn/compose/_target.py:207-211`: New `ValueError` block for `if y is None:`.
    *   `sklearn/compose/_target.py::fit` is called by `_target.py::_fit_transformer`.
    *   Related test file: `sklearn/compose/tests/test_target.py`.
*   **Unused Utility Function:**
    *   `sklearn/utils/validation.py:46-47`: `_deprecate_positional_args` default `version` changed from "1.1 (renaming of 0.26)" to "1.3".
    *   PR description states: "There's no usage of `_deprecate_positional_args` anymore."

## Impact
*   **Integration Regression:** `SequentialFeatureSelector` will fail `check_estimator` tests, preventing its integration into the standard scikit-learn estimator ecosystem and potentially blocking future development or releases. This is a critical regression.
*   **Missing Test Coverage:** The new `ValueError` in `TargetRegressor.fit` for `y is None` is a breaking change in behavior. Without a specific test, this behavior could inadvertently change in the future, or the error message itself might not be consistent, leading to unexpected failures for users.
*   **Unused Utility Function:** Keeping dead code, especially with an updated version string, adds to the codebase's cognitive load and can be misleading. It might suggest the function is actively used or planned for immediate use, when it is not.

## Recommendation (Fix / Tests / Risks)
1.  **Fix `SequentialFeatureSelector` `requires_y` tag:** Revert the removal of `"requires_y": True` in `sklearn/feature_selection/_sequential.py`'s `_more_tags` method. This will correctly inform `check_estimator` that `SequentialFeatureSelector` requires `y`, allowing `check_requires_y_none` to pass as intended.
2.  **Add Test for `TargetRegressor` `y is None`:** Add a new test case to `sklearn/compose/tests/test_target.py` that specifically calls `TargetRegressor().fit(X, None)` and asserts that a `ValueError` with the expected message is raised.
3.  **Address `_deprecate_positional_args`:**
    *   **Option A (Preferred):** If the function is truly unused and there's no immediate plan to re-introduce positional argument deprecations, remove `_deprecate_positional_args` from `sklearn/utils/validation.py`. This aligns with the goal of removing dead code.
    *   **Option B:** If the function is intended to be kept for future use (as suggested by the PR author's comment), add a clear comment above the function explaining its purpose as a dormant utility for future deprecation cycles, and why it's being kept despite no current usage. The `version="1.3"` change is then acceptable as a placeholder for its next potential activation.

## Traceability
Not specified