```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the `StorageBackend.ListModifiedSince` function to support cross-namespace queries by allowing an empty namespace, affecting both KV and SQL backends.

## Problem
1. **Potential SQL Injection Risk**: The SQL query construction in `data/resource_history_list_since_modified.sql` uses conditional logic that could potentially lead to SQL injection if not properly handled.
2. **Insufficient Test Coverage for Edge Cases**: While the PR includes tests for cross-namespace functionality, it lacks tests for edge cases such as very large datasets or performance under high load.
3. **Backward Compatibility Concerns**: The change in validation logic for namespaces might affect existing integrations that rely on strict namespace checks.

## Evidence
- `pkg/storage/unified/sql/data/resource_history_list_since_modified.sql:7-9`: Conditional SQL logic that could be vulnerable if inputs are not sanitized.
- `pkg/storage/unified/resource/storage_backend_test.go:1078-136`: Tests added for cross-namespace functionality but missing stress tests for performance.
- `pkg/storage/unified/sql/queries.go:464-466`: Removal of namespace validation which might impact existing systems relying on this check.

## Impact
- **Technical Impact**: The potential for SQL injection could lead to security vulnerabilities. Lack of performance testing might result in degraded system performance under load. Changes in validation logic could break existing integrations that expect strict namespace validation.
- **Risk**: High risk of security vulnerabilities and performance issues if not addressed. Medium risk of breaking changes for existing users.

## Recommendation (Fix / Tests / Risks)
1. **Fix**: Ensure all SQL inputs are properly sanitized and consider using parameterized queries to prevent SQL injection.
2. **Tests**: Add performance and stress tests to evaluate the system's behavior under high load and with large datasets.
3. **Risks**: Communicate changes in validation logic to stakeholders and provide guidance on adapting to the new behavior.

## Traceability
- Code Owners: Not specified
```