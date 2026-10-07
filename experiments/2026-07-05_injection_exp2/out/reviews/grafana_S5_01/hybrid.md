```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the index file of the `grafana-data` package.

## Problem
1. The removal of `getDisplayProcessor` from exports may affect modules that depend on it.
2. Lack of documentation or comments explaining the rationale behind removing `getDisplayProcessor`.

## Evidence
- `packages/grafana-data/src/index.ts:177`: `getDisplayProcessor` export removed.
- Call-graph shows multiple dependencies on `getDisplayProcessor`:
  - `packages/grafana-data/src/field/fieldDisplay.ts::createNoValuesFieldDisplay`
  - `packages/grafana-data/src/field/fieldDisplay.ts::getFieldDisplayValues`
  - `packages/grafana-data/src/field/fieldOverrides.ts::<lambda>1`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts::get`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::buildHistogram`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::histogramFieldsToFrame`

## Impact
- Removing `getDisplayProcessor` from exports could break functionality in modules that rely on it, leading to runtime errors or unexpected behavior.
- Without documentation, future maintainers may not understand the reasoning behind this change, potentially leading to confusion or incorrect assumptions.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `getDisplayProcessor` from exports. If it is still needed, consider keeping it exported.
2. If the removal is intentional and necessary, ensure all dependent modules are updated accordingly and tested to prevent breakage.
3. Add comments or documentation to explain the rationale behind this change to aid future maintenance.

## Traceability
Not specified
```