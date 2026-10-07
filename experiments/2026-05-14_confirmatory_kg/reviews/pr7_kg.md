# Review Note — Evidence-Anchored

**Scope:** This PR introduces fixes for callback management, specifically addressing `sample_weight` inconsistencies, robust callback teardown, and ensuring `on_fit_task_end` is always called in `_fit_and_score` via a `finally` block.

## Integration Risk

*   **`sklearn/linear_model/tests/test_logistic.py`**: The change in `sklearn/linear_model/_logistic.py` fixes a typo (`sample_weght` to `sample_weight`) when passing metadata to callbacks. This is a bug fix and should not break existing tests, but rather enable correct behavior for callbacks that inspect `sample_weight`.
*   **`sklearn/linear_model/tests/test_sag.py`**: No direct integration risk. The changes are internal to callback management and `sample_weight` passing, which `test_sag.py` is unlikely to directly depend on in a breaking way.
*   **`sklearn/linear_model/__init__.py`**: No integration risk. This file primarily handles imports and is not affected by internal logic changes within `_logistic.py` or callback support.
*   **`sklearn/neural_network/_base.py`**: Low integration risk. The change from `del self._skl_callbacks` to `self.__dict__.pop("_skl_callbacks", None)` in `set_callbacks` (in `_callback_support.py`) is a robustness improvement, preventing `AttributeError` if the attribute doesn't exist. The new `ExceptionGroup` for multiple teardown errors is also a more robust error handling mechanism. These changes are unlikely to break existing callback usage in `_base.py`.
*   **`sklearn/neural_network/_rbm.py`**: Low integration risk, for the same reasons as `_neural_network/_base.py`.
*   **`sklearn/inspection/_plot/decision_boundary.py`**: No integration risk. This module is unrelated to callback management or `sample_weight` handling.
*   **`sklearn/svm/_bounds.py`**: No integration risk. This module is unrelated to callback management or `sample_weight` handling.
*   **`benchmarks/bench_isotonic.py`**: Low integration risk. While benchmarks call `fit` methods that might use callbacks, the changes are primarily correctness and robustness fixes. There's a minor risk of performance regression due to `ExceptionGroup` overhead or more complex callback teardown logic, but it's unlikely to be significant.
*   **`doc/conf.py`**: No integration risk. This file is for documentation configuration.
*   **`sklearn/tree/tests/test_fenwick.py`**: No integration risk. This module is unrelated to callback management or `sample_weight` handling.
*   **`sklearn/metrics/_scorer.py`**: Low integration risk. The change in `_validation.py` to move `callback_ctx.call_on_fit_task_end` into a `finally` block ensures it's always called, even if scoring (which might involve `_scorer.py`) fails. This is a correctness fix and should improve callback reliability.
*   **`sklearn/metrics/tests/test_score_objects.py`**: No direct integration risk. This file tests scoring objects, which are not directly affected by callback management changes.
*   **`sklearn/metrics/tests/test_regression.py`**: No direct integration risk. Similar to `test_score_objects.py`.
*   **`sklearn/experimental/tests/test_enable_successive_halving.py`**: Low integration risk. This test file relies heavily on `_search.py` and `_validation.py`. The new tests in `sklearn/model_selection/tests/test_search.py` (`test_search_callbacks_receive_sample_weight`, `test_search_callbacks_with_partial_fit_failures`) directly cover the `sample_weight` and `finally` block changes relevant to search, mitigating the risk for experimental search methods.
*   **`sklearn/experimental/enable_halving_search_cv.py`**: Low integration risk, for the same reasons as `test_enable_successive_halving.py`.

## Test Coverage Assessment

*   **`sklearn/linear_model/tests/test_logistic.py`**:
    *   **Coverage Gap**: The `sample_weght` typo fix in `sklearn/linear_model/_logistic.py` ensures `sample_weight` is correctly passed to callbacks. However, `test_logistic.py` does not appear to have a dedicated test case that explicitly verifies that `LogisticRegression`'s `fit` method correctly passes `sample_weight` to its callbacks' metadata. While `test_search.py` covers this for search estimators, the base estimator's behavior should also be directly tested.
*   **`sklearn/model_selection/tests/test_search.py`**:
    *   **Coverage Adequate**: This file includes new tests (`test_search_callbacks_with_partial_fit_failures`, `test_search_callbacks_receive_sample_weight`) that directly cover the changes in `sklearn/model_selection/_search.py` and `sklearn/model_selection/_validation.py` regarding `sample_weight` metadata and the `on_fit_task_end` hook being called in a `finally` block, especially in scenarios with partial fit failures.
*   **`sklearn/utils/tests/test_validation.py`**:
    *   **Coverage Gap**: The change in `sklearn/model_selection/_validation.py` moves `callback_ctx.call_on_fit_task_end` into a `finally` block within `_fit_and_score`. While `test_search.py` covers this in the context of `GridSearchCV`, `test_validation.py` lacks a general test for `_fit_and_score` that specifically asserts `on_fit_task_end` is always called, even if an error occurs *after* the fit but *before* the original `on_fit_task_end` call (e.g., during scoring).
