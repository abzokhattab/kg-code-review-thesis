# Review Note — Evidence-Anchored

**Scope:** This PR applies several security patches, including tightening access control for annotations, fixing SQL expression parsing vulnerabilities, introducing request body size limits, correcting RBAC cache invalidation, and improving robustness in various data source macros and proxy address parsing.

## Problem
1.  **Potential Security Regression in Annotation Type Resolution:** The change in `AnnotationTypeScopeResolver` replaces a carefully constructed `tempUser` with specific read permissions for annotation type resolution with a `serviceIdentity`. The permissions implicitly granted to a `serviceIdentity` might be broader than intended for this specific read operation, potentially leading to unintended information disclosure or a bypass of granular access controls if the annotation data itself is sensitive.
2.  **Security Vulnerability in Dashboard Import Permissions:** The `ImportDashboard` function now only applies default permissions if `dto.Dashboard.ID == 0` (i.e., for new dashboards). If an existing dashboard is updated via import (where `ID != 0`), its existing permissions are preserved. This could be a security risk if a dashboard with overly permissive ACLs is imported from an external source, as it would retain those permissions rather than inheriting the target Grafana instance's default, more restrictive settings.
3.  **Incomplete Test Coverage for Critical Security Fixes:** While some new tests are added, there's a lack of explicit test cases for the significant SQL expression parsing security fixes and the annotation access control changes. Without targeted tests, it's difficult to verify that previously exploitable scenarios are now correctly blocked and that legitimate functionality remains intact.

## Evidence
*   **Potential Security Regression in Annotation Type Resolution:**
    *   `pkg/api/annotations.go:602-619` (removal of `tempUser` creation)
    *   `pkg/api/annotations.go:621` (introduction of `tmpCtx, tempUser := identity.WithServiceIdentity(ctx, orgID)`)
*   **Security Vulnerability in Dashboard Import Permissions:**
    *   `pkg/services/dashboards/service/dashboard_service.go:926-928` (conditional application of `setDefaultPermissions`)
*   **Incomplete Test Coverage for Critical Security Fixes:**
    *   No new or updated tests explicitly covering the SQL parser changes in `pkg/expr/sql/parser_allow.go`.
    *   No new or updated tests explicitly covering the annotation access control changes in `pkg/api/accesscontrol.go` and `pkg/services/sqlstore/migrations/accesscontrol/scope_migrator.go`.

## Impact
*   **Potential Security Regression in Annotation Type Resolution:** If `identity.WithServiceIdentity` grants excessive permissions, it could allow internal services to access annotation metadata that should be restricted, potentially leading to information leakage or a bypass of the intended granular access control for annotations.
*   **Security Vulnerability in Dashboard Import Permissions:** An attacker or misconfigured system could import a dashboard with broad permissions (e.g., `public:write`) into a Grafana instance, and these permissions would persist, potentially exposing sensitive dashboards or allowing unauthorized modifications.
*   **Incomplete Test Coverage for Critical Security Fixes:** Without specific tests, there's a higher risk that the security fixes might not fully address the vulnerabilities, could introduce regressions, or might be inadvertently broken in future changes without detection. This undermines confidence in the effectiveness of the security patches.

## Recommendation (Fix / Tests / Risks)
1.  **Clarify `serviceIdentity` Permissions for Annotation Resolution:**
    *   **Fix:** Explicitly define and document the permissions granted by `identity.WithServiceIdentity` when used in `AnnotationTypeScopeResolver`. If the `serviceIdentity` provides overly broad access, consider creating a more narrowly scoped `identity.Requester` specifically for annotation type resolution, granting only `accesscontrol.ActionAnnotationsRead` on `ScopeAnnotationsTypeOrganization` (or `ScopeAnnotationsAll` if necessary for legacy annotations).
    *   **Tests:** Add unit tests for `AnnotationTypeScopeResolver` to ensure that the `serviceIdentity` correctly resolves annotation types without granting unintended elevated privileges.
    *   **Risks:** If not addressed, this could be a subtle security regression.
2.  **Re-evaluate Dashboard Import Permission Logic:**
    *   **Fix:** Reconsider the conditional application of `setDefaultPermissions` in `ImportDashboard`. If the intent is to *always* apply default permissions on import (to ensure security posture), remove the `if dto.Dashboard.ID == 0` condition. If the intent is to preserve existing permissions on update, add a clear comment explaining the security implications and consider introducing an explicit `applyDefaultPermissions` flag to the `ImportDashboard` DTO, allowing callers to choose the behavior.
    *   **Tests:** Add integration tests for `ImportDashboard` to cover scenarios where existing dashboards are imported with different permission sets, verifying that the resulting permissions align with the intended security policy.
    *   **Risks:** Leaving this as is could lead to security vulnerabilities where imported dashboards retain overly permissive ACLs.
3.  **Enhance Test Coverage for Security Patches:**
    *   **Tests:**
        *   **SQL Parser:** Add new unit/integration tests for `pkg/expr/sql/parser_allow.go` that include previously vulnerable SQL queries (e.g., queries using `@@system` variables, `SELECT ... FOR UPDATE`, functions in `OrderBy`/`With`/`Limit`/`Window` clauses) and assert that they are now correctly blocked. Also, ensure legitimate queries still pass.
        *   **Annotation Access Control:** Add integration tests to verify that Viewer/Editor roles can no longer manage dashboard-specific annotations by default, and that the database migration correctly updates existing `annotations:*` scopes to `annotations:type:organization`.
    *   **Risks:** Insufficient testing increases the risk of regressions or incomplete fixes for critical security vulnerabilities.

## Traceability
Not specified