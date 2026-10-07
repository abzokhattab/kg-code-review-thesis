```
# Review Note — Evidence-Anchored

**Scope:** This PR addresses incorrect tooltips in `PopupMenu` when the search bar is enabled.

## Problem
1. The adjustment for the search bar in `PopupMenu::get_tooltip` may not account for all UI configurations.
2. The refactoring in `Viewport::_gui_get_tooltip` introduces a potential logic flaw by altering the tooltip retrieval sequence.

## Evidence
- `scene/gui/popup_menu.cpp:3233-3236`: The position adjustment for the search bar is hardcoded, which may not be robust across different UI themes or configurations.
- `scene/main/viewport.cpp:1570-1578`: The logic change in tooltip retrieval could lead to incorrect tooltip display if `PopupMenu` is not the intended control.

## Impact
- The hardcoded position adjustment could result in tooltips being displayed incorrectly if the UI theme or layout changes, leading to a poor user experience.
- The altered logic in `Viewport::_gui_get_tooltip` might cause tooltips to be fetched from the wrong control, especially in complex UI hierarchies, potentially confusing users.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Consider using a more dynamic approach to calculate the position adjustment in `PopupMenu::get_tooltip`, possibly by querying the actual layout or theme properties.
2. **Fix:** Review the logic in `Viewport::_gui_get_tooltip` to ensure that tooltips are retrieved from the correct control, especially when `PopupMenu` is involved.
3. **Tests:** Add unit tests to cover different UI configurations and ensure that tooltips are displayed correctly in all scenarios.

## Traceability
- Code owners: GUI Team, specifically those responsible for `PopupMenu` and `Viewport` components.
```