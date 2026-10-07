```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file within the `grafana-data` package.

## Problem
1. The `MutableDataFrame` export has been removed, which may affect modules that rely on this export.
2. There is no indication of updated test coverage to reflect this change in exports.

## Evidence
- `packages/grafana-data/src/index.ts:10`: The line where `MutableDataFrame` was previously exported has been modified to exclude it.

## Impact
- Removing the `MutableDataFrame` export could lead to runtime errors in any modules or components that depend on this class. This could break functionality in parts of the application that rely on mutable data frame operations.
- Without updated test coverage, there is a risk that this change could introduce undetected bugs or regressions in the system.

## Recommendation (Fix / Tests / Risks)
1. Review the codebase to identify all instances where `MutableDataFrame` is imported and ensure they are updated or refactored accordingly.
2. Add or update tests to cover scenarios where `MutableDataFrame` is used, ensuring that the removal of this export does not affect the application's functionality.
3. Consider providing alternative solutions or documentation for users who may need to replace `MutableDataFrame` in their implementations.

## Traceability
- Code Owner: Grafana Data Team (assumed based on package name)
```