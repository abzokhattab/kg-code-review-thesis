# Review Note — Evidence-Anchored

**Scope:** This PR refactors various `MIN/MAX/CLAMP` macro usages across the codebase to leverage component-wise `Vector*` math functions, aiming to improve readability and safety.

## Problem
1.  **Untested Core Math Logic:** Fundamental geometry operations like `AABB::abs()`, `Rect2::abs()`, `Rect2i::abs()`, `Rect2::intersection()`, and `Rect2::merge()` are critical components used throughout the engine. While the refactor improves readability, the absence of dedicated unit tests for these specific methods means potential regressions in edge cases (e.g., negative sizes, zero-sized rectangles, overlapping/non-overlapping intersections) might go unnoticed.
2.  **Implicit Assumptions in `clamp` Usage:** The `clamp` operations, while syntactically correct, rely on the `Vector*::clamp` implementation being perfectly equivalent to the original `CLAMP` macro for all `real_t` and `int` types. While generally true, subtle floating-point precision differences or handling of edge values (NaN, infinity) could theoretically lead to different behavior in highly sensitive calculations, especially in physics or rendering.

## Evidence
*   **Untested Core Math Logic:**
    *   `core/math/aabb.h:101` (AABB::abs)
    *   `core/math/rect2.h:152` (Rect2::intersection)
    *   `core/math/rect2.h:172` (Rect2::merge)
    *   `core/math/rect2.h:282` (Rect2::abs)
    *   `core/math/rect2i.h:95` (Rect2i::intersection)
    *   `core/math/rect2i.h:115` (Rect2i::merge)
    *   `core/math/rect2i.h:217` (Rect2i::abs)
    *   No explicit unit test files for `AABB`, `Rect2`, `Rect2i` are listed in the provided knowledge graph.
*   **Implicit Assumptions in `clamp` Usage:**
    *   `core/math/delaunay_3d.h:281` (Delaunay3D::Delaunay3D, `grid_pos.clamp`)
    *   `core/math/delaunay_3d.h:339` (Delaunay3D::find_simplex_at_pos, `from.clamp`, `to.clamp`)
    *   `servers/physics_3d/godot_shape_3d.cpp:2016` (GodotHeightMapShape3D::_get_cell, `clamped_point = p_point.clamp(...)`)
    *   `servers/rendering/renderer_rd/environment/fog.cpp:509` (Fog::_point_get_position_in_froxel_volume, `fog_position.clamp(...)`)
    *   `drivers/vulkan/rendering_device_driver_vulkan.cpp:760` (RenderingDeviceDriverVulkan::_check_device_capabilities, `vrs_capabilities.texel_size = Vector2i(16, 16).clamp(...)`)

## Impact
*   **Untested Core Math Logic:** Regressions in `AABB`, `Rect2`, or `Rect2i` calculations could lead to subtle visual glitches, incorrect collision detection, UI layout issues, or even crashes in various parts of the engine that rely on these fundamental types. For example, `AABB::abs()` is indirectly used in `convex_hull.cpp::compute` via `AABB` construction, and `Rect2::intersects` (which often relies on `Rect2::intersection()`) is called in `AnimationNodeStateMachineEditor::_state_machine_gui_input`.
*   **Implicit Assumptions in `clamp` Usage:** While unlikely, a subtle difference in `clamp` behavior could lead to incorrect grid indexing in `Delaunay3D::Delaunay3D` or `Delaunay3D::find_simplex_at_pos`, affecting 3D triangulation. Similarly, `GodotHeightMapShape3D::collide` or `GodotHeightMapShape3D::cast_motion` could experience incorrect clamping of points, leading to physics inaccuracies. `Fog::volumetric_fog_update` could have incorrect fog volume calculations.

## Recommendation (Fix / Tests / Risks)
1.  **Add Unit Tests for Core Math Types:** Introduce dedicated unit tests for `AABB`, `Rect2`, and `Rect2i` in `core/tests/` (e.g., `test_aabb.cpp`, `test_rect2.cpp`, `test_rect2i.cpp`). These tests should specifically cover:
    *   `AABB::abs()`: Test with positive, negative, and zero `size` components.
    *   `Rect2::abs()` and `Rect2i::abs()`: Test with positive, negative, and zero `size` components.
    *   `Rect2::intersection()` and `Rect2i::intersection()`: Test with overlapping, non-overlapping, partially overlapping, and zero-sized rectangles.
    *   `Rect2::merge()` and `Rect2i::merge()`: Test with various relative positions and sizes.
2.  **Verify `clamp` Behavior in Existing Tests:** Ensure that existing tests for `Delaunay3D` (in `test_delaunay_3d.cpp`), `DynamicBVH` (in `test_dynamic_bvh.cpp`), and `GodotHeightMapShape3D` (in `test_height_map_shape_3d.cpp`) adequately cover the boundary conditions and ranges where `clamp` is used. If not, expand these tests to specifically target the min/max bounds.
3.  **Review Floating Point Precision:** For `real_t` based `Vector*::clamp` operations, confirm that the underlying `Vector*` math implementation uses standard library `fmin/fmax/fclamp` or equivalent for `real_t` to ensure consistent floating-point behavior.

## Traceability
Not specified