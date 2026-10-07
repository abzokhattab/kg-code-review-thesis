```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors package exports in the index file of the grafana-data package.

## Problem
1. Potential loss of functionality due to the removal of `getDisplayProcessor` from exports.
2. Lack of clarity on whether the removal is intentional or accidental, as no explanation is provided.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The export of `getDisplayProcessor` is removed without any accompanying documentation or comments explaining the rationale.

## Impact
- The removal of `getDisplayProcessor` from exports could break existing functionality or integrations that rely on this function. This could lead to runtime errors or missing features in dependent modules or applications.

## Recommendation (Fix / Tests / Risks)
1. Verify whether the removal of `getDisplayProcessor` is intentional. If so, ensure that all dependent code is updated accordingly and that this change is documented.
2. If the removal is accidental, restore the export to maintain existing functionality.
3. Add tests or update existing ones to cover the usage of `getDisplayProcessor` to ensure that any future changes do not inadvertently break functionality.

## Traceability
Not specified
```