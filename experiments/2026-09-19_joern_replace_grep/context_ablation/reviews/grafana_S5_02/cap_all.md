```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package by removing the export of `MutableDataFrame`.

## Problem
1. The removal of `MutableDataFrame` from exports may break existing code that relies on this export.
2. Lack of test updates or additions to verify the impact of this change on dependent modules.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The line where `MutableDataFrame` export is removed.
- `packages/grafana-data/src/utils/csv.ts` and other files listed in the call-graph depend on `MutableDataFrame`.

## Impact
- Removing `MutableDataFrame` from exports can lead to runtime errors or broken functionality in any module that imports it from `index.ts`.
- Potentially affects multiple parts of the codebase, including CSV utilities and data transformations, which might rely on `MutableDataFrame`.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search for all instances where `MutableDataFrame` is imported from `index.ts` and update those imports to import directly from `MutableDataFrame.ts`.
2. Add or update tests to ensure that all functionalities relying on `MutableDataFrame` continue to work as expected.
3. Consider deprecating the export first and providing a migration path to minimize disruption.

## Traceability
- Code ownership: Likely the data processing or transformations team, but specific ownership is not specified.
```