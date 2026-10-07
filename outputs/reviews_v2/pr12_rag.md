```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a method to pick a random value from an array in the Godot Engine.

## Problem
1. The use of `Math::rand()` for random number generation is not thread-safe and may not provide sufficient randomness.
2. The method `pick_random()` does not handle the case where the array size changes between the size check and the element access.
3. Lack of test coverage for the new `pick_random()` method.

## Evidence
- `core/array.cpp:408`: The use of `Math::rand()` for generating a random index.
- `core/array.cpp:408`: The array size is checked, but not locked, before accessing an element.
- No new test cases are added in the diff to cover the `pick_random()` method.

## Impact
- Using `Math::rand()` can lead to predictable random values, which might not be suitable for all use cases, especially in a multi-threaded environment.
- If the array size changes between the size check and the element access, it could lead to accessing an invalid index, causing undefined behavior or crashes.
- Without tests, the new functionality might introduce bugs that go unnoticed until runtime.

## Recommendation (Fix / Tests / Risks)
1. Use a more robust random number generator, such as `Math::random()` or a thread-safe alternative.
2. Consider locking the array or using a snapshot of the array size to ensure safe access.
3. Add unit tests to cover the `pick_random()` method, ensuring it behaves correctly with various array sizes and contents.

## Traceability
Not specified
```