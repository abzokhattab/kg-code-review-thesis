# Review Note — Evidence-Anchored

**Scope:** This PR fixes a bug in the Browse Dashboards page where a cleared sort would be resurrected when switching to folder view, by adjusting how sort state is managed in `SearchStateManager.ts`.

## Problem
1.  **Integration Risk - State Consumption:** The change in `public/app/features/search/state/SearchStateManager.ts::onLayoutChange` now ensures that `prevSort` is set to `undefined` when switching to `SearchLayout.Folders` if the current `sort` was already `undefined` (cleared). While this fixes the bug, components like `public/app/features/browse-dashboards/components/BrowseView.tsx` or `public/app/features/browse-dashboards/components/SearchView.tsx` that might consume `SearchStateManager.state.prevSort` (though less likely directly) should be robust to `prevSort` being `undefined` in this scenario, which is a subtle change in the state manager's behavior for `prevSort`.
2.  **Test Gap - End-to-End Coverage:** The added unit tests in `public/app/features/search/state/SearchStateManager.test.ts` thoroughly cover the state transitions within `SearchStateManager`. However, there is no end-to-end test that verifies the complete user flow, including interaction with UI components like `public/app/features/browse-dashboards/components/BrowseActions/BrowseActions.tsx` (for layout switching) and the sort picker, to ensure the fix holds in a real browser scenario.

## Evidence
*   **Diff:** `public/app/features/search/state/SearchStateManager.ts` lines 234-237 show the modified logic for `onLayoutChange`, specifically `this.setStateAndDoSearch({ layout, prevSort: this.state.sort, sort: undefined });` when switching to `Folders` and `this.setStateAndDoSearch({ layout, sort: this.state.sort ?? this.state.prevSort });` when switching to `List`.
*   **Structural Context (Callers):** The `onLayoutChange` method is expected to be called by UI components responsible for layout switching, such as those found in `public/app/features/browse-dashboards/components/BrowseActions/BrowseActions.tsx` or `public/app/features/browse-dashboards/BrowseDashboardsPage.tsx`.
*   **Structural Context (Tests):** The new tests in `public/app/features/search/state/SearchStateManager.test.ts` under the `describe('onLayoutChange', ...)` block, specifically `it('does not resurrect a cleared sort when switching to Folders')`, directly address the bug fix at the unit level.

## Impact
*   **Problem 1 (Integration Risk):** While unlikely to cause a regression given the nature of `prevSort` as an internal state for `SearchStateManager`, any component that might have implicitly relied on `prevSort` always holding a valid sort string (even when `sort` was `undefined` in `Folders` view) could exhibit unexpected behavior.
*   **Problem 2 (Test Gap):** Without an E2E test, there's a risk that the UI components might not correctly trigger `SearchStateManager.onLayoutChange` or `onSortChange` in the exact sequence that reproduces the bug, or that other UI-level interactions could interfere with the state manager's logic, leading to a regression of the original bug or similar issues in the future.

## Recommendation (Fix / Tests / Risks)
1.  **Review UI Component Interaction:** Verify that `public/app/features/browse-dashboards/components/BrowseActions/BrowseActions.tsx` and any other components that interact with `SearchStateManager.state.sort` or `SearchStateManager.state.prevSort` are robust to `prevSort` being `undefined` when the layout is `SearchLayout.Folders` and the sort was explicitly cleared.
2.  **Add End-to-End Test:** Implement an E2E test scenario that simulates the full user flow to confirm the fix. This test should:
    *   Navigate to `public/app/features/browse-dashboards/BrowseDashboardsPage.tsx`.
    *   Apply a sort (e.g., via the sort picker).
    *   Clear the applied sort.
    *   Switch the layout to "Folders" using the UI (likely in `public/app/features/browse-dashboards/components/BrowseActions/BrowseActions.tsx`).
    *   Assert that no sort is active and the view remains in "Folders".
    *   Switch the layout back to "List".
    *   Assert that no sort is resurrected.

## Traceability
Not specified