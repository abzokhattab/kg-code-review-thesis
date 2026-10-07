```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses the cleanup of deprecated positional arguments and transforms certain warnings into errors in the scikit-learn codebase.

## Problem
1. The `_deprecate_positional_args` function is retained in the codebase despite being unused, potentially leading to confusion or unnecessary maintenance.
2. Removal of the `requires_y` tag in `sklearn/feature_selection/_sequential.py` without clear justification or alternative handling.
3. The test for deprecation warnings related to positional arguments has been removed, which might reduce test coverage for deprecated functionality.

## Evidence
- `sklearn/utils/validation.py:33-46`: The `_deprecate_positional_args` function is still present but not used anywhere in the current codebase.
- `sklearn/feature_selection/_sequential.py:306`: The `requires_y` tag has been removed without replacement or explanation.
- `sklearn/metrics/tests/test_regression.py:444-462`: The test `test_deprecation_positional_arguments_mape` has been removed, which previously ensured that deprecation warnings were correctly issued.

## Impact
- Retaining unused code like `_deprecate_positional_args` can lead to confusion and unnecessary maintenance overhead.
- Removing the `requires_y` tag without a clear alternative might lead to incorrect assumptions about the estimator's requirements, potentially causing runtime errors.
- Eliminating tests for deprecated functionality could lead to regressions or missed warnings in future updates, reducing the robustness of the library.

## Recommendation (Fix / Tests / Risks)
1. Consider removing the `_deprecate_positional_args` function if it is truly obsolete, or document its intended future use to avoid confusion.
2. Re-evaluate the removal of the `requires_y` tag and ensure that its functionality is either not needed or is handled elsewhere.
3. Restore or replace the removed test for deprecation warnings to maintain test coverage and ensure deprecated functionalities are correctly flagged.

## Traceability
Not specified
```