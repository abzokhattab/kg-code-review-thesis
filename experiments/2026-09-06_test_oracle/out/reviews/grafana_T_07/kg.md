```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `MutableDataFrame` class to `MutableDataFrameInternal`.

## Problem
1. The renaming of `MutableDataFrame` to `MutableDataFrameInternal` may break existing dependencies if not all references are updated.
2. The refactor lacks accompanying updates to documentation or comments that explain the rationale for the change.
3. There is no evidence of updated test coverage to ensure the renamed class does not introduce regressions.

## Evidence
- `packages/grafana-data/src/dataframe/MutableDataFrame.ts:26`: The class name is changed, but no corresponding updates are visible in dependent files.
- Dependent files such as `packages/grafana-data/src/dataframe/CircularDataFrame.ts` and `packages/grafana-data/src/transformations/transformers/merge.ts` may still reference the old class name.
- No new or updated tests are visible in the diff to confirm the change is covered.

## Impact
- The change could lead to runtime errors or broken functionality in parts of the codebase that still reference the old class name.
- Lack of documentation updates may cause confusion for future developers who encounter the renamed class.
- Without updated tests, there is a risk of undetected regressions affecting data transformation features.

## Recommendation (Fix / Tests / Risks)
1. Ensure all references to `MutableDataFrame` in dependent files are updated to `MutableDataFrameInternal`.
2. Update documentation and comments to reflect the reason for the renaming and any implications for developers.
3. Add or update tests to verify that the renamed class functions correctly and does not introduce regressions.

## Traceability
- Code owners for `packages/grafana-data/src/dataframe/` and `packages/grafana-data/src/transformations/transformers/` should be consulted to ensure all dependencies are addressed.
```