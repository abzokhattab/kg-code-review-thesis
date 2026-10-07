```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a method to pick a random value from an array.

## Problem
1. The `pick_random` method uses `Math::rand()` which is not thread-safe and may lead to non-deterministic behavior in multi-threaded environments.
2. The method does not seed the random number generator, which could lead to predictable sequences of random numbers if not handled elsewhere.
3. Lack of test coverage for the new `pick_random` method, which could lead to undetected bugs or regressions.

## Evidence
- `core/array.cpp:411`: The use of `Math::rand()` without seeding or thread-safety considerations.
- `core/array.cpp:408`: The method is added without corresponding test cases in the test suite.

## Impact
- Using `Math::rand()` without thread safety can cause unpredictable behavior in concurrent applications, potentially leading to incorrect data being returned.
- Without seeding, the randomness may not be sufficient for applications relying on truly random behavior, leading to predictable outcomes.
- Absence of tests increases the risk of future changes breaking this functionality without detection.

## Recommendation (Fix / Tests / Risks)
1. Consider using a thread-safe random number generator or ensure that `Math::rand()` is used in a thread-safe manner.
2. Ensure that the random number generator is properly seeded to avoid predictable random sequences.
3. Add unit tests for the `pick_random` method to verify its behavior under various conditions, including edge cases like empty arrays.

## Traceability
Not specified
```