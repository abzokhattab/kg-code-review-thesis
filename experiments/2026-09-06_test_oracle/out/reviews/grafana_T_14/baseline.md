```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of a function within the ArrayDataFrame module.

## Problem
1. The renaming of the function might affect external modules or dependencies if they rely on the original function name.
2. Lack of test updates or additions to verify that the refactored function name does not break existing functionality.

## Evidence
- `packages/grafana-data/src/dataframe/ArrayDataFrame.ts:30`: The function `arrayToDataFrame` is renamed to `arrayToDataFrameInternal`.

## Impact
- The technical impact includes potential breakage of any external code that imports and uses the `arrayToDataFrame` function directly. If this function is part of a public API, consumers of the API might face runtime errors due to the missing function.
- Without corresponding test updates, there is a risk that any issues introduced by this change might go unnoticed, leading to potential bugs in production.

## Recommendation (Fix / Tests / Risks)
1. Verify if `arrayToDataFrame` is part of the public API. If so, consider maintaining the original name or providing a deprecated alias to avoid breaking changes.
2. Update or add unit tests to ensure that the refactored function name does not affect existing functionality.
3. Conduct a thorough search for any internal or external references to `arrayToDataFrame` to assess the impact of this change.

## Traceability
Not specified
```