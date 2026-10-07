# Review Note — Evidence-Anchored

**Scope:** This PR applies two security patches: one to restrict the `grafana.com` API token to specific GET paths, and another to enforce `SignedInUser` identity for dashboard snapshot creation and settings retrieval.

## Problem
1.  **Potential for API Token Leakage:** The `grafanaComAPIToken` could potentially be sent to unintended `grafana.com` endpoints or via non-GET requests, which might expose sensitive authentication information.
2.  **Insufficient Identity Enforcement for Snapshot Operations:** Dashboard snapshot creation and settings retrieval handlers did not explicitly enforce that the `Requester` must be a `SignedInUser`, potentially allowing other identity types (e.g., anonymous, service accounts) to bypass intended access controls or cause unexpected behavior.

## Evidence
*   `pkg/api/grafana_com_proxy.go:41`: `if grafanaComAPIToken != "" && req.Method == http.MethodGet && ssoTokenAllowedPath(proxyPath) {`
*   `pkg/api/grafana_com_proxy.go:10-27`: Introduction of `ssoTokenAllowedPaths` and `ssoTokenAllowedPath` function.
*   `pkg/registry/apis/dashboard/snapshot/routes.go:33`: `import ("github.com/grafana/grafana/pkg/services/user")`
*   `pkg/registry/apis/dashboard/snapshot/routes.go:167-171`: `requester, err := identity.GetRequester(ctx)` followed by `signedInUser, ok := requester.(*user.SignedInUser)` and error handling.
*   `pkg/registry/apis/dashboard/snapshot/routes.go:175, 178, 181, 190, 191, 227, 228`: All subsequent uses of `user` replaced with `signedInUser`.
*   `pkg/registry/apis/dashboard/snapshot/routes.go:452-456`: Similar changes in the `/api/snapshots/settings` handler.

## Impact
1.  **Security Vulnerability (API Token):** Without these restrictions, the `grafanaComAPIToken` could be inadvertently sent to `grafana.com` endpoints that are not designed to handle it, or via HTTP methods that are not intended for token-based authentication, increasing the risk of token interception or misuse.
2.  **Security Vulnerability (Snapshots):** Allowing non-`SignedInUser` identities to proceed with snapshot operations could lead to unauthorized creation or modification of snapshots, or exposure of snapshot settings, potentially bypassing RBAC checks that assume a `SignedInUser` context. This could result in data integrity issues or information disclosure.

## Recommendation (Fix / Tests / Risks)
1.  **Fix:** The proposed changes directly address the identified security concerns by restricting token usage and enforcing identity types. The regexes for `ssoTokenAllowedPaths` appear reasonable for common plugin/dashboard API interactions.
2.  **Tests:**
    *   **`grafana_com_proxy.go`:** Add unit tests for `ssoTokenAllowedPath` to cover all defined regex patterns, including edge cases (e.g., paths with/without leading slashes, valid/invalid plugin/dashboard UIDs). Add integration tests for `ReverseProxyGnetReq` to verify that the `Authorization` header is correctly added for allowed GET requests and *not* added for disallowed GET requests or any non-GET requests.
    *   **`routes.go`:** Add unit/integration tests for the snapshot handlers (`/api/snapshots/create`, `/api/snapshots/settings`) to explicitly test scenarios where the `Requester` is *not* a `*user.SignedInUser` (e.g., an anonymous user or a different identity type, if applicable in the system), ensuring they correctly return the "expected SignedInUser identity" error.
3.  **Risks:**
    *   **`grafana_com_proxy.go`:** There's a minor risk that the `ssoTokenAllowedPaths` regexes might be too restrictive for future legitimate `grafana.com` API calls that require the `grafanaComAPIToken`. This would manifest as broken functionality and would require updating the regex list. Given this is a security patch, the bias towards restrictiveness is appropriate.
    *   **`routes.go`:** The explicit type assertion `requester.(*user.SignedInUser)` is robust. The risk is minimal, primarily ensuring that any existing legitimate flows using non-`SignedInUser` identities for these specific snapshot operations are correctly identified and either updated or confirmed as intended to be blocked.

## Traceability
Not specified