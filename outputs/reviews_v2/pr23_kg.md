```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses the cleanup of deprecated positional arguments and transforms certain warnings into errors in the scikit-learn codebase.

## Problem
1. The `_deprecate_positional_args` function is retained in the codebase despite being unused, potentially leading to confusion or unnecessary maintenance.
2. The removal of the `requires_y` tag in `sklearn/feature_selection/_sequential.py` might affect the behavior of estimators that rely on this tag for validation.
3. The transformation of warnings to errors in `sklearn/utils/estimator_checks.py` could lead to unexpected failures in downstream code that has not been updated to handle these changes.

## Evidence
- `sklearn/utils/validation.py:33-46`: The `_deprecate_positional_args` function is no longer used but remains in the codebase.
- `sklearn/feature_selection/_sequential.py:306`: The `requires_y` tag is removed, which might affect feature selection processes.
- `sklearn/utils/estimator_checks.py:3636-3683`: Warnings are replaced with assertions, which could cause tests or dependent code to fail if they have not been updated.

## Impact
- Retaining unused code like `_deprecate_positional_args` can lead to confusion and unnecessary maintenance overhead.
- Removing the `requires_y` tag might lead to incorrect assumptions about the necessity of the target variable `y` in certain estimators, potentially causing runtime errors.
- Changing warnings to errors without adequate communication or transition period could break existing codebases that depend on the previous behavior, leading to integration issues.

## Recommendation (Fix / Tests / Risks)
1. Consider removing the `_deprecate_positional_args` function entirely if it is not planned for future use, or document its purpose clearly if it is to be retained.
2. Re-evaluate the necessity of the `requires_y` tag removal and ensure that all dependent code is updated to handle this change appropriately.
3. Provide clear documentation and communication regarding the change from warnings to errors, and consider a phased approach to allow dependent projects time to adapt.

## Traceability
- Code Owners: Not specified
```