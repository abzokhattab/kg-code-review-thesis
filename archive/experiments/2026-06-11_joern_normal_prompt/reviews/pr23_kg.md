```
# Review Note — Evidence-Anchored

**Scope:** This PR removes deprecated positional argument warnings and updates validation checks in various sklearn modules.

## Problem
1. Removal of the `requires_y` tag in `_sequential.py` might affect estimators that rely on this tag for validation.
2. The `_deprecate_positional_args` decorator is removed from several functions, which might lead to unexpected behavior if positional arguments are used.
3. The check for `n_features_in_` in `estimator_checks.py` has been altered, potentially affecting the validation of custom estimators.

## Evidence
- `sklearn/feature_selection/_sequential.py:306`: The `requires_y` tag is removed.
- `sklearn/inspection/_plot/partial_dependence.py:1266`: The `_deprecate_positional_args` decorator is removed.
- `sklearn/metrics/_regression.py:287`: The `_deprecate_positional_args` decorator is removed.
- `sklearn/utils/estimator_checks.py:3636`: The warning for missing `n_features_in_` is removed.

## Impact
- **Technical Impact:** 
  - Removing the `requires_y` tag could lead to incorrect assumptions about the necessity of the target variable `y` in certain estimators, potentially causing runtime errors.
  - Without the `_deprecate_positional_args` decorator, users might inadvertently pass positional arguments, leading to silent failures or incorrect function behavior.
  - The change in `n_features_in_` validation might allow non-compliant estimators to pass checks, leading to integration issues in pipelines or when used with other sklearn components.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Re-evaluate the necessity of the `requires_y` tag and ensure that its removal does not affect any dependent functionality or tests.
2. **Tests:** Add or update tests to ensure that functions behave correctly without the `_deprecate_positional_args` decorator, especially in user-facing APIs.
3. **Risks:** Consider the implications of the `n_features_in_` check removal on custom estimators and ensure that documentation is updated to reflect these changes.

## Traceability
- Code Owners: sklearn/compose, sklearn/feature_selection, sklearn/inspection, sklearn/metrics, sklearn/utils teams
```