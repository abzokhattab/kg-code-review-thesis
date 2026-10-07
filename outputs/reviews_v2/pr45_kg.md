```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses the issue of incorrect tooltips being displayed in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the search bar's position in `PopupMenu::get_tooltip` may not account for all UI configurations.
2. The changes in `Viewport::_gui_get_tooltip` could introduce inconsistencies in tooltip behavior for other controls.

## Evidence
- `scene/gui/popup_menu.cpp:3233-3236`: The position adjustment for the search bar is hardcoded, which may not be robust across different UI themes or configurations.
- `scene/main/viewport.cpp:1570-1578`: The logic for determining the tooltip source is altered, potentially affecting how tooltips are retrieved for non-`PopupMenu` controls.

## Impact
- The hardcoded position adjustment could lead to incorrect tooltip positioning if the UI theme or configuration changes, potentially causing tooltips to be misaligned.
- The changes in tooltip retrieval logic might cause unexpected behavior for other controls, leading to incorrect or missing tooltips in different parts of the application.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Consider using a more dynamic approach to calculate the position adjustment in `PopupMenu::get_tooltip`, possibly by querying the actual layout or style properties.
2. **Tests:** Add unit tests to cover various UI configurations and themes to ensure tooltips are displayed correctly across different scenarios.
3. **Risks:** Review the impact of changes in `Viewport::_gui_get_tooltip` on other controls and ensure that existing tooltip functionality is not disrupted.

## Traceability
- Code Owners: GUI Team, specifically those responsible for `PopupMenu` and `Viewport` components.
```