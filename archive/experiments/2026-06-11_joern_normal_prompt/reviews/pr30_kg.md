```
# Review Note — Evidence-Anchored

**Scope:** This PR adds unit tests for the `TextureRect` class in the Godot Engine.

## Problem
1. Lack of integration tests to ensure `TextureRect` behaves correctly within a full scene.
2. Potential memory management issues due to manual memory allocation and deallocation.
3. Absence of tests for edge cases, such as invalid texture inputs or extreme size values.

## Evidence
- `tests/scene/test_texture_rect.cpp:16-222`: All tests are unit tests focusing on individual methods without integration into a larger scene context.
- `tests/scene/test_texture_rect.cpp:20, 221`: Manual memory management with `memnew` and `memdelete` could lead to memory leaks if not handled correctly.
- `tests/scene/test_texture_rect.cpp:50-60`: Tests do not cover scenarios where invalid or null textures are set, which could lead to unexpected behavior.

## Impact
- Without integration tests, there is a risk that `TextureRect` may not interact correctly with other components in a real-world scene, potentially leading to runtime errors.
- Manual memory management increases the risk of memory leaks or crashes if objects are not properly deleted.
- Lack of edge case testing could result in unhandled exceptions or incorrect rendering when unexpected inputs are provided.

## Recommendation (Fix / Tests / Risks)
1. Add integration tests that place `TextureRect` within a scene to verify its behavior in a more realistic context.
2. Consider using smart pointers or other memory management techniques to reduce the risk of memory leaks.
3. Expand test coverage to include edge cases, such as setting null or invalid textures and handling extreme size values.

## Traceability
Not specified
```