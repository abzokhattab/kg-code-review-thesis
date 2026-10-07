```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the index file of the grafana-data package.

## Problem
1. The removal of `getDisplayProcessor` from the exports may break existing functionality that relies on this function being publicly accessible.
2. There is no accompanying update to the documentation or tests that might indicate the intentional deprecation or replacement of `getDisplayProcessor`.

## Evidence
- `packages/grafana-data/src/index.ts:177`: The line where `getDisplayProcessor` was removed from the exports.
- Call-graph analysis shows multiple dependencies on `getDisplayProcessor`:
  - `packages/grafana-data/src/field/fieldDisplay.ts::createNoValuesFieldDisplay`
  - `packages/grafana-data/src/field/fieldDisplay.ts::getFieldDisplayValues`
  - `packages/grafana-data/src/field/fieldOverrides.ts::<lambda>1`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts::get`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::buildHistogram`
  - `packages/grafana-data/src/transformations/transformers/histogram.ts::histogramFieldsToFrame`

## Impact
- **Technical Impact:** Removing `getDisplayProcessor` from the exports can lead to runtime errors in any module or component that imports it from `index.ts`. This could break features that rely on display processing, leading to potential data visualization issues.
- **Risk:** High risk of integration failure in modules that depend on `getDisplayProcessor` being available for import.

## Recommendation (Fix / Tests / Risks)
1. **Re-export `getDisplayProcessor`:** Unless there is a clear plan to deprecate this function, it should remain exported to avoid breaking changes.
2. **Update Documentation:** If the removal is intentional, update the documentation to reflect this change and provide guidance on alternatives.
3. **Add Tests:** Ensure that there are tests covering the use cases of `getDisplayProcessor` to validate its necessity and functionality.
4. **Communicate Changes:** If the removal is part of a larger refactor or deprecation plan, communicate this to the relevant teams and update any dependent code accordingly.

## Traceability
- Code Owners: Not specified
```