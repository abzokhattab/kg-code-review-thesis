```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses incorrect tooltips in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the tooltip position in `PopupMenu::get_tooltip` may not account for all UI elements that could affect the position.
2. The changes in `Viewport::_gui_get_tooltip` could lead to incorrect tooltip retrieval for controls other than `PopupMenu`.

## Evidence
- `scene/gui/popup_menu.cpp:3234-3237`: The position adjustment only considers the `scroll_container`'s global position, which might not be sufficient if other UI elements affect the tooltip position.
- `scene/main/viewport.cpp:1571-1578`: The logic for determining the tooltip is altered such that it prioritizes `PopupMenu` tooltips, potentially ignoring other control-specific tooltips.

## Impact
- The tooltip position might still be incorrect if other UI elements influence the position, leading to a poor user experience.
- The change in tooltip retrieval logic could result in incorrect tooltips being shown for controls other than `PopupMenu`, especially if they have their own tooltip logic.

## Recommendation (Fix / Tests / Risks)
1. Ensure that all relevant UI elements are considered when adjusting the tooltip position in `PopupMenu::get_tooltip`.
2. Review and test the logic in `Viewport::_gui_get_tooltip` to ensure that it correctly handles tooltips for all control types, not just `PopupMenu`.
3. Add unit tests to verify that tooltips are correctly displayed for both `PopupMenu` and other controls when the search bar is enabled.

## Traceability
Not specified
```