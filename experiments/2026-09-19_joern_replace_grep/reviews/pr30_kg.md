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
- `tests/scene/test_texture_rect.cpp:30, 60, 90, 120, 150, 180, 210`: Manual memory management with `memnew` and `memdelete` without exception handling.

## Impact
- The lack of integration tests may lead to undetected issues when `TextureRect` is used in complex scenes, potentially causing runtime errors or unexpected behavior.
- Missing edge case tests could result in unhandled exceptions or incorrect behavior when `TextureRect` is used with unusual inputs.
- Manual memory management without exception handling could lead to memory leaks or crashes if an exception occurs before `memdelete` is called.

## Recommendation (Fix / Tests / Risks)
1. Add integration tests that place `TextureRect` within a scene with other nodes to verify its behavior in a more realistic context.
2. Implement tests for edge cases, such as setting invalid textures or using extreme values for properties.
3. Consider using smart pointers or exception-safe constructs to manage memory and avoid potential leaks or crashes.

## Traceability
Not specified
```