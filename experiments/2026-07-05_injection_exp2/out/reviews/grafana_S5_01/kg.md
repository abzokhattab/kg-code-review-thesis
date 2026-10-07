```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the exports in the `index.ts` file of the `grafana-data` package, specifically removing the export of `getDisplayProcessor`.

## Problem
1. The removal of `getDisplayProcessor` from the exports may break existing functionality that relies on this function being publicly accessible.
2. There is no indication of updated test coverage to ensure that the removal does not affect existing features.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The export of `getDisplayProcessor` has been removed.
- Call-graph analysis shows `getDisplayProcessor` is used in multiple files:
  - `packages/grafana-data/src/field/fieldDisplay.ts`
  - `packages/grafana-data/src/field/fieldOverrides.ts`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts`

## Impact
- Removing `getDisplayProcessor` from the exports can lead to runtime errors in modules that depend on it, potentially causing application features to fail.
- Without updated tests, there is a risk that the impact of this change is not fully understood, leading to undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Assess the necessity of removing `getDisplayProcessor` from exports. If it's required, ensure all dependent modules are updated accordingly.
2. Add or update test cases to cover scenarios where `getDisplayProcessor` is used to confirm that its removal does not introduce errors.
3. Consider deprecating the export first, providing a transition period for dependent modules to adjust.

## Traceability
- Code owners for `grafana-data` package: Not specified
```