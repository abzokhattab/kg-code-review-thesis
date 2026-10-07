```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the code to use component-wise `min`, `max`, and `clamp` functions for `Vector*` types to improve readability and safety.

## Problem
1. Inconsistent use of `clamp` and `min/max` functions across different files.
2. Potential for logical errors due to incorrect assumptions about vector operations.
3. Lack of test coverage for the new component-wise operations.

## Evidence
- `core/math/aabb.h:104`: Changed from `MIN` to `size.min(Vector3())`.
- `core/math/delaunay_3d.h:285`: Replaced multiple `CLAMP` calls with `grid_pos.clamp(Vector3i(), Vector3i(...))`.
- `scene/3d/decal.cpp:34`: Changed from `MAX` to `p_size.max(Vector3(...))`.

## Impact
- The changes could introduce subtle bugs if the new component-wise operations do not behave as expected in all scenarios.
- The refactoring might lead to performance implications if the new methods are not optimized.
- Without adequate testing, there is a risk of regression in functionality where these operations are critical.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure that all vector operations are consistent and correctly applied across the codebase.
2. **Tests:** Add unit tests specifically for the new component-wise `min`, `max`, and `clamp` functions to verify their correctness.
3. **Risks:** Review the performance implications of these changes, especially in performance-critical sections of the code.

## Traceability
Not specified
```