# Review Note — Evidence-Anchored

**Scope:** This PR applies two security patches, one modifying Grafana.com proxy logic to conditionally send SSO tokens, and another refining identity handling for dashboard snapshot API routes.

## Integration Risk
*   `apps/alerting/historian/pkg/apis/alertinghistorian_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/alerting/rules/pkg/apis/alerting_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/alerting/notifications/pkg/apis/alertingnotifications_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/alerting/notifications/pkg/apis/alertingnotifications/v0alpha1/routingtree_spec_gen.go`: No direct integration risk. This file is generated from API specifications and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/alerting/notifications/pkg/apis/alertingnotifications/v0alpha1/zz_openapi_gen.go`: No direct integration risk. This file is generated from OpenAPI specifications and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/alerting/notifications/pkg/apis/alertingnotifications/v0alpha1/receiver_ext.go`: No direct integration risk. This file defines API extensions and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/advisor/pkg/apis/advisor_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/preferences/pkg/apis/manifestdata/preferences_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/playlist/pkg/apis/manifestdata/playlist_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.
*   `apps/plugins/pkg/apis/plugins_manifest.go`: No direct integration risk. This file defines API manifests and does not directly call the modified `ReverseProxyGnetReq` or `GetRoutes` functions.

## Test Coverage Assessment
*   No test files were provided in the structural context, so existing test coverage cannot be assessed directly.
*   **Coverage Gaps for `pkg/api/grafana_com_proxy.go`:**
    *   The new `ssoTokenAllowedPath` function and its integration into `ReverseProxyGnetReq` are not covered. Specific scenarios that need testing include:
        *   Requests to paths matching `ssoTokenAllowedPaths` with `grafanaComAPIToken` present and `GET` method (should send token).
        *   Requests to paths *not* matching `ssoTokenAllowedPaths` (should *not* send token).
        *   Requests with `POST`/`PUT`/`DELETE` methods (should *not* send token, regardless of path).
        *   Requests with `grafanaComAPIToken` empty (should *not* send token).
*   **Coverage Gaps for `pkg/registry/apis/dashboard/snapshot/routes.go`:**
    *   The new type assertion `requester.(*user.SignedInUser)` and subsequent error handling are not covered. Specifically, a test case where `identity.GetRequester` returns an `identity.Requester` that is *not* a `*user.SignedInUser` (e.g., an anonymous user, a service account, or a custom identity type) would be valuable to ensure the error handling `fmt.Errorf("expected SignedInUser identity, got %T", requester)` is correctly triggered and handled, rather than a panic.
    *   Existing snapshot creation/reading flows should be re-verified to ensure they function correctly with the `signedInUser` variable replacing the generic `user` variable.

## Problem
1.  **Untested Proxy Logic:** The new logic for conditionally adding the `Authorization` header in `pkg/api/grafana_com_proxy.go` based on path and HTTP method is critical for security and correct integration with grafana.com, but specific test cases for its behavior are missing.
2.  **Potential Runtime Error in Snapshot Routes:** The explicit type assertion `requester.(*user.SignedInUser)` in `pkg/registry/apis/dashboard/snapshot/routes.go` introduces a potential runtime error if `identity.GetRequester` returns a type other than `*user.SignedInUser`, which is not explicitly covered by tests.

## Evidence
*   `pkg/api/grafana_com_proxy.go:14-28`: Introduction of `ssoTokenAllowedPaths` and `ssoTokenAllowedPath` function.
*   `pkg/api/grafana_com_proxy.go:44`: Conditional logic `if grafanaComAPIToken != "" && req.Method == http.MethodGet && ssoTokenAllowedPath(proxyPath)`.
*   `pkg/registry/apis/dashboard/snapshot/routes.go:33-37`: Type assertion `signedInUser, ok := requester.(*user.SignedInUser)` and error handling.
*   `pkg/registry/apis/dashboard/snapshot/routes.go:42, 45, 50, 51, 159, 162, 167, 168`: Usage of `signedInUser` instead of `user`.
*   Dependent files from KG context: `apps/alerting/historian/pkg/apis/alertinghistorian_manifest.go`, `apps/alerting/rules/pkg/apis/alerting_manifest.go`, `apps/alerting/notifications/pkg/apis/alertingnotifications_manifest.go`, `apps/alerting/notifications/pkg/apis/alertingnotifications/v0alpha1/routingtree_spec_gen.go`, `apps/alerting/notifications/pkg/apis/alertingnotifications/v0alpha1/zz_openapi_gen.go`, `apps/alerting/notifications/pkg/apis/alertingnotifications/v0alpha1/receiver_ext.go`, `apps/advisor/pkg/apis/advisor_manifest.go`, `apps/preferences/pkg/apis/manifestdata/preferences_manifest.go`, `apps/playlist/pkg/apis/manifestdata/playlist_manifest.go`, `apps/plugins/pkg/apis/plugins_manifest.go`.

## Impact
*   **Security Vulnerability/Incorrect Proxy Behavior:** Without adequate testing, the `grafana_com_proxy.go` changes could either leak SSO tokens to unauthorized paths/methods or fail to send them when required, leading to security vulnerabilities or broken functionality for Grafana.com integrations (e.g., plugin/dashboard browsing).
*   **Runtime Panics/Access Control Issues:** The `dashboard/snapshot/routes.go` changes, if not thoroughly tested for various `identity.Requester` types, could lead to runtime panics or incorrect access control decisions for dashboard snapshot operations when non-`SignedInUser` identities are involved. This could manifest as users being unable to create/read snapshots or, in a worst-case scenario, unauthorized access if the `ok` check is bypassed or mishandled.

## Recommendation
1.  **Add Unit Tests for Proxy Logic:** Create or update `pkg/api/grafana_com_proxy_test.go` to include unit tests for `ssoTokenAllowedPath` covering all regex patterns and non-matching paths. Additionally, add integration-style tests within the same file for `ReverseProxyGnetReq` to verify the `Authorization` header is correctly added/omitted based on `grafanaComAPIToken` presence, HTTP method (GET vs. POST), and various `proxyPath` values (allowed vs. disallowed).
2.  **Add Unit Tests for Snapshot Identity Handling:** Create or update `pkg/registry/apis/dashboard/snapshot/routes_test.go` to specifically test the `requester.(*user.SignedInUser)` type assertion. Include a test case where `identity.GetRequester` returns a mock `identity.Requester` that is *not* a `*user.SignedInUser` to ensure the `fmt.Errorf("expected SignedInUser identity, got %T", requester)` error is correctly returned and handled. Also, ensure existing happy path tests for snapshot creation and reading are updated/verified to pass with the new `signedInUser` variable.
3.  **Broader Identity Context Review:** While the listed dependent files are not directly impacted, consider a broader review of how `identity.GetRequester` is used across the system to identify other potential areas where a non-`SignedInUser` identity might be implicitly expected to be a `*user.SignedInUser`, especially in security-sensitive contexts.

## Traceability
Not specified