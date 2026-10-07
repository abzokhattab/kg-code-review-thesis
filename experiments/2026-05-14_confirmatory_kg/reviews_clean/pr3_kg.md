```
# Review Note — Evidence-Anchored

**Scope:** This PR applies security patches to various components of the Grafana codebase, including access control, annotations, dashboard snapshots, plugin resources, SQL parsing, and more.

## Problem
1. **Potential Over-Restriction of Permissions**: Changes in `pkg/api/accesscontrol.go` and `pkg/api/annotations.go` modify the scope of permissions from `ac.ScopeAnnotationsAll` to `ac.ScopeAnnotationsTypeOrganization`, which might inadvertently restrict access for users who previously had broader permissions.
2. **Error Handling and Logging**: In `pkg/api/plugin_resource.go`, the introduction of a maximum body size for requests could lead to unhandled errors if not properly logged or communicated to the user.
3. **Cache Invalidation**: The changes in `pkg/services/accesscontrol/resourcepermissions/service.go` introduce cache invalidation logic that might not cover all edge cases, potentially leading to stale permission data being used.

## Evidence
- **pkg/api/accesscontrol.go:361-378**: Changes in permission scopes from `ac.ScopeAnnotationsAll` to `ac.ScopeAnnotationsTypeOrganization`.
- **pkg/api/plugin_resource.go:99-118**: Introduction of `http.MaxBytesReader` to limit request body size.
- **pkg/services/accesscontrol/resourcepermissions/service.go:225-377**: Addition of `clearUserPermissionCache` method for cache invalidation.

## Impact
- **Technical Impact**: The restriction of permission scopes could lead to users losing access to certain resources, impacting their ability to perform necessary actions. The error handling for oversized requests might not provide sufficient feedback to users, leading to confusion. Cache invalidation issues could result in incorrect permission checks, potentially allowing unauthorized access or denying legitimate access.

## Recommendation (Fix / Tests / Risks)
1. **Review Permission Changes**: Ensure that the change in permission scopes does not unintentionally restrict necessary access for users. Consider adding tests to verify that permissions are correctly applied.
2. **Enhance Error Handling**: Improve logging and user feedback for oversized request errors to ensure users understand why their requests are failing.
3. **Test Cache Invalidation**: Add tests to cover edge cases for cache invalidation to ensure that permission data is always up-to-date.

## Traceability
- **Code Owners**: Identity Access Team, Plugin Resource Team, SQL Parsing Team
```