# Review Note — Evidence-Anchored

**Scope:** This PR applies several security patches, including tightening access control for annotations, introducing request body size limits for plugin resources and live push, hardening SQL expression parsing, and refining dashboard import permission handling and datasource macro validation.

## Integration Risk

*   `pkg/middleware/auth.go`: The changes in `pkg/api/annotations.go` to use `identity.Requester` and `identity.WithServiceIdentity` for resolving annotation types could subtly change how user context and permissions are handled for annotation-related requests. If `auth.go` makes assumptions about the `user.SignedInUser` type or its population, this change could lead to unexpected authorization failures or bypasses.
*   `pkg/cmd/grafana-cli/commands/datamigrations/to_unified_storage.go`: The new `AnnotationsAllScopeReplacementMigration` in `pkg/services/sqlstore/migrations/accesscontrol/scope_migrator.go` directly modifies the `permission` table. If `to_unified_storage.go` has its own logic for migrating or handling permissions, there's a risk of conflict or unexpected behavior if it runs before/after this new migration, or if it makes assumptions about the `annotations:*` scope that no longer hold.
*   `apps/alerting/alertenrichment/pkg/apis/alertenrichment/v1beta1/object.go`, `apps/alerting/alertenrichment/pkg/apis/alertenrichment/v1beta1/zz_generated.openapi.go`, `apps/alerting/alertenrichment/pkg/apis/alertenrichment/v1beta1/types.go`, `apps/alerting/historian/pkg/apis/alertinghistorian_manifest.go`: The changes in `pkg/api/accesscontrol.go` to replace `ac.ScopeAnnotationsAll` with `ac.ScopeAnnotationsTypeOrganization` for basic Viewer/Editor roles significantly tightens permissions. Any alerting component that previously relied on `ScopeAnnotationsAll` to read/write *dashboard-level* annotations via these basic roles will now fail, potentially breaking existing alerting configurations or enrichment processes.
*   `pkg/infra/usagestats/service/service.go`, `pkg/infra/usagestats/service/api.go`, `devenv/docker/blocks/stateful_webhook/main.go`: The introduction of `maxResourceBodySize` in `pkg/api/plugin_resource.go` and `500*1024` limit in `pkg/services/live/pushhttp/push.go` could cause `413 Request Entity Too Large` errors for existing clients that send large payloads to plugin resources or live push endpoints. Usage stats or dev environment webhooks might be affected if they exceed these new limits.

## Test Coverage Assessment

*   `pkg/services/accesscontrol/acimpl/accesscontrol_test.go`: This test suite should cover the cache invalidation logic added to `pkg/services/accesscontrol/resourcepermissions/service.go`. The current diff does not show new tests explicitly verifying that `clearUserPermissionCache` is called and that the permission cache is indeed invalidated after `SetUserPermission` and `SetPermissions` operations.
*   `pkg/services/accesscontrol/accesscontrol_test.go`: Similar to the above, this test suite needs specific coverage for the cache invalidation in `pkg/services/accesscontrol/resourcepermissions/service.go`.
*   `pkg/services/annotations/accesscontrol/accesscontrol_test.go`: This test suite should cover the updated annotation scopes in `pkg/api/accesscontrol.go` (from `ScopeAnnotationsAll` to `ScopeAnnotationsTypeOrganization`) and the `identity.WithServiceIdentity` usage in `pkg/api/annotations.go`. It should verify that users with basic roles can no longer access dashboard-scoped annotations and that the `AnnotationTypeScopeResolver` functions correctly with the new identity context.
*   `pkg/services/dashboards/accesscontrol_test.go`: This test suite should cover the updated `SetDefaultPermissions` logic in `pkg/services/dashboards/service/dashboard_service.go` which now only applies if `dto.Dashboard.ID == 0`. It should verify the behavior for importing dashboards with pre-existing IDs.
*   `pkg/services/ngalert/provisioning/accesscontrol_test.go`: This test suite is less directly impacted by the specific changes, but general access control tests should still pass.
*   `pkg/tests/api/annotations/annotations_test.go`: This test suite should explicitly cover the changes in `pkg/api/annotations.go`, particularly the `findAnnotationByID` signature change and the use of `identity.WithServiceIdentity` in `AnnotationTypeScopeResolver`.
*   `pkg/api/annotations_test.go`: This test suite should also explicitly cover the changes in `pkg/api/annotations.go`, ensuring the new permission model for annotations is correctly enforced.
*   `pkg/api/dashboard_snapshot_test.go`: This test suite should cover the new logic in `pkg/api/dashboard_snapshot.go` that checks `dashboardUID` in addition to `dashboardID` for permissions when deleting snapshots.
*   `pkg/api/plugin_resource_test.go`: **Adequate coverage.** The PR explicitly adds a new test case `Test oversized request body returns 413` which directly covers the new `maxResourceBodySize` logic in `pkg/api/plugin_resource.go`.
*   `pkg/expr/sql/parser_allow_test.go`: This test suite needs additional coverage for the new SQL parser hardening in `pkg/expr/sql/parser_allow.go`. Specifically, it should include test cases that attempt to use `@@` system variables and verify they are blocked. It should also include tests that place disallowed functions or expressions within `OrderBy`, `With`, `Limit`, and `Window` clauses of `SetOp` and `Select` statements to ensure the explicit `walkNodes` logic correctly identifies and blocks them.
*   `pkg/infra/metrics/service_test.go`: This test suite is not directly affected by the changes.
*   `pkg/infra/usagestats/statscollector/service_test.go`: This test suite is not directly affected by the changes.

## Problem

