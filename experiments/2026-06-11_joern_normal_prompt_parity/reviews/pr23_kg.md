```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the handling of deprecated positional arguments and transforms certain warnings into errors in the scikit-learn codebase.

## Problem
1. The `_deprecate_positional_args` function is retained in the codebase despite being unused, potentially leading to confusion or unnecessary maintenance.
2. The removal of the `requires_y` tag in `sklearn/feature_selection/_sequential.py` might affect the behavior of estimators that rely on this tag for validation.
3. The transformation of warnings into errors in `sklearn/utils/estimator_checks.py` could lead to unexpected failures in downstream code that has not yet adapted to these changes.

## Evidence
- `sklearn/utils/validation.py:33-46`: The `_deprecate_positional_args` function is no longer used but remains in the codebase.
- `sklearn/feature_selection/_sequential.py:306`: The `requires_y` tag is removed, which might affect estimators that depend on this tag.
- `sklearn/utils/estimator_checks.py:3636-3683`: Warnings are replaced with assertions, which could cause tests to fail if the conditions are not met.

## Impact
- Retaining unused code like `_deprecate_positional_args` can lead to confusion and unnecessary maintenance overhead.
- Removing the `requires_y` tag might cause issues with estimators that expect this tag to be present, potentially leading to incorrect behavior or errors.
- Transforming warnings into errors without adequate communication or adaptation time could lead to unexpected test failures and integration issues for users who have not updated their code.

## Recommendation (Fix / Tests / Risks)
1. Consider removing the `_deprecate_positional_args` function if it is confirmed to be unnecessary, or document its purpose clearly if it is to be retained for future use.
2. Re-evaluate the removal of the `requires_y` tag to ensure that it does not negatively impact any dependent code or estimators.
3. Provide clear documentation and communication regarding the change from warnings to errors, and consider a phased approach to allow users time to adapt.

## Traceability
Not specified
```