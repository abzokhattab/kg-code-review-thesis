```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors `getLoadedBuilds()` to avoid unnecessary copying of builds by introducing a `BuildReferenceMapAdapter` backed by the existing `core` map.

## Problem
1. **Potential Performance Degradation:** The new `ConsistentSizeBuildReferenceMapAdapter` implementation of `size()` iterates over all entries, which could lead to performance issues for large maps.
2. **Lack of Automated Tests:** The PR mentions manual testing but lacks evidence of comprehensive automated test coverage for the new functionality.
3. **Backward Compatibility Concerns:** Changes in the `BuildReferenceMapAdapter` and its interfaces might affect existing integrations or plugins relying on the previous behavior.

## Evidence
- **Performance Issue:** `AbstractLazyLoadRunMap.java: lines 249-251` — The `size()` method in `ConsistentSizeBuildReferenceMapAdapter` iterates over all entries, which is inefficient.
- **Lack of Tests:** No new test cases are added in `AbstractLazyLoadRunMapTest.java` or related test files to cover the new `LoadedOnlyBuildReferenceResolver` and `DefaultBuildReferenceResolver`.
- **Backward Compatibility:** Changes in `BuildReferenceMapAdapter.java: lines 22-328` — Introduction of new interfaces and changes in method signatures.

## Impact
- **Performance Risks:** The inefficient `size()` method could lead to significant slowdowns in environments with a large number of builds.
- **Potential Bugs:** Without automated tests, there's a risk of introducing bugs that could affect the stability of Jenkins instances.
- **Integration Breakage:** Changes to public interfaces might break existing plugins or custom integrations that depend on the previous API.

## Recommendation (Fix / Tests / Risks)
1. **Optimize `size()` Method:** Consider implementing a more efficient way to calculate the size without iterating over all entries.
2. **Add Automated Tests:** Introduce comprehensive test cases to cover the new functionality and ensure backward compatibility.
3. **Review API Changes:** Evaluate the impact of interface changes on existing plugins and provide migration guidelines if necessary.

## Traceability
- **Code Owners:** @jglick, @timja, @bennettzhu1
```