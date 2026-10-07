```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package by removing the export of `getDisplayProcessor`.

## Problem
1. The removal of `getDisplayProcessor` from exports may break functionality in dependent files.
2. Insufficient test coverage to ensure that the removal does not affect existing functionality.

## Evidence
- `packages/grafana-data/src/index.ts:180`: `getDisplayProcessor` export removed.
- `packages/grafana-data/src/field/displayProcessor.test.ts`: This test file depends on `getDisplayProcessor`.
- `packages/grafana-data/src/field/fieldDisplay.test.ts`: This test file depends on `getDisplayProcessor`.
- `packages/grafana-data/src/field/fieldOverrides.test.ts`: This test file depends on `getDisplayProcessor`.
- `packages/grafana-data/src/transformations/transformers/histogram.ts`: This file calls `getDisplayProcessor`.

## Impact
- Removing `getDisplayProcessor` from exports can lead to runtime errors in any module that imports it, potentially breaking functionality across multiple parts of the application.
- Tests that rely on `getDisplayProcessor` may fail, indicating a lack of backward compatibility.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `getDisplayProcessor` from exports. If it is still required, ensure all dependent modules are updated accordingly.
2. Add or update tests to cover the scenarios where `getDisplayProcessor` is used to ensure that its removal does not introduce bugs.
3. Consider deprecating `getDisplayProcessor` with a warning before removal to give dependent modules time to adjust.

## Traceability
- Code Owner: Not specified
```