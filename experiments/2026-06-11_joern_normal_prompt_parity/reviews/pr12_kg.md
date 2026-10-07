```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a method to pick a random value from an array in the Godot Engine.

## Problem
1. The `pick_random` method uses `Math::rand()` which is not thread-safe and may lead to non-deterministic behavior in multi-threaded environments.
2. The method lacks test coverage to ensure its correctness and reliability, especially in edge cases like empty arrays.

## Evidence
- `core/array.cpp:411`: The use of `Math::rand()` for generating random indices.
- `core/array.cpp:408`: The error condition for empty arrays is handled, but no tests are provided to verify this behavior.

## Impact
- Using `Math::rand()` can lead to unpredictable results in multi-threaded applications, potentially causing hard-to-reproduce bugs.
- Lack of test coverage increases the risk of undetected bugs, especially when the method is used in various contexts or with different array sizes.

## Recommendation (Fix / Tests / Risks)
1. Replace `Math::rand()` with a thread-safe random number generator, such as `Math::random()`, which is designed for concurrent use.
2. Add unit tests for the `pick_random` method to cover scenarios including normal usage, empty arrays, and arrays with a single element.
3. Review the integration of this method in multi-threaded contexts to ensure it does not introduce concurrency issues.

## Traceability
- Code Owners: Not specified
```