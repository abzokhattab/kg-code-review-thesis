```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The removal of `getDisplayProcessor` from the exports may lead to integration issues in modules that depend on it.
2. There is no evidence of updated tests to ensure that removing `getDisplayProcessor` from exports does not break existing functionality.

## Evidence
- `packages/grafana-data/src/index.ts:180`: `getDisplayProcessor` has been removed from the exports.
- Call-graph indicates multiple dependencies on `getDisplayProcessor`:
  - `packages/grafana-data/src/field/fieldDisplay.ts::createNoValuesFieldDisplay`
  - `packages/grafana-data/src/field/fieldDisplay.ts::getFieldDisplayValues`
  - `packages/grafana-data/src/field/fieldOverrides.ts::<lambda>1`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts::get`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::buildHistogram`

## Impact
- Removing `getDisplayProcessor` from exports can lead to runtime errors in any module that imports it, potentially causing failures in data display logic across the application.
- Lack of test updates increases the risk of undetected issues, as existing tests may not cover the scenarios affected by this change.

## Recommendation (Fix / Tests / Risks)
1. Review all modules that currently import `getDisplayProcessor` to ensure they are not broken by this change.
2. Add or update tests to verify that removing `getDisplayProcessor` from exports does not lead to any regressions or runtime errors.
3. Consider deprecating `getDisplayProcessor` with a warning before removing it entirely to allow dependent modules time to adapt.

## Traceability
- Code owners or teams: Not specified
```