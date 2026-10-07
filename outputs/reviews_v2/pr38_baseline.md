```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes the redirect functionality for custom `home_page` settings when the application is served under a subpath.

## Problem
1. The logic for handling relative paths without a subpath prefix may not correctly handle all edge cases.
2. Lack of comprehensive test coverage for scenarios involving complex query parameters and subpath configurations.

## Evidence
- `packages/grafana-data/src/utils/location.ts:172-176`: The logic for determining whether to use `href` or `pathname + search` may not account for all possible URL configurations.
- `packages/grafana-data/src/utils/location.test.ts:340-367`: Tests added cover some scenarios but may not be exhaustive, particularly for complex query parameter combinations.

## Impact
- Incorrect handling of URLs could lead to broken redirects, especially in environments with complex subpath configurations.
- Users might experience unexpected navigation behavior, potentially impacting user experience and application reliability.

## Recommendation (Fix / Tests / Risks)
1. Review and expand the logic in `location.ts` to ensure all edge cases are covered, particularly for URLs with complex query parameters.
2. Add additional test cases in `location.test.ts` to cover scenarios with nested query parameters and different subpath configurations.
3. Consider edge cases where the `redirectUri` might be malformed or unexpected, and ensure graceful handling.

## Traceability
Not specified
```