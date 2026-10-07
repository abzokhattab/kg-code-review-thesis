```
# Review Note — Evidence-Anchored

**Scope:** This PR transforms certain warnings into errors and removes deprecated positional arguments in preparation for version 1.1.

## Problem
1. The `_deprecate_positional_args` function is retained in the codebase despite being unused.
2. Removal of the `requires_y` tag in `_sequential.py` might affect estimators that rely on this tag for validation.
3. The test for deprecated positional arguments in `test_regression.py` has been removed without replacement, potentially reducing test coverage.

## Evidence
- `sklearn/utils/validation.py:33-46`: The `_deprecate_positional_args` function is no longer used but remains in the codebase.
- `sklearn/feature_selection/_sequential.py:306`: The `requires_y` tag has been removed.
- `sklearn/metrics/tests/test_regression.py:444-463`: The test `test_deprecation_positional_arguments_mape` has been removed.

## Impact
- Retaining unused code like `_deprecate_positional_args` can lead to confusion and maintenance overhead.
- Removing the `requires_y` tag without ensuring all dependent components are updated could lead to runtime errors if any estimator still relies on this tag.
- Eliminating tests without replacements can decrease the robustness of the codebase, potentially allowing regressions to go unnoticed.

## Recommendation (Fix / Tests / Risks)
1. Consider removing `_deprecate_positional_args` entirely if there is no foreseeable use, or document its purpose clearly if it is to be retained.
2. Verify that the removal of the `requires_y` tag does not affect any existing functionality or add alternative validation mechanisms if necessary.
3. Replace the removed test with new tests that ensure the same level of coverage for positional argument handling, especially in public APIs.

## Traceability
Not specified
```