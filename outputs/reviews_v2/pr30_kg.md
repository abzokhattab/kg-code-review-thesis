```
# Review Note — Evidence-Anchored

**Scope:** This PR adds unit tests for the `TextureRect` class in the Godot Engine.

## Problem
1. Lack of integration tests to ensure `TextureRect` behaves correctly within a full scene context.
2. Absence of tests for edge cases, such as invalid texture inputs or extreme property values.
3. Potential memory management issues due to manual memory allocation and deallocation.

## Evidence
- `tests/scene/test_texture_rect.cpp:15-222`: All tests are unit tests focusing on individual properties and methods of `TextureRect`.
- `tests/scene/test_texture_rect.cpp:20, 40, 60, 80, 100, 120, 140, 160, 180, 200`: Manual memory management with `memnew` and `memdelete` is used throughout the test cases.

## Impact
- Without integration tests, there is a risk that `TextureRect` may not interact correctly with other components in a real-world scene, leading to unexpected behavior.
- Missing edge case tests could result in unhandled exceptions or incorrect behavior when `TextureRect` is used with unusual inputs.
- Manual memory management increases the risk of memory leaks or segmentation faults if not handled correctly.

## Recommendation (Fix / Tests / Risks)
1. Add integration tests that place `TextureRect` within a complete scene to verify its behavior in a realistic context.
2. Introduce tests for edge cases, such as setting invalid textures or using extreme values for properties.
3. Consider using smart pointers or other memory management techniques to reduce the risk of memory-related issues.

## Traceability
Not specified
```