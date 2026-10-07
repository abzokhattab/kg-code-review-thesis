```
# Review Note — Evidence-Anchored

**Scope:** This PR applies security patches to various components of the Grafana codebase, including access control, annotations, dashboard snapshots, plugin resources, SQL parsing, and more.

## Problem
1. **Access Control Changes**: The modification of access control scopes in `pkg/api/accesscontrol.go` could inadvertently restrict or expand permissions beyond intended levels.
2. **SQL Parsing Logic**: Changes in `pkg/expr/sql/parser_allow.go` introduce new logic for SQL node validation, which might lead to unexpected query rejections or security bypasses.
3. **Resource Permission Caching**: The addition of cache clearing logic in `pkg/services/accesscontrol/resourcepermissions/service.go` could introduce performance overhead or race conditions.

## Evidence
- **Access Control Changes**: `pkg/api/accesscontrol.go:360-377` - Changes from `ScopeAnnotationsAll` to `ScopeAnnotationsTypeOrganization`.
- **SQL Parsing Logic**: `pkg/expr/sql/parser_allow.go:16-93` - Introduction of `walkNodes` function and changes to node validation logic.
- **Resource Permission Caching**: `pkg/services/accesscontrol/resourcepermissions/service.go:219-371` - Addition of `clearUserPermissionCache` method and its integration.

## Impact
- **Access Control Changes**: Incorrect scope adjustments could lead to unauthorized access or denial of access to necessary resources, impacting user roles and permissions.
- **SQL Parsing Logic**: Misconfigured SQL parsing could result in legitimate queries being blocked or malicious queries being allowed, affecting data integrity and security.
- **Resource Permission Caching**: Inefficient cache management might degrade performance, especially under high load, and could lead to stale permission data being used.

## Recommendation (Fix / Tests / Risks)
1. **Access Control Changes**: Review and verify the intended scope changes with the identity-access team to ensure they align with security policies.
2. **SQL Parsing Logic**: Add comprehensive tests to cover new SQL parsing logic, ensuring all edge cases are handled and no regressions occur.
3. **Resource Permission Caching**: Conduct performance testing to assess the impact of cache clearing and consider optimizing the cache invalidation strategy.

## Traceability
- **Access Control**: Identity-Access Team
- **SQL Parsing**: Database Team
- **Resource Permission Caching**: Access Control Team
```