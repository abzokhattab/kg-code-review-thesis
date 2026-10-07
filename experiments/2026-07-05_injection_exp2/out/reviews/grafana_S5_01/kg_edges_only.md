```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in `index.ts` by removing the export of `getDisplayProcessor`.

## Problem
1. The removal of the `getDisplayProcessor` export could break existing functionality that depends on this function being available externally.
2. There is no evidence of updated test coverage to ensure that the removal of this export does not affect the dependent modules.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The `getDisplayProcessor` export is removed.
- Call-graph indicates multiple dependencies on `getDisplayProcessor`:
  - `packages/grafana-data/src/field/fieldDisplay.ts::createNoValuesFieldDisplay`
  - `packages/grafana-data/src/field/fieldDisplay.ts::getFieldDisplayValues`
  - `packages/grafana-data/src/field/fieldOverrides.ts::<lambda>1`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts::get`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::buildHistogram`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::histogramFieldsToFrame`

## Impact
Removing the export of `getDisplayProcessor` could lead to runtime errors in modules that rely on this function. This could result in broken features or data processing failures, especially in areas related to field display and transformations.

## Recommendation (Fix / Tests / Risks)
1. **Re-evaluate the necessity of removing `getDisplayProcessor`:** Ensure that all dependent modules are updated to handle its absence, or consider retaining the export if it is still needed.
2. **Update test coverage:** Add or update tests to verify that the removal of `getDisplayProcessor` does not negatively impact the functionality of dependent modules.
3. **Conduct integration testing:** Perform thorough integration testing to ensure that the removal does not introduce any regressions or runtime errors.

## Traceability
Not specified
```