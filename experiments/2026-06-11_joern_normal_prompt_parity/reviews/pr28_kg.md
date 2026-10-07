```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes a bug in the Browse Dashboards page where clearing the Sort picker and switching to folder view would incorrectly restore the previously cleared sort.

## Problem
1. The `onLayoutChange` function logic may not handle all edge cases for state transitions between layouts, potentially leading to unexpected behavior.
2. The reliance on `localStorage` for state persistence might introduce inconsistencies if the storage is manipulated or cleared externally.

## Evidence
- `public/app/features/search/state/SearchStateManager.ts:231-243`: The logic for handling layout changes has been modified to unconditionally stash the current sort when switching to Folders, but it may not account for all possible state transitions.
- `public/app/features/search/state/SearchStateManager.test.ts:213-271`: Tests have been added to cover the new behavior, but they may not cover scenarios where `localStorage` is externally modified.

## Impact
- If the `onLayoutChange` logic does not handle all edge cases, users might experience unexpected behavior when switching between layouts, potentially leading to confusion or incorrect data presentation.
- External manipulation of `localStorage` could lead to state inconsistencies, affecting user experience and potentially causing bugs that are hard to reproduce.

## Recommendation (Fix / Tests / Risks)
1. Review and expand the test cases to cover additional edge cases, such as unexpected `localStorage` states or rapid layout changes.
2. Consider implementing a more robust state management solution that does not rely solely on `localStorage`, or ensure that `localStorage` interactions are fail-safe.
3. Conduct a thorough integration test to ensure that changes do not negatively impact other components that depend on `SearchStateManager`.

## Traceability
- Code Owners: Not specified
```