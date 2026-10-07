```
# Review Note — Evidence-Anchored

**Scope:** This PR transforms certain warnings into errors and removes deprecated positional arguments in preparation for version 1.1.

## Problem
1. The `_deprecate_positional_args` function is retained in the codebase despite no longer being used.
2. Removal of the `requires_y` tag in `_sequential.py` might affect estimators that rely on this tag for validation.
3. The removal of tests related to deprecated positional arguments might reduce test coverage for backward compatibility.

## Evidence
- `sklearn/utils/validation.py:33-46`: The `_deprecate_positional_args` function is still present but unused.
- `sklearn/feature_selection/_sequential.py:306-309`: The `requires_y` tag is removed without clear justification.
- `sklearn/metrics/tests/test_regression.py:444-462`: The test for deprecated positional arguments is removed entirely.

## Impact
- Retaining unused code like `_deprecate_positional_args` can lead to confusion and maintenance overhead.
- Removing the `requires_y` tag might cause issues with estimators that expect this tag for proper functionality, potentially leading to runtime errors.
- Eliminating tests for deprecated features without ensuring backward compatibility could lead to undetected regressions.

## Recommendation (Fix / Tests / Risks)
1. Remove the `_deprecate_positional_args` function if it is confirmed to be unnecessary, or document its purpose clearly if retained.
2. Re-evaluate the necessity of the `requires_y` tag and ensure that its removal does not affect any dependent functionality.
3. Consider maintaining a minimal set of tests for deprecated features to ensure backward compatibility, especially if users might still rely on them.

## Traceability
Not specified
```