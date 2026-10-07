```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses the issue of incorrect tooltips being displayed in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the search bar's position in `PopupMenu::get_tooltip` may not account for all UI elements affecting the tooltip position.
2. The logic for determining the tooltip in `Viewport::_gui_get_tooltip` is inconsistent and may lead to incorrect tooltip display for other controls.

## Evidence
- `scene/gui/popup_menu.cpp:3233-3236`: The position adjustment for the search bar is added, but it may not consider other UI elements that could affect the tooltip position.
- `scene/main/viewport.cpp:1570-1578`: The logic for determining the tooltip is altered, potentially affecting how tooltips are displayed for controls other than `PopupMenu`.

## Impact
- The tooltip may still be incorrect if other UI elements affect the position, leading to a poor user experience.
- The changes in `Viewport::_gui_get_tooltip` could inadvertently affect tooltip behavior for other controls, introducing new bugs.

## Recommendation (Fix / Tests / Risks)
1. Ensure that the position adjustment in `PopupMenu::get_tooltip` accounts for all relevant UI elements, not just the search bar.
2. Review and test the changes in `Viewport::_gui_get_tooltip` to ensure they do not negatively impact other controls.
3. Add unit tests to verify that tooltips are displayed correctly for various configurations of `PopupMenu`.

## Traceability
Not specified
```