```
# Review Note — Evidence-Anchored

**Scope:** This PR fixes a bug in the Browse Dashboards page where clearing the Sort picker and switching to folder view would incorrectly restore the previously cleared sort.

## Problem
1. The `onLayoutChange` function logic may not handle all edge cases for state transitions between layouts.
2. Potential lack of comprehensive test coverage for all possible state transitions in `SearchStateManager`.

## Evidence
- `public/app/features/search/state/SearchStateManager.ts:231-243`: The logic for handling layout changes has been modified, but it may not account for all edge cases.
- `public/app/features/search/state/SearchStateManager.test.ts:213-271`: Tests added for `onLayoutChange`, but they may not cover all possible state transitions and edge cases.

## Impact
- If the logic in `onLayoutChange` does not handle all edge cases, users might experience unexpected behavior when switching between list and folder views, potentially leading to incorrect UI states.
- Insufficient test coverage could lead to regressions in future changes, as not all scenarios might be tested.

## Recommendation (Fix / Tests / Risks)
1. Review and ensure that `onLayoutChange` handles all possible state transitions, including edge cases where `sort` and `prevSort` might be undefined or null.
2. Expand test cases in `SearchStateManager.test.ts` to cover additional scenarios, such as switching layouts with various initial states of `sort` and `prevSort`.
3. Consider adding integration tests that simulate user interactions across the Browse Dashboards page to ensure consistent behavior.

## Traceability
Not specified
```