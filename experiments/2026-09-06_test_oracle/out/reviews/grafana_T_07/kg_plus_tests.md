```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `MutableDataFrame` class to `MutableDataFrameInternal`.

## Problem
1. The renaming of `MutableDataFrame` to `MutableDataFrameInternal` may break existing dependencies that rely on the original class name.
2. The deprecation notice in the class documentation may not be sufficient if the class is still being used in other parts of the codebase.
3. Insufficient test coverage for the impact of renaming on dependent modules and external integrations.

## Evidence
- **packages/grafana-data/src/dataframe/MutableDataFrame.ts:23**: The class name is changed from `MutableDataFrame` to `MutableDataFrameInternal`.
- **packages/grafana-data/src/dataframe/CircularDataFrame.ts**: This file imports `MutableDataFrame`, which may break due to the renaming.
- **packages/grafana-data/src/transformations/transformers/merge.ts**: This file also imports `MutableDataFrame`, indicating potential breakage.
- **packages/grafana-data/src/transformations/transformers/seriesToRows.ts**: Another dependency on `MutableDataFrame`.
- **packages/grafana-data/src/utils/csv.ts**: Uses `MutableDataFrame`, which could be affected by the renaming.

## Impact
- The renaming could lead to runtime errors in any module that imports `MutableDataFrame` without updating the import statement to the new class name.
- Potential disruption in functionality for users relying on this class in their custom transformations or data processing scripts.
- Risk of incomplete deprecation if the class is still actively used in the codebase.

## Recommendation (Fix / Tests / Risks)
1. Update all import statements in dependent files to reflect the new class name `MutableDataFrameInternal`.
2. Ensure that all related test files, such as `MutableDataFrame.test.ts`, are updated to test the renamed class and verify no functionality is broken.
3. Consider adding a transitional alias or backward compatibility layer to prevent immediate breakage for external users.
4. Communicate the change clearly in release notes and provide guidance for users on how to update their code.

## Traceability
- Code Owners: Not specified
```