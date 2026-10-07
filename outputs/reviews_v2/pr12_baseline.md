```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a method to the Array class to pick a random value from the array.

## Problem
1. The `pick_random` method uses `Math::rand()` which may not be thread-safe or provide sufficient randomness.
2. Lack of test coverage for the new `pick_random` method to ensure its correctness and robustness.

## Evidence
- `core/array.cpp:411`: The method `pick_random` uses `Math::rand()` for generating a random index.
- `core/array.cpp:408`: The method does not include any test cases in the PR to validate its functionality.

## Impact
- Using `Math::rand()` could lead to predictable random values, especially if the random number generator is not properly seeded, which might not be suitable for all use cases.
- Without tests, there is a risk of introducing bugs or unexpected behavior in the `pick_random` method, which could affect any functionality relying on this method.

## Recommendation (Fix / Tests / Risks)
1. Consider using a more robust random number generator, such as `Math::random()` or another thread-safe alternative, to ensure better randomness.
2. Add unit tests for the `pick_random` method to verify its behavior with different array sizes and contents, including edge cases like empty arrays.
3. Ensure that the random number generator is properly seeded if necessary to avoid predictable sequences.

## Traceability
Not specified
```