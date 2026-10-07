# Review Note — Evidence-Anchored

**Scope:** This PR moves Cython sorting functions and their associated test from `sklearn/tree/` to `sklearn/utils/_sorting.pyx` to centralize utility functions.

## Problem
1.  **Unused and Potentially Misleading `swap` Function:** A `cdef inline void swap` function remains in `sklearn/tree/_partitioner.pyx` with a `float32_t*` signature. However, the `sort` logic (including `introsort` and `heapsort`) that previously used a `swap` helper has been moved to `sklearn/utils/_sorting.pyx` and now exclusively uses `dual_swap`. This leaves an unused function in `_partitioner.pyx` that could cause confusion or be mistakenly used in the future.
2.  **Incomplete `floating` Type Test Coverage for `sort`:** The `sort` function in `sklearn/utils/_sorting.pyx` is designed to handle `floating*` (a fused type for both `float32_t` and `float64_t`). However, the moved non-regression test `test_sort_log2_build` in `sklearn/utils/tests/test_sorting.py` only verifies its behavior with `np.float32` inputs, leaving `float64_t` inputs untested for this critical sorting routine.

## Evidence
*   **Problem 1:**
    *   `sklearn/tree/_partitioner.pyx`: Lines 694-695 show the definition of `cdef inline void swap(float32_t* feature_values, intp_t* samples, intp_t i, intp_t j)`. This function is not called by any remaining code in `_partitioner.pyx` after the `sort` logic was moved.
    *   `sklearn/tree/_partitioner.pyx`: Lines 697-820 (original content) were removed, which included the previous `sort` function and its internal `swap` helper.
    *   `sklearn/utils/_sorting.pyx`: Lines 100-214 contain the moved `sort`, `introsort`, `heapsort`, `median3`, and `sift_down` functions, all of which now exclusively call `dual_swap` (defined at `sklearn/utils/_sorting.pyx:12-17`).
*   **Problem 2:**
    *   `sklearn/utils/_sorting.pxd`: Lines 7-10 define the `sort` function signature as `cdef void sort(floating* feature_values, intp_t* samples, intp_t n)`.
    *   `sklearn/utils/_sorting.pyx`: Lines 100-104 implement `sort` using `floating*`.
    *   `sklearn/utils/tests/test_sorting.py`: Lines 14-15 show `feature_values` being created with `astype(np.float32)`, specifically `some = rng.normal(loc=0.0, scale=10.0, size=10).astype(np.float32)`. There is no corresponding test case for `np.float64`.

## Impact
*   **Problem 1:** The presence of an unused `swap` function in `_partitioner.pyx` introduces code clutter and potential for confusion. It could lead to future maintainers mistakenly using it or assuming it's part of the active sorting logic, potentially introducing bugs or making refactoring more difficult.
*   **Problem 2:** Without explicit testing for `float64_t` inputs, regressions or subtle behavioral differences for double-precision floating-point numbers could go unnoticed. This could affect the correctness or numerical stability of algorithms in `sklearn.tree._criterion.pyx` or `sklearn.tree._partitioner.pyx` (which call the new `sort` function) when processing `float64_t` features, potentially leading to incorrect model training or predictions.

## Recommendation (Fix / Tests / Risks)
1.  **Remove Unused `swap` Function:** Delete the `cdef inline void swap` function from `sklearn/tree/_partitioner.pyx` (lines 694-695 in the diff) entirely, as it is no longer used by any active code after the sorting logic was moved.
2.  **Add `float64_t` Test Coverage:** Extend `sklearn/utils/tests/test_sorting.py::test_sort_log2_build` to include a test case where `feature_values` are of type `np.float64`. This could be achieved by parameterizing the test or adding a new test function, for example, `test_sort_log2_build_float64`, to ensure the `sort` function handles both `float32_t` and `float64_t` correctly as per its `floating` fused type definition.

## Traceability
Not specified