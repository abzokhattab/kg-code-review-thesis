```
# Review Note — Evidence-Anchored

**Scope:** This PR adds validation for empty `Group`/`Resource` in the SQL backend's `ListModifiedSince` method, aligning it with the KV backend's behavior.

## Problem
1. The validation logic for `Group` and `Resource` is added directly in the `ListModifiedSince` method, which may not be the most appropriate location for input validation.
2. The error handling mechanism in the `ListModifiedSince` method could lead to silent failures if not properly managed.

## Evidence
- `pkg/storage/unified/sql/backend.go:1093-1098`: The validation for `Group` and `Resource` is implemented directly in the `ListModifiedSince` method.
- `pkg/storage/unified/sql/backend.go:1095`: The error is returned through a sequence, which might not be immediately apparent to the caller.

## Impact
- Placing validation logic directly in the `ListModifiedSince` method could lead to code duplication if similar validation is needed elsewhere.
- The current error handling approach might result in silent failures if the caller does not properly iterate over the sequence to check for errors.

## Recommendation (Fix / Tests / Risks)
1. Consider moving the validation logic to a separate validation function that can be reused across different methods.
2. Ensure that the error handling mechanism is robust and that errors are clearly communicated to the caller.
3. Add additional test cases to verify that errors are correctly propagated and handled by the caller.

## Traceability
Not specified
```