# Review Note — Evidence-Anchored

**Scope:** This PR refactors repeated `ValueError` checks for metadata routing parameters into a new helper function `_raise_for_params` and updates some tests to use a pytest fixture for enabling metadata routing.

## Problem
1.  **Test Gap for `MultiOutputEstimator` methods:** The new `_raise_for_params` helper is used in `MultiOutputEstimator.partial_fit` and `MultiOutputEstimator.fit`. However, there are no explicit tests in the diff or related test files that verify the `ValueError` is raised when extra parameters are passed to these methods while metadata routing is disabled.
2.  **Test Gap for `Pipeline` methods:** Similarly, `Pipeline.decision_function`, `Pipeline.transform`, and `Pipeline.inverse_transform` now use `_raise_for_params`. There are no dedicated tests to ensure these methods correctly raise a `ValueError` when `params` are provided and `enable_metadata_routing` is `False`.
3.  **Minor Error Message Inconsistency for `_Scorer`:** The `_raise_for_params` function is called with `method=None` in `_Scorer.__call__`. This results in the error message referencing `_Scorer` (the class name) instead of `_Scorer.__call__` (the method name), which was more precise in the original implementation.

## Evidence
*   **Problem 1 (MultiOutputEstimator):**
    *   `sklearn/multioutput.py:149`: `_raise_for_params(partial_fit_params, self, "partial_fit")`
    *   `sklearn/multioutput.py:920`: `_raise_for_params(fit_params, self, "fit")`
    *   Related test file: `sklearn/tests/test_multioutput.py` (no specific test for this negative case in the diff or implied by the PR description).
*   **Problem 2 (Pipeline):**
    *   `sklearn/pipeline.py:744`: `_raise_for_params(params, self, "decision_function")`
    *   `sklearn/pipeline.py:883`: `_raise_for_params(params, self, "transform")`
    *   `sklearn/pipeline.py:930`: `_raise_for_params(params, self, "inverse_transform")`
    *   Related test file: `sklearn/tests/test_pipeline.py` (no specific test for this negative case in the diff or implied by the PR description).
*   **Problem 3 (Scorer Error Message):**
    *   `sklearn/metrics/_scorer.py:255`: `_raise_for_params(kwargs, self, None)`
    *   `sklearn/utils/_metadata_requests.py:139`: `caller = f"{owner.__class__.__name__}.{method}" if method else owner.__class__.__name__` (This line dictates the message format when `method` is `None`).
    *   Original message in `sklearn/metrics/_scorer.py` before change: `"kwargs is only supported if enable_metadata_routing=True. See the User Guide for more information."`

## Impact
1.  **Untested Error Handling:** Without specific tests, regressions in the error handling for `MultiOutputEstimator` and `Pipeline` methods could go unnoticed. Users might pass unexpected parameters without receiving the intended `ValueError`, leading to silent failures or incorrect behavior when metadata routing is not enabled.
2.  **User Confusion:** The slightly less precise error message for `_Scorer.__call__` might cause minor confusion for users trying to debug issues related to metadata routing, as it refers to the class rather than the specific method being called.

## Recommendation (Fix / Tests / Risks)
1.  **Add Negative Tests for `MultiOutputEstimator`:** In `sklearn/tests/test_multioutput.py`, add new test cases that instantiate a `MultiOutputEstimator` (e.g., `MultiOutputClassifier` or `MultiOutputRegressor`) and call its `partial_fit` and `fit` methods with extra `partial_fit_params` or `fit_params` respectively, while `sklearn.set_config(enable_metadata_routing=False)` is active. Assert that a `ValueError` with the expected message is raised.
2.  **Add Negative Tests for `Pipeline`:** In `sklearn/tests/test_pipeline.py`, add new test cases that instantiate a `Pipeline` and call its `decision_function`, `transform`, and `inverse_transform` methods with extra `params` while `sklearn.set_config(enable_metadata_routing=False)` is active. Assert that a `ValueError` with the expected message is raised.
3.  **Refine `_Scorer` Error Message:** Consider passing `"__call__"` as the `method` argument to `_raise_for_params` in `sklearn/metrics/_scorer.py:255` to ensure the error message explicitly mentions `_Scorer.__call__`, maintaining consistency with the original message's precision.

## Traceability
@OmarManzoor @glemaitre