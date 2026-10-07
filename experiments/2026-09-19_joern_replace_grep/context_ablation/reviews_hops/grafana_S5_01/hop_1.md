```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the package exports in `index.ts` by removing the export of `getDisplayProcessor`.

## Problem
1. The removal of `getDisplayProcessor` from exports might break other modules that rely on it.
2. Insufficient test coverage to ensure that removing `getDisplayProcessor` does not affect dependent modules.

## Evidence
- `packages/grafana-data/src/index.ts:180`: `getDisplayProcessor` is removed from exports.
- Call-graph indicates multiple dependencies on `getDisplayProcessor`:
  - `packages/grafana-data/src/field/fieldDisplay.ts::createNoValuesFieldDisplay`
  - `packages/grafana-data/src/field/fieldDisplay.ts::getFieldDisplayValues`
  - `packages/grafana-data/src/field/fieldOverrides.ts::<lambda>1`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts::get`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::buildHistogram`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::histogramFieldsToFrame`

## Impact
- Removing `getDisplayProcessor` from exports could lead to runtime errors in modules that depend on it, potentially causing failures in data processing or display functionalities.
- The change might introduce bugs that are not covered by existing tests, leading to undetected issues in production.

## Recommendation (Fix / Tests / Risks)
1. Review all dependent modules and ensure they do not require `getDisplayProcessor` as an export.
2. Add or update tests to cover scenarios where `getDisplayProcessor` is used to ensure its removal does not introduce regressions.
3. Consider deprecating `getDisplayProcessor` with a warning before removing it entirely to allow dependent modules to adjust.

## Traceability
- Code owners for `packages/grafana-data/src/field/fieldDisplay.ts`, `packages/grafana-data/src/field/fieldOverrides.ts`, `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts`, and `packages/grafana-data/src/transformations/transformers/histogram.ts` should be consulted.
```