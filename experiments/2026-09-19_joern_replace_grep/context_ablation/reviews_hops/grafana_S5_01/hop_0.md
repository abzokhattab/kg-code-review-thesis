```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The removal of `getDisplayProcessor` from the exports may lead to unintended consequences if it is used elsewhere in the codebase.
2. Lack of information on whether there are any tests covering the removal of this export to ensure it does not affect other parts of the application.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The line where `getDisplayProcessor` was removed from the exports.

## Impact
- Removing `getDisplayProcessor` from exports could break functionality in other parts of the application that rely on this function, potentially leading to runtime errors or unexpected behavior.
- Without proper testing, there is a risk that this change could cause integration issues that are not immediately apparent.

## Recommendation (Fix / Tests / Risks)
1. Conduct a search across the codebase to identify any instances where `getDisplayProcessor` is being imported from `grafana-data`. Ensure that these instances are refactored appropriately or confirm that they are no longer needed.
2. Add or update tests to cover the removal of `getDisplayProcessor` to ensure that this change does not introduce regressions.
3. Document the change in the package's CHANGELOG or relevant documentation to inform other developers of this modification.

## Traceability
Not specified
```