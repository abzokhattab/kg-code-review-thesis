```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors `getLoadedBuilds()` to avoid unnecessary copying by using a `BuildReferenceMapAdapter` backed by the existing `core` map.

## Problem
1. The `getLoadedBuilds()` method now returns a `ConsistentSizeBuildReferenceMapAdapter`, which may introduce performance issues due to its inefficient `size()` method.
2. The `DefaultBuildReferenceResolver` and `LoadedOnlyBuildReferenceResolver` implementations may not be adequately tested for edge cases, such as handling null references or large datasets.
3. The removal of the `search` method's logic in favor of using `adapter` methods might lead to unexpected behavior changes if not thoroughly validated.

## Evidence
- `AbstractLazyLoadRunMap.java:249-251`: The `getLoadedBuilds()` method now uses `ConsistentSizeBuildReferenceMapAdapter`, which has a potentially inefficient `size()` method.
- `AbstractLazyLoadRunMap.java:530-574`: Introduction of `DefaultBuildReferenceResolver` and `LoadedOnlyBuildReferenceResolver` without evidence of comprehensive test coverage.
- `AbstractLazyLoadRunMap.java:339-344`: The `search` method's logic has been replaced with `adapter` methods, which may alter its behavior.

## Impact
- The inefficient `size()` method in `ConsistentSizeBuildReferenceMapAdapter` could lead to performance degradation, especially in environments with a large number of builds.
- Insufficient testing of the new resolver implementations could result in runtime errors or incorrect build resolutions, particularly in edge cases.
- Changes in the `search` method's behavior could introduce regressions if the new logic does not fully replicate the previous functionality.

## Recommendation (Fix / Tests / Risks)
1. Optimize the `size()` method in `ConsistentSizeBuildReferenceMapAdapter` to avoid full collection scans.
2. Add comprehensive unit tests for `DefaultBuildReferenceResolver` and `LoadedOnlyBuildReferenceResolver` to cover edge cases and ensure robustness.
3. Conduct thorough regression testing on the `search` method to confirm that the new implementation behaves as expected in all scenarios.

## Traceability
Not specified
```