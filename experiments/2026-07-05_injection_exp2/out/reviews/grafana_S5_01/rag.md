```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. Inconsistent export removal: The removal of `getDisplayProcessor` from exports may cause issues if it is used elsewhere in the codebase or expected by consumers of the package.
2. Lack of documentation or comments: The change lacks documentation or comments explaining why `getDisplayProcessor` was removed, which can lead to confusion for future maintainers.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The line removing `getDisplayProcessor` from exports.
- Similar patterns in `packages/grafana-data/src/internal/index.ts` show consistent export practices, but no removal of exports without clear documentation.

## Impact
- Removing `getDisplayProcessor` from exports without proper documentation or understanding of its usage can lead to runtime errors or broken functionality if other parts of the application rely on it.
- It may also cause integration issues if external projects or plugins depend on this export.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search to identify all usages of `getDisplayProcessor` within the codebase and any external dependencies.
2. Add comments or documentation explaining the rationale behind the removal of `getDisplayProcessor` to ensure clarity for future maintainers.
3. Consider adding tests to ensure that the removal does not break existing functionality or integrations.

## Traceability
Not specified
```