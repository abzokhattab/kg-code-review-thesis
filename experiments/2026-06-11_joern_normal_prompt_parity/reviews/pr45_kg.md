```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses incorrect tooltips in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the tooltip position in `PopupMenu` may not account for all UI elements, potentially leading to incorrect tooltip display.
2. The changes in `viewport.cpp` introduce a conditional logic that might not handle all control types correctly, potentially causing tooltip retrieval issues.

## Evidence
- `scene/gui/popup_menu.cpp:3233-3236`: The position adjustment for the tooltip does not consider other UI elements that might affect the tooltip position.
- `scene/main/viewport.cpp:1570-1578`: The conditional logic for `PopupMenu` tooltip retrieval might bypass other control-specific tooltip logic.

## Impact
- Incorrect tooltip positioning can lead to a poor user experience, as users may see tooltips for the wrong items.
- The conditional logic in `viewport.cpp` could result in tooltips not being displayed for certain controls, leading to incomplete UI feedback.

## Recommendation (Fix / Tests / Risks)
1. Ensure that the position adjustment in `popup_menu.cpp` accounts for all relevant UI elements that could affect tooltip positioning.
2. Review and test the conditional logic in `viewport.cpp` to ensure it correctly handles all control types and does not bypass necessary tooltip logic.
3. Add unit tests to cover scenarios where the search bar is enabled and ensure tooltips are displayed correctly for all items.

## Traceability
Not specified
```