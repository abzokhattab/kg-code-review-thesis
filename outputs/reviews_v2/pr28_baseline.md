```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes a bug in the Browse Dashboards page where clearing the Sort picker and switching to folder view would incorrectly restore the previously cleared sort.

## Problem
1. The `onLayoutChange` method logic could potentially lead to unexpected behavior if not all edge cases are covered.
2. The reliance on localStorage for state management might introduce issues if the storage is not properly synchronized or cleared.

## Evidence
- `public/app/features/search/state/SearchStateManager.ts:231-239`: The logic change in `onLayoutChange` now unconditionally stashes the current sort when switching to Folders, which could lead to issues if not all scenarios are considered.
- `public/app/features/search/state/SearchStateManager.test.ts:213-271`: The tests added cover several scenarios, but there might be edge cases not considered, such as concurrent modifications to localStorage.

## Impact
- If the logic in `onLayoutChange` does not handle all edge cases, users might experience unexpected behavior when switching between layouts, potentially leading to confusion or incorrect data presentation.
- The use of localStorage for state management could lead to inconsistencies if multiple tabs or windows are open, as changes in one might not be reflected in another.

## Recommendation (Fix / Tests / Risks)
1. Ensure comprehensive test coverage for all possible transitions between layouts and sort states, including edge cases like concurrent localStorage access.
2. Consider implementing a mechanism to synchronize localStorage across multiple tabs or windows to prevent state inconsistencies.
3. Review the logic in `onLayoutChange` to ensure it handles all potential edge cases, especially when dealing with undefined or null values.

## Traceability
Not specified
```