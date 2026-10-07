```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in `index.ts` by removing `getDisplayProcessor` from the exports.

## Problem
1. **Potential Breakage in Dependent Files:** The removal of `getDisplayProcessor` from the exports may break functionality in files that depend on it.
2. **Insufficient Test Coverage:** The change might not be adequately covered by tests, risking undetected issues in dependent functionalities.

## Evidence
- `packages/grafana-data/src/index.ts:180`: `getDisplayProcessor` is removed from the exports.
- `packages/grafana-data/src/field/fieldDisplay.ts: createNoValuesFieldDisplay` and `getFieldDisplayValues` depend on `getDisplayProcessor`.
- `packages/grafana-data/src/transformations/transformers/histogram.ts: buildHistogram` and `histogramFieldsToFrame` call `getDisplayProcessor`.
- Test files such as `packages/grafana-data/src/field/displayProcessor.test.ts` and `packages/grafana-data/src/field/fieldDisplay.test.ts` reference `getDisplayProcessor`.

## Impact
- **Technical Impact:** Removing `getDisplayProcessor` from exports can lead to runtime errors in any module that imports it, potentially causing application failures.
- **Risk of Undetected Errors:** If tests do not cover all scenarios where `getDisplayProcessor` is used, issues may go unnoticed until runtime.

## Recommendation (Fix / Tests / Risks)
1. **Re-evaluate Export Removal:** Consider if `getDisplayProcessor` is still needed by external modules and if its removal is justified.
2. **Ensure Comprehensive Test Coverage:** Verify that all functionalities relying on `getDisplayProcessor` are covered by tests, and add tests if necessary.
3. **Communicate with Code Owners:** Engage with the owners of the dependent files to assess the impact of this change and plan any necessary adjustments.

## Traceability
- Code Owners: Not specified
```