# Review Note — Evidence-Anchored

**Scope:** This pull request applies several security patches and bug fixes, including hardening access control for annotations and dashboard snapshots, limiting request body sizes for plugin resources and live push, enhancing SQL expression parsing security, improving RBAC cache invalidation, correcting proxy address parsing, adjusting dashboard import permissions, and validating data source query intervals.

## Problem

1.  **Potential for RBAC bypass in SQL expressions:** The original SQL parser walk logic might have missed certain Abstract Syntax Tree (AST) nodes (like `OrderBy`, `With`, `Limit` in `SetOp` or `Window` in `Select`), allowing malicious SQL functions or system variables to bypass the allowlist. This could lead to information disclosure or unauthorized operations.
2.  **Stale RBAC permissions due to missing cache invalidation:** Changes to user or team resource permissions were not consistently invalidating the RBAC permission cache, potentially leading to users operating with outdated access rights until the cache naturally expired or the service restarted.
3.  **Denial of Service (DoS) vulnerability via large request bodies:** Several API endpoints (plugin resources, live push) lacked explicit limits on request body size, making them vulnerable to DoS attacks where an attacker could send excessively large payloads, consuming server memory and network bandwidth.

## Evidence

*   `pkg/expr/sql/parser_allow.go`: Extensive changes to `AllowQuery` and `allowedNode` functions, including the introduction of `walkNodes` to explicitly traverse previously skipped AST fields and new checks for `@@system` variables and `LOCK` clauses.
*   `pkg/services/accesscontrol/resourcepermissions/service.go:229`, `pkg/services/accesscontrol/resourcepermissions/service.go:339`: Addition of `s.clearUserPermissionCache` calls after `SetUserPermission` and `SetPermissions` methods, along with the `clearUserPermissionCache` helper function.
*   `pkg/api/plugin_resource.go:19`, `pkg/api/plugin_resource.go:100`, `pkg/api/plugin_resource.go:116`: Introduction of `maxResourceBodySize`, `http.MaxBytesReader`, and specific error handling for `http.MaxBytesError`.
*   `pkg/services/live/pushhttp/push.go:62`: Addition of `ctx.Req.Body = http.MaxBytesReader(ctx.Resp, ctx.Req.Body, 500*1024)` to limit push message body size.

## Impact

1.  **Security Vulnerability (SQL Injection/Information Disclosure):** Without the enhanced SQL parsing, an attacker could craft queries that exploit overlooked AST nodes or system variables to extract sensitive information, execute unauthorized database commands, or bypass intended data access restrictions.
2.  **Incorrect Authorization Decisions:** Stale RBAC caches could result in users retaining permissions they no longer possess or being denied access to resources they should have, leading to security policy violations or user frustration and operational issues.
3.  **System Instability and Resource Exhaustion:** Unrestricted request body sizes could allow an attacker to flood the server with large amounts of data, leading to memory exhaustion, increased CPU usage, and potential service outages for legitimate users.

## Recommendation (Fix / Tests / Risks)

1.  **Review SQL Parser Allowlist Thoroughness:**
    *   **Fix:** Ensure the `allowedNode` function and the new `walkNodes` logic cover all possible SQL AST nodes that could be used to bypass security, especially for new or complex SQL features. Consider a fuzzing approach or extensive negative testing against the SQL parser.
    *   **Tests:** Add more comprehensive integration tests for the SQL parser, specifically targeting edge cases with `SetOp`, `Select` (with `Window`, `Lock`), and `ColName` (with `@@` prefixes) to confirm the allowlist is robust.
    *   **Risks:** Overly restrictive rules could break legitimate queries; overly permissive rules could reintroduce vulnerabilities.
2.  **Verify RBAC Cache Invalidation Logic:**
    *   **Fix:** Confirm that `clearUserPermissionCache` is called in all relevant code paths where a user's permissions might change (e.g., user role updates, team membership changes, direct permission assignments).
    *   **Tests:** Add unit and integration tests specifically for RBAC permission changes to verify that the cache is correctly invalidated and new permissions are immediately reflected.
    *   **Risks:** Incomplete cache invalidation could lead to continued authorization issues.
3.  **Standardize Request Body Size Limits:**
    *   **Fix:** Evaluate if `maxResourceBodySize` (128 MiB) for plugin resources and 500 KiB for live push messages are appropriate and consistent across the application. Consider if other endpoints also need similar protections.
    *   **Tests:** Ensure the existing tests for oversized bodies cover both the plugin resource and live push endpoints.
    *   **Risks:** Setting limits too low could break legitimate integrations; setting them too high could still leave a DoS vector.
4.  **Assess Annotation Permission Migration Impact:**
    *   **Fix:** The migration `AnnotationsAllScopeReplacementMigrationID` correctly handles existing `annotations:*` permissions. However, ensure that any custom roles or integrations that relied on the broader `annotations:*` scope for dashboard-level annotations are updated or documented, as they will now be restricted to `annotations:type:organization` by default.
    *   **Tests:** Verify the migration logic on a database with diverse existing permission configurations to ensure no unintended data loss or unique constraint violations occur.
    *   **Risks:** Users might lose access to dashboard-specific annotations if they previously relied on the `annotations:*` scope without explicit dashboard permissions.
5.  **Review Dashboard Import Permission Change:**
    *   **Fix:** The change in `ImportDashboard` (`pkg/services/dashboards/service/dashboard_service.go:1076`) to only set default permissions for *new* dashboards (`dto.Dashboard.ID == 0`) is a behavioral change. Confirm this is the desired behavior, as it means importing an updated dashboard will *not* reset its permissions to defaults. If the intent is to always enforce default permissions on import, this condition should be removed.
    *   **Tests:** Add tests for importing existing dashboards to verify that their permissions are preserved as expected.
    *   **Risks:** If not intended, this could lead to dashboards retaining overly permissive or restrictive permissions after an update, potentially bypassing security policies.

## Traceability
Not specified