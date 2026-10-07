# Review Note — Evidence-Anchored

**Scope:** This PR fixes redirect logic for the `home_page` setting when Grafana is served under a subpath, specifically for relative paths that do not include the subpath prefix.

## Problem
1.  **Integration Risk: Changed Input Type for `stripBaseFromUrl` with Internal Paths:** The modification to `locationUtil.processRedirectUri` changes the input format passed to `stripBaseFromUrl` for relative URIs that *do* contain the `appSubUrl` prefix (e.g., `/grafana/d/my-dashboard`). Previously, `stripBaseFromUrl` would receive an absolute URL string (e.g., `http://localhost:3000/grafana/d/my-dashboard`), but now it will receive a relative path string (e.g., `/grafana/d/my-dashboard`). While `stripBaseFromUrl` is expected to handle both, this change in input type for a common scenario could lead to subtle regressions in how internal links are processed by core navigation components.
2.  **Test Gap: Relative Paths *with* Subpath Prefix:** The new tests added in this PR correctly cover relative paths *without* the `appSubUrl` prefix (e.g., `/admin/users`). However, there are no specific test cases to verify the behavior of `locationUtil.processRedirectUri` when `redirectUri` is a relative path *that includes* the `appSubUrl` prefix (e.g., `/grafana/d/my-dashboard`) and `appSubUrl` is configured. This leaves a gap in ensuring that internal Grafana links continue to be processed correctly under subpath configurations.

## Evidence
*   **packages/grafana-data/src/utils/location.ts:171**: The line `return stripBaseFromUrl(isAbsoluteUri ? redirectUrl.href : redirectUrl.pathname + redirectUrl.search);` directly implements the change in input to `stripBaseFromUrl`.
*   **packages/grafana-data/src/utils/location.test.ts**: The new tests (`handles relative path without subpath prefix`, `merges current params into relative path without subpath prefix`, `redirect URI params take precedence over current params when no subpath prefix`) only cover scenarios like `/admin/users`, not `/grafana/d/my-dashboard`.
*   **public/app/core/navigation/patch/interceptLinkClicks.ts**: This file calls `locationUtil.processRedirectUri` to handle internal link clicks, making it a critical integration point for this change.
*   **public/app/core/navigation/GrafanaRoute.tsx**: This core routing component also relies on `locationUtil.processRedirectUri` for determining navigation targets.

## Impact
Incorrect routing for internal Grafana links when `appSubUrl` is configured, leading to broken navigation, 404 errors, or unexpected redirects within the application. This could affect users accessing dashboards, plugins, or other core features via relative paths that are expected to be handled by Grafana's router.

## Recommendation (Fix / Tests / Risks)
1.  **Add Test for Relative Path with Subpath:** Add a new test case to `packages/grafana-data/src/utils/location.test.ts` within the `processRedirectUri` describe block. This test should specifically cover a `redirectUri` that is a relative path *including* the `appSubUrl` (e.g., `/grafana/d/my-dashboard`) when `appSubUrl` is configured. Assert that the output is the expected path relative to the subpath (e.g., `/d/my-dashboard`).
2.  **Verify `stripBaseFromUrl` Robustness:** If possible, review the implementation of `stripBaseFromUrl` to explicitly confirm its robustness in handling both absolute URL strings (e.g., `http://localhost:3000/grafana/d/my-dashboard`) and relative path strings (e.g., `/grafana/d/my-dashboard`) as inputs, especially concerning the `appSubUrl` stripping logic. This will mitigate the risk identified in Problem 1.

## Traceability
Not specified