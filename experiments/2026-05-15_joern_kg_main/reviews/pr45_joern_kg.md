# Review Note — Evidence-Anchored

**Scope:** This PR aims to fix incorrect tooltip display in `PopupMenu` instances when the search bar is enabled, by adjusting coordinate calculations.

## Problem
1.  **Incorrect Coordinate Adjustment in `PopupMenu::get_tooltip`:** The core fix in `PopupMenu::get_tooltip` uses `pos.y += scroll_container->get_global_position().y;` to adjust the mouse position. Given that `p_pos` is typically local to the `PopupMenu` control, adding the `scroll_container`'s global Y position will result in an incorrect coordinate, likely causing `_get_mouse_over` to fail or return the wrong item. The adjustment should account for the local offset of the search bar and scroll container within the `PopupMenu`.
2.  **Removal of `PopupMenu` Specific Position Adjustment in `Viewport`:** The `Viewport::_gui_get_tooltip` method previously included a "Temporary solution for PopupMenus" that adjusted `pos.y` by `sb->get_margin(SIDE_TOP)` before calling `PopupMenu::get_tooltip`. This adjustment has been removed from `viewport.cpp`. While the intent might be to consolidate all adjustments within `PopupMenu::get_tooltip`, this change means `PopupMenu::get_tooltip` now receives a different `p_pos` than it did previously, making the correctness of the new adjustment in `PopupMenu` even more critical and prone to error if not perfectly compensating for the removed `Viewport` logic.
3.  **Lack of Dedicated Test Coverage:** There are no explicit test files provided in the context that specifically cover `PopupMenu` tooltip behavior, especially when the `allow_search` property is enabled. This leaves the fix vulnerable to regressions and doesn't guarantee the original bug is fully resolved across various `PopupMenu` configurations.

## Evidence
*   `scene/gui/popup_menu.cpp:3234`: `pos.y += scroll_container->get_global_position().y;` (Suspicious coordinate adjustment logic).
*   `scene/main/viewport.cpp:1567-1577`: The `PopupMenu` specific `pos.y` adjustment using `sb->get_margin(SIDE_TOP)` has been removed from `Viewport::_gui_get_tooltip`.
*   `scene/main/viewport.cpp:1571`: `PopupMenu *menu = Object::cast_to<PopupMenu>(this);` (Incorrectly attempts to cast the `Viewport` itself to a `PopupMenu`, though the `else` branch still calls `p_control->get_tooltip(pos)` which will reach `PopupMenu::get_tooltip`).
*   Callers of `PopupMenu` methods, such as `color_picker.cpp::set_picker_shape`, `file_dialog.cpp::_popup_menu`, and `line_edit.cpp::set_text_direction`, rely on `PopupMenu` functionality, including potentially tooltips, but their existing tests (if any) likely don't cover this specific tooltip scenario.

## Impact
*   **Incorrect Tooltips / Regression:** The incorrect coordinate adjustment in `PopupMenu::get_tooltip` will likely cause tooltips to still be displayed for the wrong item, or not at all, effectively failing to fix the original bug or introducing new tooltip display issues.
*   **Subtle Behavioral Change:** The removal of the `SIDE_TOP` margin adjustment from `Viewport` means `PopupMenu::get_tooltip` now operates on a different `p_pos` baseline, which could lead to unexpected behavior if the new adjustment doesn't perfectly compensate.
*   **Untested Critical Path:** Without dedicated tests for `PopupMenu` tooltips with search bars, this specific bug fix and potential regressions in tooltip behavior for widely used UI components (like those in `ColorPicker`, `FileDialog`, `LineEdit`) could go unnoticed.

## Recommendation (Fix / Tests / Risks)
1.  **Correct `PopupMenu::get_tooltip` Coordinate Adjustment:** Re-evaluate `scene/gui/popup_menu.cpp:3234`. The `p_pos` is local to `PopupMenu`. To get the coordinate relative to the scrollable item list, you should likely subtract the local Y position of the `scroll_container` (which accounts for the search bar and top margin). Consider `pos.y -= scroll_container->get_position().y;` or a similar calculation that correctly translates `p_pos` into the `scroll_container`'s local coordinate space.
2.  **Re-evaluate `Viewport` Changes:** While the intent to consolidate logic is good, ensure that the `PopupMenu::get_tooltip` method is now robust enough to handle *all* necessary coordinate adjustments without the `Viewport`'s previous `SIDE_TOP` margin adjustment. The line `PopupMenu *menu = Object::cast_to<PopupMenu>(this);` in `scene/main/viewport.cpp:1571` should be reverted to `PopupMenu *menu = Object::cast_to<PopupMenu>(p_control);` to correctly identify the hovered control as a `PopupMenu` if the `if (menu)` block is intended to be used.
3.  **Add Dedicated Test Cases:** Create a new test case (e.g., in `test/scene/gui/test_popup_menu.gd` or a new C++ test file) that specifically:
    *   Instantiates a `PopupMenu` with `set_allow_search(true)`.
    *   Adds multiple items with distinct tooltips.
    *   Simulates mouse hover events (using `PopupMenu::get_tooltip`) over different items, both when the search bar is visible and when it's scrolled out of view (if applicable), asserting that the correct tooltip is returned.
    *   Verifies that `PopupMenu` instances used by callers like `color_picker.cpp::ColorPicker` and `file_dialog.cpp::FileDialog` still display correct tooltips.

## Traceability
Not specified