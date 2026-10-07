```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors `getLoadedBuilds()` to avoid unnecessary copying of builds by introducing a `BuildReferenceMapAdapter` backed by the existing `core` map.

## Problem
1. Lack of automated tests for the new `BuildReferenceMapAdapter` and its resolvers.
2. Potential performance issues with the `ConsistentSizeBuildReferenceMapAdapter` due to inefficient `size()` implementation.
3. Risk of incorrect behavior in `getEstimatedDurationCandidates()` due to changes in iteration logic.

## Evidence
- `jenkins/model/lazy/AbstractLazyLoadRunMap.java:249-251`: Introduction of `ConsistentSizeBuildReferenceMapAdapter` with a note about inefficient `size()` method.
- `jenkins/model/lazy/LazyBuildMixIn.java:273-274`: Changes in `getEstimatedDurationCandidates()` logic, potentially affecting candidate selection.
- Absence of new test cases in the diff for `BuildReferenceMapAdapter` and its new resolvers.

## Impact
- Without automated tests, there's a risk of introducing regressions or incorrect behavior in build reference resolution.
- The inefficient `size()` method in `ConsistentSizeBuildReferenceMapAdapter` could lead to performance degradation, especially with large datasets.
- Changes in iteration logic for `getEstimatedDurationCandidates()` might lead to unexpected results, affecting build duration estimation.

## Recommendation (Fix / Tests / Risks)
1. Implement unit tests for `BuildReferenceMapAdapter`, `LoadedOnlyBuildReferenceResolver`, and `DefaultBuildReferenceResolver` to ensure correct behavior.
2. Optimize the `size()` method in `ConsistentSizeBuildReferenceMapAdapter` or provide clear documentation on its intended use to avoid performance pitfalls.
3. Review and test the logic changes in `getEstimatedDurationCandidates()` to ensure it meets the intended functionality and does not introduce regressions.

## Traceability
Not specified
```