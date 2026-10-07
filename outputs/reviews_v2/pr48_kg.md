```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors `getLoadedBuilds()` to avoid unnecessary copying by using a `BuildReferenceMapAdapter` backed by the existing `core` map.

## Problem
1. Lack of automated test coverage for new classes and methods introduced, such as `LoadedOnlyBuildReferenceResolver` and `ConsistentSizeBuildReferenceMapAdapter`.
2. Potential performance issues with the `size()` method in `ConsistentSizeBuildReferenceMapAdapter` due to full collection scans.
3. Risk of integration issues due to changes in core map handling, which might affect other components relying on `AbstractLazyLoadRunMap`.

## Evidence
- **core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:249-251**: Introduction of `ConsistentSizeBuildReferenceMapAdapter` with a potentially inefficient `size()` method.
- **core/src/main/java/jenkins/model/lazy/BuildReferenceMapAdapter.java:148-150**: The `size()` method implementation iterates over all entries, which can be slow for large maps.
- **core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:36-37**: Changes in map handling logic that could impact other components.

## Impact
- The lack of automated tests for new components increases the risk of undetected bugs and regressions.
- Performance degradation in scenarios where `size()` is frequently called on large maps.
- Potential integration issues with other parts of the system that depend on the behavior of `AbstractLazyLoadRunMap`.

## Recommendation (Fix / Tests / Risks)
1. **Tests**: Add unit tests for `LoadedOnlyBuildReferenceResolver` and `ConsistentSizeBuildReferenceMapAdapter` to ensure their correctness and performance.
2. **Performance**: Consider optimizing the `size()` method in `ConsistentSizeBuildReferenceMapAdapter` to avoid full collection scans.
3. **Integration**: Conduct thorough integration testing to ensure that changes in map handling do not adversely affect other components.

## Traceability
- Code Owners: @jglick, @timja, @bennettzhu1
```