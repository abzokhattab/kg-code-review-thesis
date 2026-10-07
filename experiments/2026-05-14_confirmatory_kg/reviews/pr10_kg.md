# Review Note — Evidence-Anchored

**Scope:** This PR introduces a new project setting `rendering/environment/fog/use_legacy_blending` to revert volumetric fog blending behavior to pre-4.6 versions, primarily for visual compatibility with existing projects.

## Integration Risk

*   **`doc/classes/ProjectSettings.xml`**: This documentation update depends on the `GLOBAL_DEF_RST` key in `servers/rendering/rendering_server.cpp` matching the path `rendering/environment/fog/use_legacy_blending`. A mismatch would lead to incorrect documentation or a non-functional setting.
*   **`servers/rendering/rendering_server.cpp`**: This file defines the global project setting. Its correctness is paramount as it's the entry point for the setting's value. An incorrect key or default value would break the entire feature chain.
*   **`servers/rendering/renderer_rd/renderer_scene_render_rd.h` and `servers/rendering/renderer_rd/renderer_scene_render_rd.cpp`**: These files manage the `fog_use_legacy_blending` state. `renderer_scene_render_rd.cpp` depends on `rendering_server.cpp` for initialization. The getter `fog_use_legacy_blending_get()` exposed by `renderer_scene_render_rd.h` is crucial for `sky.cpp` and `render_forward_clustered.cpp`. Any error in initialization or the getter would propagate incorrect state throughout the rendering pipeline.
*   **`servers/rendering/renderer_rd/environment/sky.h` and `servers/rendering/renderer_rd/environment/sky.cpp`**: These files integrate the legacy blending flag into the `SkyRD` rendering path. `sky.h` modifies the `SkySceneState::UBO` struct, which is highly sensitive to `std140` packing rules and must precisely align with `servers/rendering/renderer_rd/shaders/environment/sky.glsl`. Misalignment could lead to runtime crashes or incorrect rendering. `sky.cpp` depends on `renderer_scene_render_rd.h` to retrieve the setting.
*   **`servers/rendering/renderer_rd/forward_clustered/scene_shader_forward_clustered.h` and `servers/rendering/renderer_rd/forward_clustered/render_forward_clustered.cpp`**: These files integrate the legacy blending flag into the `Forward+` rendering path. `scene_shader_forward_clustered.h` modifies the `Specialization` bitfield, which is sensitive to bit packing and must align with `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered_inc.glsl`. Incorrect bit allocation could lead to incorrect shader behavior. `render_forward_clustered.cpp` depends on `renderer_scene_render_rd.h` to retrieve the setting.
*   **`servers/rendering/renderer_rd/shaders/environment/sky.glsl`**: This shader implements the legacy blending logic for the sky. It critically depends on the `SkySceneData` UBO definition matching `sky.h` and `sky.cpp`. Incorrect logic here would result in visual regressions for sky fog when the legacy setting is enabled.
*   **`servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl` and `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered_inc.glsl`**: These shaders implement the legacy blending logic for the forward clustered renderer. `scene_forward_clustered_inc.glsl` defines `sc_fog_use_legacy_blending()`, which depends on the bitfield packing in `scene_shader_forward_clustered.h`. `scene_forward_clustered.glsl` uses this function. Any mismatch in bitfield indexing or incorrect blending logic would lead to visual regressions for scene fog.

## Test Coverage Assessment

No test files are listed in the provided structural context. This indicates a complete lack of dedicated test coverage for the new `use_legacy_blending` project setting.

Specific scenarios not tested include:
*   Visual correctness of legacy blending with various fog colors (e.g., light, dark, neutral) and opacities.
*   Visual correctness of legacy blending when both standard fog and volumetric fog are active.
*   Visual correctness of legacy blending when only volumetric fog is active.
*   Visual correctness of legacy blending when only standard fog is active.
*   The interaction of `volumetric_fog_sky_affect` with the legacy blending in `sky.glsl`.
*   Ensuring the project setting is correctly loaded and applied on scene load and when the setting is changed at runtime.
*   Performance impact, if any, of the conditional blending logic in the shaders.

