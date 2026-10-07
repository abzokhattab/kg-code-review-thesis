```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses the issue of a cleared sort being incorrectly reset when switching to the folder view in the BrowseDashboards feature.

## Problem
1. The `onLayoutChange` method in `SearchStateManager.ts` may not handle all edge cases for sort state transitions, particularly when switching between layouts.
2. The current test coverage may not fully account for all possible user interactions and state transitions, potentially missing edge cases.

## Evidence
- `public/app/features/search/state/SearchStateManager.ts:233-239`: The logic for handling sort state transitions when changing layouts is modified, but it assumes that the `prevSort` state is always correctly set and restored.
- `public/app/features/search/state/SearchStateManager.test.ts:213-271`: Tests are added to cover some scenarios of layout changes and sort state transitions, but they may not cover all edge cases, such as simultaneous changes in other state variables.

## Impact
- If the sort state is not correctly managed, users may experience unexpected behavior when switching between list and folder views, leading to confusion and potential data misinterpretation.
- Incomplete test coverage could result in undetected bugs, especially in complex user interactions involving multiple state changes.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure that the `onLayoutChange` method robustly handles all possible state transitions, including edge cases where other state variables might change simultaneously.
2. **Tests:** Expand test coverage to include additional scenarios, such as simultaneous changes in layout and other state variables, to ensure comprehensive validation of the sort state logic.
3. **Risks:** Review the integration points with other components that depend on `SearchStateManager` to ensure that changes do not introduce regressions or unexpected behavior.

## Traceability
- Code Owners: Not specified
```