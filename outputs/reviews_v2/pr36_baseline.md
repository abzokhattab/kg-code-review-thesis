```
# Review Note — Evidence-Anchored

**Scope:** This PR adds validation to reject empty `Group` or `Resource` in the SQL backend's `ListModifiedSince` method, aligning it with the KV backend's behavior.

## Problem
1. The validation logic for `Group` and `Resource` is added directly in the `ListModifiedSince` method, which may not be the most appropriate location for input validation.
2. The error handling mechanism in the `ListModifiedSince` method could lead to confusion, as it returns a sequence with an error instead of directly returning an error.

## Evidence
- `pkg/storage/unified/sql/backend.go:1093-1097`: The validation for `Group` and `Resource` is implemented directly in the `ListModifiedSince` method.
- `pkg/storage/unified/sql/backend.go:1094`: The method returns a sequence with an error, which might not be intuitive for error handling.

## Impact
- Placing validation logic directly in the `ListModifiedSince` method could lead to code duplication if similar validation is needed elsewhere, reducing maintainability.
- The current error handling approach might lead to misuse or misunderstanding of the API, as consumers might not expect errors to be returned in a sequence.

## Recommendation (Fix / Tests / Risks)
1. Consider moving the validation logic to a separate validation function or method to improve code organization and reusability.
2. Refactor the error handling in `ListModifiedSince` to return an error directly if validation fails, rather than using a sequence to convey errors.
3. Ensure comprehensive test coverage for the new validation logic to verify that it behaves consistently across different scenarios.

## Traceability
Not specified
```