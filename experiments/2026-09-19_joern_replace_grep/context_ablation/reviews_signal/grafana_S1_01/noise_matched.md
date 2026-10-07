```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `Registry` class to `RegistryInternal` in the `Registry.ts` file.

## Problem
1. The renaming of the `Registry` class to `RegistryInternal` may break existing imports and usages across multiple files that depend on this class.
2. There is a lack of corresponding updates in test files or dependent files to reflect this change, which could lead to runtime errors or failed tests.

## Evidence
- `packages/grafana-data/src/utils/Registry.ts`: The class `Registry` is renamed to `RegistryInternal` (line 7).
- Dependent files such as `packages/grafana-data/src/transformations/transformers/filterByRefId.ts` and `packages/grafana-data/src/utils/throwIfAngular.ts` may still be using the old class name.
- Test files like `packages/grafana-data/src/query/refId.test.ts` and `packages/grafana-data/src/transformations/transformers/transpose.test.ts` do not show any changes to accommodate the new class name.

## Impact
- The renaming could lead to import errors in files that have not been updated, causing the application to fail at runtime.
- Tests that rely on the `Registry` class might fail if they are not updated to use the new class name, leading to a loss of test coverage and potential undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Update all files that import or use the `Registry` class to use the new `RegistryInternal` name.
2. Ensure all test files that reference the `Registry` class are updated and run successfully with the new class name.
3. Consider adding a deprecation warning or alias for the old class name to maintain backward compatibility temporarily.

## Traceability
Not specified
```