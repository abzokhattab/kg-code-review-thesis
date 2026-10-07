```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes a bug in the Browse Dashboards page where clearing the Sort picker and switching to folder view would incorrectly restore the previously cleared sort.

## Problem
1. The `onLayoutChange` function logic may not handle all edge cases for state transitions between layouts.
2. Potential lack of test coverage for scenarios where `prevSort` is not set initially.

## Evidence
- `public/app/features/search/state/SearchStateManager.ts:231-243`: The logic for handling `onLayoutChange` has been modified to unconditionally stash the current sort when switching to Folders, but it may not account for all edge cases.
- `public/app/features/search/state/SearchStateManager.test.ts:213-271`: Tests added for `onLayoutChange` cover several scenarios, but there is no explicit test for when `prevSort` is initially `undefined`.

## Impact
- If `prevSort` is not correctly managed, users might experience unexpected behavior when switching between List and Folder views, potentially leading to confusion or incorrect data presentation.
- The absence of tests for certain edge cases could lead to regressions in future changes.

## Recommendation (Fix / Tests / Risks)
1. Review and ensure that `onLayoutChange` handles all possible state transitions, especially when `prevSort` is initially `undefined`.
2. Add a test case to cover the scenario where `prevSort` is not set initially to ensure robust handling of all state transitions.
3. Consider adding comments in the code to clarify the logic for future maintainers.

## Traceability
Not specified
```