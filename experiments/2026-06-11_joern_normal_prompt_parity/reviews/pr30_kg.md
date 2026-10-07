```
# Review Note — Evidence-Anchored

**Scope:** This PR adds unit tests for the `TextureRect` class in the Godot Engine.

## Problem
1. Lack of integration tests to ensure `TextureRect` behaves correctly within a full scene context.
2. Absence of tests for edge cases, such as invalid texture inputs or extreme property values.
3. Potential memory management issues due to manual memory allocation and deallocation.

## Evidence
- `tests/scene/test_texture_rect.cpp:15-222`: All tests are unit tests focusing on individual properties and methods of `TextureRect`.
- `tests/scene/test_texture_rect.cpp:20-222`: No tests simulate a full scene setup or interaction with other nodes.
- `tests/scene/test_texture_rect.cpp:20-222`: Memory is manually allocated with `memnew` and deallocated with `memdelete`, which can lead to memory leaks if not handled correctly.

## Impact
- Without integration tests, there is a risk that `TextureRect` may not function as expected when used in a real-world scene, potentially leading to runtime errors or unexpected behavior.
- Missing edge case tests could result in unhandled exceptions or incorrect behavior when `TextureRect` is used with unusual inputs.
- Manual memory management increases the risk of memory leaks or crashes if objects are not properly deleted.

## Recommendation (Fix / Tests / Risks)
1. Add integration tests that place `TextureRect` within a scene and verify its behavior in conjunction with other nodes.
2. Implement tests for edge cases, such as setting invalid textures or using extreme values for properties.
3. Consider using smart pointers or other memory management techniques to reduce the risk of memory leaks.

## Traceability
Not specified
```