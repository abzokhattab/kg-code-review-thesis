```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses incorrect tooltips in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the tooltip position in `PopupMenu` may not account for all UI elements, potentially leading to incorrect tooltip display.
2. The changes in `viewport.cpp` introduce a conditional logic that might not handle all control types consistently, leading to potential tooltip inconsistencies.

## Evidence
- `popup_menu.cpp:3233-3236`: The position adjustment for the tooltip does not consider other UI elements that might affect the tooltip's position.
- `viewport.cpp:1570-1578`: The conditional logic for `PopupMenu` tooltips might bypass other control-specific tooltip logic, leading to inconsistent behavior.

## Impact
- Incorrect tooltip positioning can lead to a poor user experience, as users may see tooltips for the wrong items.
- The conditional logic in `viewport.cpp` could result in tooltips not being displayed correctly for controls other than `PopupMenu`, potentially affecting usability across the application.

## Recommendation (Fix / Tests / Risks)
1. Ensure that the position adjustment in `popup_menu.cpp` accounts for all relevant UI elements that could affect tooltip positioning.
2. Review and test the conditional logic in `viewport.cpp` to ensure consistent tooltip behavior across different control types.
3. Add unit tests to cover scenarios where tooltips are displayed with and without the search bar enabled to ensure consistent behavior.

## Traceability
- Code Owners: GUI Team, specifically those responsible for `PopupMenu` and `Viewport` components.
```