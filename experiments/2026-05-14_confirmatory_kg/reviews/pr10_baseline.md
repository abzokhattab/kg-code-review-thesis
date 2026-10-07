# Review Note — Evidence-Anchored

**Scope:** This pull request introduces a new project setting to allow users to revert to a "legacy" volumetric fog blending behavior from previous Godot versions, primarily for visual compatibility during engine upgrades.

## Problem
1.  **Potential UBO/Shader Mismatch Risk:** While the UBO changes in C++ and GLSL appear to align, the use of `bool` in GLSL for a `uint32_t` in C++ within a `std140` uniform block, especially when replacing padding, introduces a subtle risk of alignment or packing issues across different GPU drivers or platforms.
2.  **Inconsistent "Legacy" Blending Logic:** The "legacy" blending behavior is implemented with different equations in `sky.glsl` and `scene_forward_clustered.glsl`, and even within `scene_forward_clustered.glsl` depending on whether `SCENE_DATA_FLAGS_USE_FOG` is active. It's not immediately clear if these distinct equations collectively represent the *exact* previous "incorrect" behavior across all scenarios, which could lead to unexpected visual discrepancies for users expecting a precise revert.
3.  **Lack of Specific Test Coverage:** The change introduces a new rendering path based on a project setting, but no specific tests (e.g., visual regression tests or dedicated unit tests for the blending math) are included to verify that the "legacy" behavior precisely matches the intended older behavior or that the "new" behavior remains correct when the flag is off.

## Evidence
*   `servers/rendering/renderer_rd/environment/sky.h:158-161` (UBO struct change in C++)
*   `servers/rendering/renderer_rd/shaders/environment/sky.glsl:78-81` (GLSL UBO struct change, using `bool` for `fog_use_legacy_blending`)
*   `servers/rendering/renderer_rd/shaders/environment/sky.glsl:286-292` (Conditional blending logic in sky shader)
*   `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl:1505-1518` (Conditional blending logic in forward clustered shader, with different equations)
*   No new test files or modifications to existing test files are present in the diff.

## Impact
*   **Rendering Artifacts/Crashes:** An UBO mismatch could lead to incorrect data being read by the shader, resulting in visual artifacts, corrupted rendering, or even GPU crashes, though less likely with `std140` and simple types.
*   **Subtle Visual Inconsistencies:** If the "legacy" blending equations are not perfectly aligned with the exact previous behavior, projects upgrading and enabling this flag might still experience subtle visual differences, defeating the primary purpose of the compatibility setting.
*   **Regression Risk:** Without specific tests, future changes to fog rendering might inadvertently break either the new or legacy blending paths, leading to regressions that are hard to detect.
*   **Increased Maintenance Burden:** Maintaining two distinct blending code paths adds complexity and potential for bugs in the long term.

## Recommendation (Fix / Tests / Risks)
1.  **UBO Type Consistency:** For `fog_use_legacy_blending` in `SkySceneData` GLSL UBO, consider using `uint` instead of `bool` to directly match the `uint32_t` type in the C++ `SkySceneState::UBO`. While `bool` might work due to `std140` rules, `uint` removes any ambiguity and potential for driver-specific packing issues.
2.  **Verify Legacy Blending Equations:** Thoroughly review and confirm that the specific blending equations implemented for the "legacy" path in both `sky.glsl` and `scene_forward_clustered.glsl` (including the `(1.0 - fog.a)` factors and `mix` calls) precisely replicate the *exact* behavior of the previous engine versions across all relevant fog configurations (e.g., volumetric fog only, environment fog only, both combined). This might involve comparing against the original PRs that introduced the "correct" behavior.
3.  **Add Visual Regression Tests (or Manual Verification Plan):** While automated visual tests are complex, consider adding a plan for manual visual verification for both the legacy and new blending modes across a range of test scenes. Ideally, a small set of visual regression tests could be created to capture screenshots of key scenarios for both modes, ensuring consistency over time.
4.  **Document Architectural Trade-offs:** Add a comment in the code or a more detailed note in the project settings documentation explaining the technical debt introduced by maintaining two blending paths and the rationale for doing so (user compatibility).

## Traceability
Not specified