*   **`sklearn/utils/tests/test_param_validation.py`**:
    *   **Coverage Gap**: The `ProgressBar` class in `sklearn/callback/_progressbar.py` now uses `validate_params` for its `max_propagation_depth` parameter. `test_param_validation.py` should contain a test case that verifies the `Interval(Integral, 0, None, closed="left")` validation for `ProgressBar` by passing invalid inputs (e.g., negative integers, floats, strings) to its constructor and asserting that a `ValueError` is raised.
*   **`sklearn/model_selection/tests/test_validation.py`**:
    *   **Coverage Gap**: Similar to `sklearn/utils/tests/test_validation.py`, this file should ideally have a test for `_fit_and_score` (which is in `sklearn/model_selection/_validation.py`) that verifies the `on_fit_task_end` callback is called in a `finally` block, independent of `GridSearchCV`'s specific logic. This would ensure the robustness of `_fit_and_score`'s callback handling in more general cross-validation contexts.

## Problem

1.  **Incomplete Test Coverage for `sample_weight` in Base Estimators**: While `sample_weight` handling for callbacks is improved in `_logistic.py` and `_search.py`, `sklearn/linear_model/tests/test_logistic.py` does not explicitly test that `LogisticRegression` correctly passes `sample_weight` to its callbacks. This leaves a gap in verifying the base estimator's direct callback integration.
2.  **Missing General `_fit_and_score` Callback Teardown Test**: The crucial change of moving `on_fit_task_end` to a `finally` block in `_fit_and_score` (in `sklearn/model_selection/_validation.py`) is covered by `test_search.py` within `GridSearchCV`. However, `sklearn/utils/tests/test_validation.py` and `sklearn/model_selection/tests/test_validation.py` lack a more general test for `_fit_and_score` that ensures this `finally` block behavior for callbacks, independent of the complexities of a grid search.
3.  **Untested Parameter Validation for `ProgressBar`**: The `validate_params` decorator was added to `ProgressBar.__init__` in `sklearn/callback/_progressbar.py` for `max_propagation_depth`. There is no corresponding test in `sklearn/utils/tests/test_param_validation.py` to verify that this validation correctly rejects invalid inputs.

## Evidence

*   **Problem 1 (Incomplete Test Coverage for `sample_weight` in Base Estimators)**:
    *   Diff: `sklearn/linear_model/_logistic.py:1461` (`{"sample_weight": sample_weight}` fix).
    *   KG Context: `sklearn/linear_model/tests/test_logistic.py` (no explicit test for `sample_weight` in callbacks).
*   **Problem 2 (Missing General `_fit_and_score` Callback Teardown Test)**:
    *   Diff: `sklearn/model_selection/_validation.py:883-888` (moving `callback_ctx.call_on_fit_task_end` to `finally`).
    *   KG Context: `sklearn/utils/tests/test_validation.py`, `sklearn/model_selection/tests/test_validation.py` (no specific test for `_fit_and_score`'s `finally` block with callbacks).
*   **Problem 3 (Untested Parameter Validation for `ProgressBar`)**:
    *   Diff: `sklearn/callback/_progressbar.py:26-29` (`@validate_params` added to `ProgressBar.__init__`).
    *   KG Context: `sklearn/utils/tests/test_param_validation.py` (no test for `ProgressBar`'s `max_propagation_depth` validation).

## Impact

*   **Problem 1**: Without direct tests in `test_logistic.py`, future regressions in how `LogisticRegression` (or other base estimators) passes `sample_weight` to callbacks could go unnoticed. This could lead to callbacks receiving incorrect or missing `sample_weight` metadata when used directly with these estimators.
*   **Problem 2**: The robustness of `_fit_and_score`'s callback management, particularly ensuring `on_fit_task_end` is always called, is not fully verified across all scenarios. If an error occurs during scoring or other post-fit steps in a non-GridSearchCV context, the `on_fit_task_end` callback might still be missed, leading to incomplete callback lifecycle management and potential resource leaks or incorrect state.
*   **Problem 3**: The `validate_params` decorator for `ProgressBar`'s `max_propagation_depth` is a new validation rule. Without a dedicated test, there's no guarantee that this validation works as intended, potentially allowing invalid `max_propagation_depth` values to be passed, leading to unexpected behavior or runtime errors in `ProgressBar`.

## Recommendation

1.  **Add `sample_weight` Callback Test for `LogisticRegression`**: In `sklearn/linear_model/tests/test_logistic.py`, add a test case that instantiates `LogisticRegression` with a `RecordingCallback`, calls `fit` with `sample_weight`, and asserts that the `on_fit_task_begin` and `on_fit_task_end` hooks receive the correct `sample_weight` in their `metadata` dictionary.
2.  **Add General `_fit_and_score` Callback Teardown Test**: In `sklearn/model_selection/tests/test_validation.py` (or `sklearn/utils/tests/test_validation.py`), add a test that calls `_fit_and_score` with a `RecordingCallback` and an estimator that raises an error *after* `fit` but *before* the original `on_fit_task_end` location. Assert that `on_fit_task_end` is still called due to the `finally` block.
3.  **Add Parameter Validation Test for `ProgressBar`**: In `sklearn/utils/tests/test_param_validation.py`, add test cases for `sklearn.callback.ProgressBar`'s `__init__` method. Verify that passing invalid values (e.g., `max_propagation_depth=-1`, `max_propagation_depth=0.5`, `max_propagation_depth="abc"`) for `max_propagation_depth` raises a `ValueError` as expected by the `validate_params` decorator.

## Traceability
Not specified