## Problem

1.  **Lack of Dedicated Test Coverage:** There are no specific tests to verify the correct functionality and visual output of the new `use_legacy_blending` setting across different fog configurations and rendering paths. This makes it difficult to ensure the feature works as intended and prevents regressions.
2.  **Potential for UBO/Specialization Packing Mismatches:** The changes involve modifying UBOs (`SkySceneState::UBO`) and shader specializations (`Specialization` bitfield) in C++ headers and corresponding GLSL shader definitions. Any subtle mismatch in byte alignment or bit indexing between C++ and GLSL could lead to hard-to-debug runtime errors, visual glitches, or crashes.
3.  **Consistency of Blending Logic:** The legacy blending logic is implemented in two distinct shader files (`sky.glsl` and `scene_forward_clustered.glsl`). While the current implementation appears consistent, future changes or refactors could inadvertently introduce discrepancies between these two paths if not thoroughly tested.

## Evidence

*   **Problem 1 (Lack of Test Coverage):**
    *   Knowledge Graph Context: No test files are listed in the "Repository Structural Context".
*   **Problem 2 (UBO/Specialization Mismatches):**
    *   `servers/rendering/renderer_rd/environment/sky.h:158` (C++ UBO definition)
    *   `servers/rendering/renderer_rd/shaders/environment/sky.glsl:78` (GLSL UBO definition)
    *   `servers/rendering/renderer_rd/forward_clustered/scene_shader_forward_clustered.h:126` (C++ Specialization bitfield)
    *   `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered_inc.glsl:138` (GLSL bitfield access)
*   **Problem 3 (Consistency of Blending Logic):**
    *   `servers/rendering/renderer_rd/shaders/environment/sky.glsl:286` (Sky fog blending logic)
    *   `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl:1505` (Scene fog blending logic)

## Impact

*   **Visual Regressions:** Without dedicated tests, projects relying on the new legacy blending behavior might experience unexpected visual artifacts, incorrect fog appearance, or even crashes if UBO/specialization mismatches occur. This directly contradicts the PR's goal of providing visual compatibility.
*   **Debugging Difficulty:** Errors related to UBO packing or bitfield indexing are notoriously difficult to diagnose, often manifesting as subtle visual glitches or memory corruption far from the source of the error.
*   **Inconsistent Rendering:** If the blending logic differs between the sky and scene rendering paths, it could lead to an inconsistent visual experience, especially in scenes with both types of fog.

## Recommendation

1.  **Add Dedicated Visual Tests:** Implement new visual tests within the engine's testing framework (e.g., using `tests/render/test_render_scenes.cpp` or similar) to cover the `use_legacy_blending` setting. These tests should:
    *   Render scenes with various fog colors (light, dark) and opacities, both with and without volumetric fog, for both `use_legacy_blending = true` and `false`.
    *   Capture screenshots and compare them against reference images to ensure visual correctness.
    *   Specifically test the interaction of `volumetric_fog_sky_affect` in `servers/rendering/renderer_rd/shaders/environment/sky.glsl`.
2.  **Verify UBO/Specialization Packing:** Double-check the `std140` packing rules for `SkySceneState::UBO` in `servers/rendering/renderer_rd/environment/sky.h` and `servers/rendering/renderer_rd/shaders/environment/sky.glsl`. Similarly, confirm the bitfield indexing for `Specialization` in `servers/rendering/renderer_rd/forward_clustered/scene_shader_forward_clustered.h` and `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered_inc.glsl`. Consider adding a compile-time assertion or a runtime check (e.g., a `WARN_ONCE` if a calculated offset doesn't match an expected value) if possible, though this is often difficult with shader UBOs.
3.  **Consolidate Blending Logic (if feasible):** Evaluate if the core legacy blending equation can be abstracted into a shared GLSL function or macro to ensure consistency between `servers/rendering/renderer_rd/shaders/environment/sky.glsl` and `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl`. If not, ensure thorough comments explain why the logic is duplicated and how to keep it consistent.

## Traceability

Not specified