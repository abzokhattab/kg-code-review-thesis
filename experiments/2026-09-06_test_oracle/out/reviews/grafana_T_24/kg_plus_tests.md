```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors an internal naming cleanup by renaming a function in the string utility module.

## Problem
1. The function `escapeStringForRegexInternal` is still being used externally, which contradicts the intended internal use suggested by the name change.
2. The related test file `string.test.ts` does not seem to cover the updated function name, potentially leading to a gap in test coverage.

## Evidence
- `packages/grafana-data/src/text/string.ts:8`: The function `escapeStringForRegexInternal` is renamed but still used externally.
- `packages/grafana-data/src/transformations/matchers/refIdMatcher.ts`: This file imports and uses `escapeStringForRegex`, indicating external usage.
- `packages/grafana-data/src/text/string.test.ts`: No updates to reflect the function name change, suggesting tests may not cover the renamed function.

## Impact
- The renaming to `escapeStringForRegexInternal` suggests the function is for internal use only, but it is still used externally, which could lead to confusion and misuse.
- Lack of updated test coverage for the renamed function could result in undetected bugs or regressions.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the function's intended scope (internal vs. external) and adjust the naming or usage accordingly.
2. Update the test suite in `string.test.ts` to ensure it covers the renamed function and verify that all relevant test cases pass.
3. Consider adding comments or documentation to clarify the function's intended use and any constraints on its usage.

## Traceability
- Code Owner: Not specified
```