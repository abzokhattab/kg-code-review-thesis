```
# Review Note — Evidence-Anchored

**Scope:** This PR applies security patches to the Grafana codebase, focusing on access control, annotations, and plugin resource handling.

## Problem
1. **Potential Overlooked Permissions Change**: The change from `ac.ScopeAnnotationsAll` to `ac.ScopeAnnotationsTypeOrganization` may inadvertently restrict access that was previously granted.
2. **Error Handling in SQL Parsing**: The SQL parser changes introduce new error handling that might not be fully covered by existing tests.
3. **Cache Invalidation Logic**: The addition of cache invalidation logic in `clearUserPermissionCache` might not be adequately tested for concurrency issues.

## Evidence
- `pkg/api/accesscontrol.go:361-378`: Changes in scope from `ac.ScopeAnnotationsAll` to `ac.ScopeAnnotationsTypeOrganization`.
- `pkg/expr/sql/parser_allow.go:15-82`: New error handling logic in SQL parsing.
- `pkg/services/accesscontrol/resourcepermissions/service.go:225-377`: Introduction of `clearUserPermissionCache` method.

## Impact
- **Permissions Change**: Users might lose access to annotations they previously had, leading to potential disruptions in workflows.
- **SQL Parsing Errors**: Unhandled SQL parsing errors could lead to unexpected failures in query execution.
- **Cache Invalidation**: Incorrect cache invalidation could lead to stale permissions being used, affecting access control decisions.

## Recommendation (Fix / Tests / Risks)
1. **Review Permissions Changes**: Ensure that the change in scope does not unintentionally restrict necessary access. Consider adding tests to verify expected permissions.
2. **Enhance SQL Parsing Tests**: Add tests to cover new error handling paths in the SQL parser to ensure robustness.
3. **Test Cache Invalidation**: Implement tests to simulate concurrent access and verify that cache invalidation logic works correctly under load.

## Traceability
Not specified
```