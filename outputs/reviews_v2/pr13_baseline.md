```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the code to use component-wise `min`, `max`, and `clamp` functions for `Vector*` types to improve readability and safety.

## Problem
1. Potential for incorrect behavior if the new `min`, `max`, and `clamp` methods do not handle edge cases as expected.
2. Lack of test coverage to ensure that the refactored methods behave identically to the previous implementations.

## Evidence
- `core/math/aabb.h:104`: Changed from `MIN` to `size.min(Vector3())`.
- `core/math/delaunay_3d.h:285`: Replaced multiple `CLAMP` calls with `grid_pos.clamp(...)`.
- `scene/3d/decal.cpp:34`: Changed from `MAX` to `p_size.max(Vector3(0.001, 0.001, 0.001))`.

## Impact
- The refactoring could introduce subtle bugs if the new methods do not perfectly replicate the behavior of the original `MIN`, `MAX`, and `CLAMP` macros.
- Without adequate testing, there is a risk of regression, especially in edge cases where the original macros might have had specific handling.

## Recommendation (Fix / Tests / Risks)
1. **Tests**: Implement unit tests for the `min`, `max`, and `clamp` methods to ensure they handle all edge cases correctly.
2. **Verification**: Manually verify that the behavior of the refactored code matches the original, especially in critical areas like rendering and physics calculations.
3. **Documentation**: Update documentation to reflect the changes in method usage, ensuring that future developers understand the new approach.

## Traceability
Not specified
```