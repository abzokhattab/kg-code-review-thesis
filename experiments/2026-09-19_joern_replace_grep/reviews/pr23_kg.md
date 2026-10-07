```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses the cleanup of deprecated positional arguments and transforms certain warnings into errors in the scikit-learn codebase.

## Problem
1. The `_deprecate_positional_args` function is retained in the codebase despite being unused.
2. Removal of the `requires_y` tag in `_sequential.py` without clear justification or replacement.
3. The test for deprecated positional arguments in `test_regression.py` has been removed, potentially reducing test coverage.

## Evidence
- `sklearn/utils/validation.py:33-46`: The `_deprecate_positional_args` function is retained but not used anywhere in the current codebase.
- `sklearn/feature_selection/_sequential.py:306`: The `requires_y` tag is removed without a replacement or explanation.
- `sklearn/metrics/tests/test_regression.py:444-463`: The test `test_deprecation_positional_arguments_mape` is removed, which previously ensured warnings were triggered for deprecated positional arguments.

## Impact
- Retaining unused code like `_deprecate_positional_args` can lead to confusion and maintenance overhead.
- Removing the `requires_y` tag without a replacement might lead to incorrect assumptions about the estimator's requirements, potentially causing runtime errors.
- Eliminating tests for deprecated features without ensuring equivalent coverage elsewhere can lead to regressions and undetected issues in future updates.

## Recommendation (Fix / Tests / Risks)
1. Consider removing the `_deprecate_positional_args` function if it is truly unnecessary, or document its purpose and future plans clearly if it is to be retained.
2. Re-evaluate the removal of the `requires_y` tag in `_sequential.py` and ensure that the estimator's requirements are clearly documented and enforced.
3. Ensure that the removal of the `test_deprecation_positional_arguments_mape` does not reduce test coverage by verifying that similar tests exist or by adding new tests to cover the same scenarios.

## Traceability
Not specified
```