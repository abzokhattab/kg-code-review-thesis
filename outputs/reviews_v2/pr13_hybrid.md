```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the code to use component-wise `min`, `max`, and `clamp` functions for `Vector*` types to improve readability and safety.

## Problem
1. **Potential for Incorrect Behavior**: The refactoring assumes that the new component-wise methods (`min`, `max`, `clamp`) behave identically to the previous implementations using `MIN`, `MAX`, and `CLAMP` macros. Any deviation in behavior could introduce subtle bugs.
2. **Lack of Test Coverage**: There is no indication that new tests have been added or existing tests have been updated to cover the changes, which could lead to undetected issues if the new methods do not behave as expected.

## Evidence
- **core/math/aabb.h:104**: Changed from `MIN` to `min` method.
- **core/math/delaunay_3d.h:285-287**: Replaced `CLAMP` with `clamp` method.
- **core/math/dynamic_bvh.h:380-386**: Replaced `MIN` and `MAX` with `min` and `max` methods.
- **scene/3d/decal.cpp:34**: Changed from `MAX` to `max` method.

## Impact
- **Technical Impact**: If the new methods do not handle edge cases or specific conditions as the macros did, it could lead to incorrect calculations, especially in geometry and rendering calculations where precision is crucial.
- **Risk of Regression**: Without adequate testing, there's a risk that existing functionality may break, leading to potential regressions in the application.

## Recommendation (Fix / Tests / Risks)
1. **Verify Method Equivalence**: Ensure that the new `min`, `max`, and `clamp` methods are functionally equivalent to the previous macro implementations, especially in edge cases.
2. **Enhance Test Coverage**: Add or update unit tests to cover scenarios affected by these changes, ensuring that the new methods behave as expected.
3. **Conduct Thorough Testing**: Perform integration testing to ensure that the changes do not introduce regressions in the system.

## Traceability
Not specified
```