1.  **Potential Regression in Dashboard Import Permissions:** The `SetDefaultPermissions` logic for imported dashboards now only applies if `dto.Dashboard.ID == 0`. This means if a dashboard is imported with a pre-existing ID (e.g., from a JSON file that includes an ID), its permissions will *not* be reset to defaults. This is a significant behavioral change that could lead to unintended permission configurations for existing or re-imported dashboards, potentially allowing broader access than intended if the source dashboard had lax permissions.
2.  **Incomplete Test Coverage for SQL Parser Hardening:** While `pkg/expr/sql/parser_allow.go` introduces important security hardening by explicitly walking more SQL AST nodes and rejecting `@@` system variables, the existing `pkg/expr/sql/parser_allow_test.go` does not appear to have corresponding new test cases to verify these specific protections. This leaves a gap where newly disallowed patterns might not be caught by tests.
3.  **Untested Access Control Cache Invalidation:** The new cache clearing logic in `pkg/services/accesscontrol/resourcepermissions/service.go` is critical for ensuring that permission changes are immediately effective. However, there are no explicit test cases in `pkg/services/accesscontrol/acimpl/accesscontrol_test.go` or `pkg/services/accesscontrol/accesscontrol_test.go` that verify the cache is correctly invalidated after `SetUserPermission` or `SetPermissions` calls.

## Evidence

*   **Problem 1 (Dashboard Import Permissions):**
    *   `pkg/services/dashboards/service/dashboard_service.go:1073-1076`:
        ```diff
        -	dr.SetDefaultPermissions(ctx, dto, dash, false)
        +	// new dashboard created
        +	if dto.Dashboard.ID == 0 {
        +		dr.SetDefaultPermissions(ctx, dto, dash, false)
        +	}
        ```
*   **Problem 2 (SQL Parser Hardening Test Gap):**
    *   `pkg/expr/sql/parser_allow.go:31-50`: New `walkNodes` logic explicitly traversing `OrderBy`, `With`, `Limit`, `Window` for `SetOp` and `Select`.
    *   `pkg/expr/sql/parser_allow.go:76-85`: New logic to reject `@@` and `@` prefixed `ColName` and `Qualifier`.
    *   `pkg/expr/sql/parser_allow_test.go`: (Contextual evidence) No corresponding new test cases are visible in the diff for this file to cover the specific scenarios mentioned.
*   **Problem 3 (Access Control Cache Invalidation):**
    *   `pkg/services/accesscontrol/resourcepermissions/service.go:229-231`:
        ```go
        	s.clearUserPermissionCache(orgID, user.ID)
        	return result, nil
        ```
    *   `pkg/services/accesscontrol/resourcepermissions/service.go:338-344`:
        ```go
        	clearedUsers := make(map[int64]bool)
        	for _, cmd := range commands {
        		if cmd.UserID != 0 && !clearedUsers[cmd.UserID] {
        			s.clearUserPermissionCache(orgID, cmd.UserID)
        			clearedUsers[cmd.UserID] = true
        		}
        	}
        ```
    *   `pkg/services/accesscontrol/acimpl/accesscontrol_test.go`: (Contextual evidence) No new tests visible in the diff to verify cache invalidation.
    *   `pkg/services/accesscontrol/accesscontrol_test.go`: (Contextual evidence) No new tests visible in the diff to verify cache invalidation.

## Impact

*   **Problem 1:** Importing dashboards with existing IDs might bypass default permission settings, potentially leading to security vulnerabilities or unintended access levels if the imported dashboard's JSON contains less restrictive permissions than the system defaults. This could be a regression in security posture for dashboard management.
*   **Problem 2:** Without specific tests for the new SQL parser hardening, there's a risk that malicious SQL queries leveraging `@@` variables or disallowed functions within previously un-walked AST nodes could still bypass the allowlist, leading to potential SQL injection vulnerabilities or information disclosure.
*   **Problem 3:** If the permission cache is not reliably invalidated, users might experience stale permissions, meaning recently granted or revoked access might not take effect immediately, leading to authorization errors or unintended access for a period. This could cause user frustration and security inconsistencies.

## Recommendation

1.  **Address Dashboard Import Permissions:**
    *   Clarify the intended behavior for `SetDefaultPermissions` when importing dashboards with existing IDs. If the current behavior (only apply for `ID == 0`) is intentional for security reasons, add a comment explaining the rationale.
    *   Add specific test cases to `pkg/services/dashboards/accesscontrol_test.go` that cover importing dashboards with non-zero IDs and verify that default permissions are *not* applied, and that the existing permissions (if any) are preserved or handled as expected.
2.  **Enhance SQL Parser Test Coverage:**
    *   Add new test cases to `pkg/expr/sql/parser_allow_test.go` that specifically target the newly hardened areas in `pkg/expr/sql/parser_allow.go`. This includes:
        *   Queries using `@@` system variables (e.g., `SELECT @@version`).
        *   Queries with disallowed functions or expressions within `OrderBy`, `With`, `Limit`, and `Window` clauses of `SetOp` and `Select` statements.
3.  **Verify Access Control Cache Invalidation:**
    *   Add explicit test cases to `pkg/services/accesscontrol/acimpl/accesscontrol_test.go` and `pkg/services/accesscontrol/accesscontrol_test.go` that perform a `SetUserPermission` or `SetPermissions` operation, then immediately attempt to query permissions for that user/resource, verifying that the updated permissions are reflected and not served from a stale cache.
4.  **Review Alerting Component Compatibility:**
    *   Conduct a targeted review or integration test with the `apps/alerting` components (e.g., `alertenrichment`, `historian`) to ensure they are compatible with the new annotation access control scopes (`ScopeAnnotationsTypeOrganization`). If any components relied on `ScopeAnnotationsAll` for dashboard-level annotations, adjustments may be needed in those components or a specific migration path.

## Traceability
Not specified