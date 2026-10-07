```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a method to pick a random value from an array in the Godot Engine.

## Problem
1. The use of `Math::rand()` for random number generation is not thread-safe and may lead to predictable results.
2. Lack of test coverage for the new `pick_random` method, which could lead to undetected bugs or regressions.
3. The error message in `pick_random` when the array is empty is not consistent with other error messages in the codebase.

## Evidence
- `core/array.cpp:410`: The use of `Math::rand()` for generating random indices.
- `core/array.cpp:408`: The error message "Can't take value from empty array." is hardcoded and not localized.
- No new test cases added in the PR for `pick_random`.

## Impact
- Using `Math::rand()` can lead to non-deterministic behavior in multi-threaded environments, potentially causing hard-to-reproduce bugs.
- Without tests, future changes to the array class might inadvertently break the `pick_random` functionality without detection.
- Inconsistent error messaging can lead to confusion for developers and users, especially in a localized environment.

## Recommendation (Fix / Tests / Risks)
1. Replace `Math::rand()` with a thread-safe and more robust random number generator, such as `Math::randomize()` or `Math::randf()`.
2. Add unit tests for the `pick_random` method to ensure it behaves correctly, especially with edge cases like empty arrays.
3. Update the error message to use a consistent and localized format, possibly using `ERR_FAIL_COND_V_MSG` with a localized string.

## Traceability
Not specified
```