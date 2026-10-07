```
# Review Note — Evidence-Anchored

**Scope:** This PR adds validation to reject empty `Group`/`Resource` in the SQL backend's `ListModifiedSince` method, aligning it with the KV backend's behavior.

## Problem
1. The validation logic for `Group` and `Resource` is added directly in the `ListModifiedSince` method, which may not be the most appropriate location for such checks.
2. The integration test coverage for the new validation logic may not be comprehensive enough to ensure all edge cases are handled.

## Evidence
- `pkg/storage/unified/sql/backend.go:1093-1098`: The validation logic for `Group` and `Resource` is directly embedded in the `ListModifiedSince` method.
- `pkg/storage/unified/testing/storage_backend.go:726-746`: The new subtest checks for missing `Group` or `Resource`, but only covers two specific cases.

## Impact
- Embedding validation logic directly in the `ListModifiedSince` method could lead to code duplication if similar checks are needed elsewhere, reducing maintainability.
- Insufficient test coverage might miss edge cases, potentially allowing invalid inputs to pass through in certain scenarios, leading to inconsistent behavior across different backends.

## Recommendation (Fix / Tests / Risks)
1. Consider refactoring the validation logic into a separate function or method that can be reused across different parts of the codebase to improve maintainability.
2. Expand the test cases in `pkg/storage/unified/testing/storage_backend.go` to cover additional edge cases, such as null values or unexpected data types, to ensure robustness.
3. Review the integration with other parts of the system to ensure that the new validation logic does not introduce any unintended side effects.

## Traceability
- Code Owners: Unified Storage Team
```