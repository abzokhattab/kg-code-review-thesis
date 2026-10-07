```
# Review Note — Evidence-Anchored

**Scope:** This PR adds validation to reject empty `Group`/`Resource` in the SQL backend's `ListModifiedSince` method, aligning it with the KV backend's behavior.

## Problem
1. The validation logic for `Group` and `Resource` is added directly in the `ListModifiedSince` method, which may not be the most appropriate location for such checks.
2. The error handling mechanism in the `ListModifiedSince` method could lead to silent failures if not properly managed.

## Evidence
- `pkg/storage/unified/sql/backend.go:1093-1098`: Validation logic for `Group` and `Resource` is directly embedded in the `ListModifiedSince` method.
- `pkg/storage/unified/sql/backend.go:1095`: The error is returned via a sequence function, which might not be immediately clear to all developers.

## Impact
- Placing validation logic directly in the `ListModifiedSince` method could lead to code duplication if similar checks are needed elsewhere, reducing maintainability.
- The current error handling approach might lead to silent failures if the sequence function's error is not properly checked by the caller, potentially causing unexpected behavior in production.

## Recommendation (Fix / Tests / Risks)
1. Consider refactoring the validation logic into a separate function that can be reused across different methods, improving code maintainability.
2. Ensure that the error handling mechanism is robust and that any errors are properly logged or handled to prevent silent failures.
3. Add additional test cases to verify that the error handling mechanism works as expected and that errors are not silently ignored.

## Traceability
Not specified
```