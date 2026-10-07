# Review Note — Evidence-Anchored

**Scope:** This PR updates the minimum `joblib` dependency to version 1.0.0 and removes compatibility code for older `joblib` versions (pre-0.12/0.13) across various modules.

## Problem
1.  **Potential CPU Count Over-estimation:** The removal of the version-specific check for `joblib.cpu_count()` in the build utilities might reintroduce issues with CPU over-estimation, particularly in CI or containerized environments, if `joblib` 1.0.0 does not fully address the underlying `loky#114` concern for all scenarios.
2.  **Subtle Parallel Backend Behavior Changes:** While the new `joblib.Parallel` API (`prefer`, `require`) is syntactically correct for `joblib` 1.0.0, there's a risk of subtle behavioral differences compared to the older `backend` parameter, which the removed `_joblib_parallel_args` utility explicitly managed. This could lead to regressions in parallel execution, especially for critical `sharedmem` use cases.
3.  **Test Coverage Gap for Parallel Arguments:** The removal of dedicated tests for `_joblib_parallel_args` in `test_fixes.py` creates a gap. Although the compatibility utility is gone, the robust testing of `joblib.Parallel`'s `prefer` and `require` arguments (especially `sharedmem`) is crucial to prevent regressions with future `joblib` updates or environment changes.

## Evidence
*   **CPU Count Over-estimation:**
    *   `sklearn/_build_utils/__init__.py:64-68`: The `if LooseVersion(joblib.__version__) > LooseVersion("0.13.0")` condition and its associated `n_jobs = joblib.cpu_count()` assignment are removed. The original comment explicitly mentioned `earlier joblib versions don't account for CPU affinity constraints, and may over-estimate the number of available CPU particularly in CI (cf loky#114)`.
    *   This `n_jobs` value is used by `cythonize_extensions` during the build process.
*   **Subtle Parallel Backend Behavior Changes:**
    *   `sklearn/utils/fixes.py:58-116`: The `_joblib_parallel_args` function, which mapped `prefer`/`require` to `backend` for older `joblib` versions, has been entirely removed.
    *   `sklearn/ensemble/_forest.py:249, 282, 471, 625, 879, 1002`: Calls to `Parallel` are changed from `**_joblib_parallel_args(prefer="threads")` or `**_joblib_parallel_args(require="sharedmem")` to direct `prefer="threads"` or `require="sharedmem"`.
    *   `sklearn/linear_model/_logistic.py:1585, 2150`: Similar changes from `**_joblib_parallel_args(prefer=prefer)` to direct `prefer=prefer`.
    *   `sklearn/neighbors/_base.py:795, 1133`: Removal of `parse_version` checks and direct use of `prefer="threads"`.
    *   `sklearn/pipeline.py:326-339`: Simplified `joblib.Memory` API checks, removing `hasattr(memory, "cachedir")` and `memory.cachedir` for `joblib < 0.11` compatibility.
*   **Test Coverage Gap for Parallel Arguments:**
    *   `sklearn/utils/tests/test_fixes.py:11-45`: The `test_joblib_parallel_args` function, which specifically tested the compatibility logic for `joblib.Parallel` arguments, has been removed.
    *   `sklearn/tests/test_config.py:110`: Removal of `parse_version` check for `joblib < 0.12` and `loky` backend.
    *   `sklearn/utils/tests/test_parallel.py:19`: Removal of `joblib.__version__ < LooseVersion("0.12")` check.
    *   Critical callers using `require="sharedmem"`: `sklearn/ensemble/_forest.py` (in `predict_proba` and `predict` methods) and `sklearn/linear_model/_stochastic_gradient.py` (in `_fit_multiclass`).

## Impact
*   **CPU Count Over-estimation:** Incorrect `n_jobs` during the build process could lead to inefficient compilation (under-utilization) or, more critically, resource contention and build failures (over-utilization) in environments with strict CPU limits, such as CI pipelines or Docker containers.
*   **Subtle Parallel Backend Behavior Changes:** Regressions in parallel execution could manifest as incorrect model predictions, deadlocks, or significant performance degradation, especially for estimators like `RandomForestClassifier` (via `predict_proba` and `predict`) and `SGDClassifier` (via `_fit_multiclass`) that heavily rely on `joblib.Parallel` with `sharedmem` for efficiency.
*   **Test Coverage Gap for Parallel Arguments:** Without explicit tests for `joblib.Parallel`'s `prefer` and `require` arguments, future changes in `joblib` or the execution environment could silently break parallel processing, leading to hard-to-diagnose issues in core estimators.

## Recommendation (Fix / Tests / Risks)
1.  **Verify `joblib.cpu_count()` Behavior:**
    *   **Action:** Confirm with `joblib` maintainers or through targeted testing that `joblib.cpu_count()` in version 1.0.0 reliably accounts for CPU affinity constraints and avoids over-estimation in all relevant environments (e.g., CI, containerized setups), fully addressing the `loky#114` concern.
    *   **Tests:** If direct confirmation is not sufficient, consider adding a new test case in `sklearn/tests/` (e.g., `sklearn/tests/test_build_utils.py` if created, or an existing relevant test file) that specifically asserts the correct behavior of `joblib.cpu_count()` under simulated CPU-constrained conditions.
2.  **Review `joblib.Parallel` Backend Behavior:**
    *   **Action:** Conduct a thorough review of `joblib` 1.0.0 release notes and documentation for any non-obvious behavioral changes between the old `backend='threading'`/`'multiprocessing'` and the new `prefer='threads'`/`'processes'` or `require='sharedmem'` parameters, especially concerning memory sharing and object serialization.
    *   **Tests:** Ensure that existing tests for parallel estimators, such as `sklearn/ensemble/tests/test_forest.py` (e.g., `test_forest_parallel_predict_proba`) and `sklearn/linear_model/tests/test_stochastic_gradient.py` (e.g., `test_sgd_multiclass_sparse_data`), are robust enough to catch regressions in correctness and performance when `require="sharedmem"` is used.
3.  **Add Explicit `joblib.Parallel` Argument Tests:**
    *   **Tests:** Introduce new, explicit test cases in `sklearn/utils/tests/test_parallel.py` or `sklearn/tests/test_config.py` that directly test `joblib.Parallel` with various combinations of `n_jobs`, `prefer`, and `require` (especially `sharedmem`). These tests should assert expected behavior, such as correct results, absence of deadlocks, and potentially expected memory usage patterns, effectively replacing the coverage lost by removing `test_joblib_parallel_args`.

## Traceability
Not specified