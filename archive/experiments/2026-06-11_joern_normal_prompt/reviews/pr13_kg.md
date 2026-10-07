```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the code to use component-wise `min/max/clamp` functions for `Vector*` types where applicable.

## Problem
1. Potential performance impact due to increased function call overhead.
2. Risk of introducing subtle bugs if the new methods do not behave identically to the previous inline logic.
3. Lack of test coverage for the new component-wise methods to ensure they handle edge cases correctly.

## Evidence
- **core/math/aabb.h:102**: Changed `MIN` usage to `size.min(Vector3())`.
- **core/math/delaunay_3d.h:284**: Replaced multiple `CLAMP` calls with `grid_pos.clamp(Vector3i(), Vector3i(...))`.
- **core/math/dynamic_bvh.h:379**: Replaced multiple `MIN` and `MAX` calls with `volume.min.min(p_points[i])` and `volume.max.max(p_points[i])`.

## Impact
- **Performance**: The use of method calls instead of inline operations could introduce slight performance degradation, especially in performance-critical sections of the code.
- **Functionality**: If the new methods do not perfectly replicate the behavior of the previous logic, it could lead to incorrect calculations, particularly in geometric computations.
- **Testing**: Without additional tests, it is difficult to ensure that the new methods handle all edge cases, such as negative values or zero-length vectors.

## Recommendation (Fix / Tests / Risks)
1. **Performance Testing**: Conduct performance benchmarks to ensure that the refactoring does not introduce significant overhead.
2. **Unit Tests**: Add unit tests specifically for the new `min`, `max`, and `clamp` methods to verify their correctness across a range of inputs.
3. **Code Review**: Ensure that the new methods are reviewed for logical equivalence to the previous inline operations to prevent functional regressions.

## Traceability
- **Code Owners**: Not specified
```