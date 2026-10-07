# Review Note — Evidence-Anchored

**Scope:** Adds unit tests for `TextureRect` covering default properties, texture assignment, expand/stretch modes, flip flags, minimum size, and configuration warnings.

## Problem

1.  **Incomplete `get_combined_minimum_size()` coverage for `EXPAND_FIT_*` modes:** The tests for `get_combined_minimum_size()` only cover `EXPAND_KEEP_SIZE` and `EXPAND_IGNORE_SIZE`. The `EXPAND_FIT_WIDTH`, `EXPAND_FIT_HEIGHT`, `EXPAND_FIT_WIDTH_PROPORTIONAL`, and `EXPAND_FIT_HEIGHT_PROPORTIONAL` modes, which calculate minimum size based on the `TextureRect`'s current dimensions, are not tested.
2.  **Missing tests for `texture_filter` and `texture_repeat` properties:** `TextureRect` exposes `texture_filter` and `texture_repeat` properties that control rendering quality and tiling behavior. These properties are not covered by any of the new unit tests.
3.  **Lack of explicit verification for layout and redraw updates:** While property setters are tested, there's no explicit verification that changes to properties like `stretch_mode`, `flip_h`, `flip_v`, or `expand_mode` (beyond the limited `get_combined_minimum_size()` checks) correctly trigger `Control::minimum_size_changed()` and `Control::queue_redraw()`, which are essential for ensuring the UI updates visually and structurally.

## Evidence

*   **Problem 1:**
    *   `tests/scene/test_texture_rect.cpp:179-193`: The `[SceneTree][TextureRect] Minimum size` test only includes subcases for `EXPAND_KEEP_SIZE` and `EXPAND_IGNORE_SIZE`.
    *   `tests/scene/test_texture_rect.cpp:60-78`: The `[SceneTree][TextureRect] Expand mode` test only verifies the setter/getter for all `ExpandMode` values, but does not check their effect on `get_combined_minimum_size()`.
    *   `scene/gui/texture_rect.cpp:get_minimum_size()`: This method's implementation for `EXPAND_FIT_*` modes depends on the `Control::get_size()` and the texture's aspect ratio.
*   **Problem 2:**
    *   `scene/gui/texture_rect.h`: Defines `set_texture_filter(TextureFilter p_filter)`, `get_texture_filter()`, `set_texture_repeat(TextureRepeat p_repeat)`, `get_texture_repeat()`.
    *   `tests/scene/test_texture_rect.cpp`: No `TEST_CASE` or `SUBCASE` references `texture_filter` or `texture_repeat`.
*   **Problem 3:**
    *   `tests/scene/test_texture_rect.cpp:100-120`: The `[SceneTree][TextureRect] Flip flags` test only checks `is_flipped_h()` and `is_flipped_v()` after setting.
    *   `tests/scene/test_texture_rect.cpp:80-98`: The `[SceneTree][TextureRect] Stretch mode` test only checks `get_stretch_mode()` after setting.
    *   `scene/gui/texture_rect.cpp:set_texture(const Ref<Texture2D> &p_texture)`: This method calls `minimum_size_changed()` and `queue_redraw()`.
    *   `scene/gui/texture_rect.cpp:set_expand_mode(ExpandMode p_mode)`: This method calls `minimum_size_changed()` and `queue_redraw()`.
    *   `scene/gui/texture_rect.cpp:set_stretch_mode(StretchMode p_mode)`: This method calls `queue_redraw()`.
    *   `scene/gui/texture_rect.cpp:set_flip_h(bool p_flip_h)`: This method calls `queue_redraw()`.
    *   `scene/gui/texture_rect.cpp:set_flip_v(bool p_flip_v)`: This method calls `queue_redraw()`.

## Impact

1.  **Incorrect UI Layouts:** Without testing `EXPAND_FIT_*` modes, `TextureRect` might report incorrect minimum sizes to parent `Container`s (e.g., `HBoxContainer`, `VBoxContainer`), leading to misaligned or improperly sized UI elements that are difficult to diagnose.
2.  **Undetected Visual Regressions:** Changes to the rendering backend or `TextureRect`'s internal drawing logic related to `texture_filter` or `texture_repeat` could introduce visual artifacts or performance issues without being caught by automated tests.
3.  **Stale UI and Performance Issues:** If `Control::minimum_size_changed()` or `Control::queue_redraw()` are not correctly invoked by property setters, the `TextureRect` might not update its layout or appearance when its properties change, leading to stale visuals or unnecessary redraws if other mechanisms compensate.

## Recommendation (Fix / Tests / Risks)

1.  **Tests:** Extend the `[SceneTree][TextureRect] Minimum size` test in `tests/scene/test_texture_rect.cpp` to include subcases for `EXPAND_FIT_WIDTH`, `EXPAND_FIT_HEIGHT`, `EXPAND_FIT_WIDTH_PROPORTIONAL`, and `EXPAND_FIT_HEIGHT_PROPORTIONAL`. For these tests, explicitly set the `TextureRect`'s `set_size()` to a known value (e.g., `texture_rect->set_size(Size2(100, 0));`) before calling `SceneTree::get_singleton()->process(0)` and checking `get_combined_minimum_size()`.
2.  **Tests:** Add a new `TEST_CASE` in `tests/scene/test_texture_rect.cpp` to cover `set_texture_filter`/`get_texture_filter` and `set_texture_repeat`/`get_texture_repeat` functionality, ensuring all enum values for `TextureFilter` and `TextureRepeat` are tested.
3.  **Tests:** For properties that trigger `Control::minimum_size_changed()` (e.g., `set_texture`, `set_expand_mode`), ensure that `get_combined_minimum_size()` is checked after the property change and `SceneTree::get_singleton()->process(0)` to confirm the layout update. For properties that trigger `Control::queue_redraw()` (e.g., `set_stretch_mode`, `set_flip_h`, `set_flip_v`), consider adding a mock `TextureRect` that overrides `_notification(int p_what)` to assert that `NOTIFICATION_DRAW` is received after the property change and `SceneTree::get_singleton()->process(0)`.

## Traceability
Not specified