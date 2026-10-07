# Review Note — Evidence-Anchored

**Scope:** This pull request refines the callback system by improving error handling during setup and teardown, ensuring `on_fit_task_end` is always called, and standardizing `sample_weight` metadata passing.

## Problem
1.  **Incomplete Teardown Logic:** Callbacks that failed during setup or were not fully set up might still have their `teardown` method called, leading to potential errors or incorrect state. The previous implementation iterated over all registered callbacks for teardown, regardless of whether their `setup` hook was successfully invoked.
2.  **Fragile `on_fit_task_end` Invocation:** The `on_fit_task_end` hook was not guaranteed to be called in `_fit_and_score` if an exception occurred during fitting or scoring, leading to incomplete callback lifecycle management, especially in scenarios like `GridSearchCV` where some fits are expected to fail.
3.  **Inconsistent `set_callbacks` Behavior:** Calling `set_callbacks()` without arguments would raise an `AttributeError` if no callbacks were previously set, making the API less robust when attempting to clear callbacks.

## Evidence
*   `sklearn/callback/_callback_support.py:95-96` (addition of `_skl_callbacks_to_teardown` and conditional append)
*   `sklearn/callback/_callback_support.py:122-133` (change in teardown loop to use `_skl_callbacks_to_teardown` and `ExceptionGroup` handling for multiple teardown errors)
*   `sklearn/callback/_callback_support.py:44` (change from `del self._skl_callbacks` to `self.__dict__.pop("_skl_callbacks", None)`)
*   `sklearn/model_selection/_validation.py:890-894` (moving `call_on_fit_task_end` into a `finally` block)
*   `sklearn/callback/tests/test_callback_support.py:59-70` (new test `test_teardown_matches_setup_calls_on_partial_setup_failure`)
*   `sklearn/callback/tests/test_callback_support.py:73-87` (new test `test_multiple_teardown_errors_are_grouped`)
*   `sklearn/callback/tests/test_callback_support.py:129-137` (new test `test_set_callback_empty`)
*   `sklearn/model_selection/tests/test_search.py:3132-3149` (new test `test_search_callbacks_with_partial_fit_failures`)

## Impact
*   **Runtime Errors and State Corruption:** Callbacks could fail during teardown if their setup was incomplete, leading to unhandled exceptions or an inconsistent state in the application. The new `ExceptionGroup` handling improves error reporting but the underlying issue of incorrect teardown calls is fixed by tracking setup callbacks.
*   **Incomplete Monitoring/Logging:** Critical `on_fit_task_end` events might be missed, especially in hyperparameter search scenarios where individual fits can fail, leading to incomplete monitoring, logging, or resource cleanup by callbacks.
*   **API Fragility:** The `set_callbacks` method was less user-friendly and could lead to unexpected `AttributeError` when attempting to clear callbacks on an estimator that had none set.

## Recommendation (Fix / Tests / Risks)
1.  **Fix:** The changes are well-justified and correctly address the identified problems, significantly improving the robustness and reliability of the callback system. No further fixes are immediately apparent from the diff.
2.  **Tests:** The added tests are comprehensive for the new behaviors, covering partial setup failures, multiple teardown errors, and the `finally` block for `on_fit_task_end`. The `validate_params` addition for `ProgressBar` is also well-covered by existing validation infrastructure.
3.  **Risks:**
    *   **Callback Contract Change:** The change in `_search.py` and `_validation.py` where `metadata_callbacks` can now be `None` (if `sample_weight` is not provided) instead of `{"sample_weight": {}}` or `{"sample_weight": None}` might subtly change the contract for existing custom callbacks. Callbacks should ideally check `if metadata is not None and "sample_weight" in metadata` before accessing `metadata["sample_weight"]`. This is a minor risk, as `None` is generally a clearer signal for absence.
    *   **Shallow Copy in `_from_reconstruction_attributes`**: The removal of the `TODO` regarding `copy.copy` implies a decision to use a shallow copy. While likely correct for the intended use (reconstructing an estimator from specific attributes), it's a common source of subtle bugs if the estimator's internal state includes mutable objects that are not part of `reconstruction_attributes` and are modified during `fit`. This is a general architectural consideration rather than a direct bug introduced by this PR, but worth noting.

## Traceability
Not specified