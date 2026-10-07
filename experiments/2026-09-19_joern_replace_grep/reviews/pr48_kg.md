```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors `getLoadedBuilds()` to avoid unnecessary copying of builds by introducing a `BuildReferenceMapAdapter` backed by the existing `core` map.

## Problem
1. Lack of automated test coverage for new functionality introduced in `BuildReferenceMapAdapter`.
2. Potential performance issues with the `size()` method in `ConsistentSizeBuildReferenceMapAdapter`.
3. Risk of integration issues due to changes in core map handling logic.

## Evidence
- **core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:249-251**: The `getLoadedBuilds()` method now returns a `ConsistentSizeBuildReferenceMapAdapter`, which uses a potentially inefficient `size()` method.
- **core/src/main/java/jenkins/model/lazy/BuildReferenceMapAdapter.java:148-150**: The `size()` method in `ConsistentSizeBuildReferenceMapAdapter` iterates over all entries, which can be slow for large maps.
- **core/src/main/java/jenkins/model/lazy/BuildReferenceMapAdapter.java:327-328**: The new `BuildReferenceResolver` interface lacks direct test coverage, which could lead to undetected issues.

## Impact
- The inefficient `size()` method could lead to performance degradation in scenarios where `getLoadedBuilds()` is frequently called on large datasets.
- Without automated tests, the new `BuildReferenceResolver` logic might introduce bugs that are not caught during manual testing.
- Changes to core map handling logic could affect other parts of the system that rely on `RunMap` and `AbstractLazyLoadRunMap`, potentially causing integration issues.

## Recommendation (Fix / Tests / Risks)
1. **Tests**: Add unit tests specifically targeting the new `BuildReferenceResolver` implementations to ensure they function correctly.
2. **Performance**: Consider optimizing the `size()` method in `ConsistentSizeBuildReferenceMapAdapter` or document its intended use to prevent misuse in performance-critical paths.
3. **Integration**: Conduct thorough integration testing to ensure that changes to map handling do not adversely affect dependent components.

## Traceability
- Code Owners: @jglick, @timja, @bennettzhu1
```