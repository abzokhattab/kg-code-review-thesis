```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package by removing `MutableDataFrame` from the exports.

## Problem
1. The removal of `MutableDataFrame` from exports may break existing functionality that depends on this class being publicly accessible.
2. Lack of test coverage for the impact of removing `MutableDataFrame` on other modules that might rely on it.

## Evidence
- `packages/grafana-data/src/index.ts:12`: `MutableDataFrame` is no longer exported.
- `packages/grafana-data/src/utils/csv.ts::<lambda>2`: This file calls `MutableDataFrame.addFieldFor`, indicating a dependency.
- `packages/grafana-data/src/dataframe/MutableDataFrame.ts::<init>`: Constructor references `MutableDataFrame.addField`, showing internal dependencies.

## Impact
- Removing `MutableDataFrame` from the exports could lead to runtime errors in any module or external code that relies on it being available for import.
- Potentially breaks backward compatibility, affecting users who depend on this export for their implementations.

## Recommendation (Fix / Tests / Risks)
1. **Fix**: Re-evaluate the need to remove `MutableDataFrame` from exports. If necessary, consider deprecating it first before complete removal.
2. **Tests**: Add tests to ensure that other modules or external projects that rely on `MutableDataFrame` are not adversely affected by this change.
3. **Risks**: Communicate with stakeholders or teams using this package to assess the impact and plan a phased deprecation if removal is essential.

## Traceability
- Code Owner: Data Team (assumed from package name)
```