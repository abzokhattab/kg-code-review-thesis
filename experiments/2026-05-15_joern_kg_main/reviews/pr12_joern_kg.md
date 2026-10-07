# Review Note — Evidence-Anchored

**Scope:** This pull request adds a new `pick_random()` method to the `Array` class, allowing users to retrieve a random element from an array, and exposes it to the scripting API and documentation.

## Problem
1.  **Non-Deterministic Randomness:** The `Array::pick_random()` method directly uses `Math::rand()`, which is a pseudo-random number generator that typically requires explicit seeding (e.g., via `Math::seed()` or `randomize()`) to produce non-deterministic sequences across different application runs. Without proper seeding, this method will yield the same sequence of "random" values every time, leading to predictable and potentially undesirable behavior in games or applications.
2.  **Lack of Test Coverage:** There are no new or modified test files included in this pull request to validate the functionality of `Array::pick_random()`. This leaves the new method vulnerable to regressions and makes it difficult to verify its correctness, especially concerning edge cases (empty arrays, single-element arrays) and the expected behavior of its random selection.

## Evidence
*   **Non-Deterministic Randomness:**
    *   `core/array.cpp:408`: `return operator[](Math::rand() % _p->array.size());` directly calls `Math::rand()`.
    *   The `core/math/math_funcs.h` header, included in `core/array.cpp`, defines `Math::rand()`.
*   **Lack of Test Coverage:**
    *   The provided diff does not include any changes to existing test files or the addition of new ones.
    *   The knowledge graph context does not list any test files (e.g., `test_array.cpp` or `test_core.cpp`) as being modified or added.
    *   The `_VariantCall` struct in `core/variant_call.cpp:578` and `register_variant_methods()` in `core/variant_call.cpp:1961` register `pick_random` for scripting, but its behavior is not verified by tests.

## Impact
*   **Predictable Application Behavior:** Any code that relies on `Array::pick_random()` for varied outcomes (e.g., enemy AI, item drops, procedural generation) will produce identical results on every application launch unless `Math::randomize()` or `Math::seed()` is called elsewhere in the project. This can lead to a poor user experience and make debugging harder.
*   **Untested Functionality:** Without dedicated tests, there's no automated way to ensure `pick_random()` correctly handles an empty array (which should return `Variant()`), an array with a single element, or that it selects elements from multi-element arrays as expected. Future changes to `Array`'s internal structure or `Math::rand()` could silently break this functionality.

## Recommendation (Fix / Tests / Risks)
1.  **Address Randomness Source:**
    *   **Option A (Preferred):** Change `Array::pick_random()` to use `Math::random()` instead of `Math::rand()`. `Math::random()` is typically seeded by `randomize()` at engine startup, providing a more generally useful pseudo-random sequence.
    *   **Option B (If `Math::rand()` is intentional):** Add a note to the `doc/classes/Array.xml` entry for `pick_random` clarifying that it uses `Math::rand()` and that users should call `Math::randomize()` or `Math::seed()` for non-deterministic results.
2.  **Add Comprehensive Unit Tests:**
    *   Create a new test case within an appropriate test file, such as `test_core.cpp` (or `test_array.cpp` if it exists), for `Array::pick_random()`.
    *   **Test Empty Array:** Assert that `Array().pick_random()` returns an empty `Variant()`, verifying the `ERR_FAIL_COND_V_MSG` logic.
    *   **Test Single-Element Array:** Assert that `Array([10]).pick_random()` consistently returns `10`.
    *   **Test Multi-Element Array (Deterministic):**
        *   Call `Math::seed(12345)` to ensure a reproducible random sequence.
        *   Create an array, e.g., `var arr = [1, 2, 3, 4]`.
        *   Call `arr.pick_random()` multiple times and assert that the sequence of returned values matches a pre-calculated, expected sequence for that specific seed.
    *   **Test Multi-Element Array (Distribution - Optional but Recommended):** Call `arr.pick_random()` a large number of times (e.g., 1000) and verify that all elements in the array have been picked at least once, indicating a reasonable distribution.

## Traceability
Not specified