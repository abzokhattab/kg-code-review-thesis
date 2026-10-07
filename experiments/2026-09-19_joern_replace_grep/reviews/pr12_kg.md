```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a method to pick a random value from an array in the Godot Engine.

## Problem
1. The `pick_random` method uses `Math::rand()` which is not thread-safe and may lead to non-deterministic behavior in multi-threaded environments.
2. The method does not account for the possibility of the array being modified concurrently, which could lead to undefined behavior or crashes.
3. There is no test coverage for the new `pick_random` method, which could lead to undetected bugs.

## Evidence
- `core/array.cpp:411`: The use of `Math::rand()` for random number generation.
- `core/array.cpp:408`: The method does not include any synchronization mechanisms to handle concurrent modifications.
- Lack of any new test cases in the PR diff for `pick_random`.

## Impact
- Using `Math::rand()` can lead to unpredictable results in multi-threaded applications, potentially causing hard-to-reproduce bugs.
- Without proper synchronization, concurrent modifications to the array could result in crashes or data corruption.
- Absence of tests increases the risk of introducing undetected bugs, especially in edge cases.

## Recommendation (Fix / Tests / Risks)
1. Replace `Math::rand()` with a thread-safe random number generator, such as `Math::randomize()` or another suitable alternative.
2. Implement synchronization mechanisms, such as mutexes, to ensure thread safety when accessing the array.
3. Add unit tests specifically for the `pick_random` method to cover various scenarios, including edge cases like empty arrays and concurrent access.

## Traceability
Not specified
```