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
- If the `onLayoutChange` logic does not handle all edge cases, users might experience unexpected behavior when switching between layouts, such as incorrect sort restoration.
- External manipulation of `localStorage` could lead to inconsistent application state, affecting user experience and potentially causing bugs that are hard to reproduce.

## Recommendation (Fix / Tests / Risks)
1. Review and test additional edge cases for `onLayoutChange`, such as rapid switching between layouts or unexpected `localStorage` states.
2. Consider adding tests that simulate `localStorage` being cleared or modified to ensure the application handles these scenarios gracefully.
3. Evaluate the necessity of relying on `localStorage` for state persistence and explore alternative state management strategies if needed.

## Traceability
Not specified
```