```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses incorrect tooltips in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the search bar's position in `PopupMenu::get_tooltip` may not account for all UI configurations.
2. The logic in `Viewport::_gui_get_tooltip` could lead to incorrect tooltip retrieval due to the conditional handling of `PopupMenu`.

## Evidence
- `scene/gui/popup_menu.cpp:3233-3236`: The position adjustment for the search bar is hardcoded, which might not be robust across different UI layouts.
- `scene/main/viewport.cpp:1570-1578`: The conditional logic for `PopupMenu` tooltip retrieval could lead to incorrect behavior if `p_control` is not a `PopupMenu`.

## Impact
- The hardcoded position adjustment may not work correctly if the UI layout changes, leading to incorrect tooltip display.
- The conditional logic in `Viewport::_gui_get_tooltip` might cause tooltips to be fetched incorrectly, especially if the control hierarchy changes or if `PopupMenu` is not the expected type.

## Recommendation (Fix / Tests / Risks)
1. Refactor the position adjustment logic in `PopupMenu::get_tooltip` to dynamically calculate offsets based on the current UI layout.
2. Simplify and ensure the logic in `Viewport::_gui_get_tooltip` correctly identifies and handles `PopupMenu` instances.
3. Add unit tests to cover various UI configurations and ensure tooltips are displayed correctly in all scenarios.

## Traceability
Not specified
```