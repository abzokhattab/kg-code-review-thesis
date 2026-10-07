```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming by renaming a function in the `fieldState` module.

## Problem
1. The renamed function `getFieldDisplayNameInternal` is not updated in other parts of the codebase where it might be used.
2. Lack of test coverage to ensure that the renaming does not affect the functionality or integration with other modules.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:110`: The function `getFieldDisplayName` is renamed to `getFieldDisplayNameInternal`.

## Impact
- If the function is used elsewhere in the codebase, failing to update its references could lead to runtime errors or broken functionality.
- Without adequate tests, there is a risk that the change could introduce regressions or unexpected behavior in the application.

## Recommendation (Fix / Tests / Risks)
1. Perform a comprehensive search across the codebase to update all references to the renamed function `getFieldDisplayNameInternal`.
2. Add or update unit tests to cover the renamed function, ensuring its behavior remains consistent and correct.
3. Consider adding integration tests if the function is used in critical paths or interacts with other modules.

## Traceability
Not specified
```