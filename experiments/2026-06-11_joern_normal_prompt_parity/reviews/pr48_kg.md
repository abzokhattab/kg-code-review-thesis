```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors `getLoadedBuilds()` to avoid unnecessary copying of builds by introducing a `BuildReferenceMapAdapter` backed by the existing `core` map.

## Problem
1. **Potential Performance Degradation:** The new `ConsistentSizeBuildReferenceMapAdapter` in `getLoadedBuilds()` may cause performance issues due to its inefficient `size()` method.
2. **Insufficient Test Coverage:** The changes in `AbstractLazyLoadRunMap` and `BuildReferenceMapAdapter` lack corresponding automated tests to ensure the new logic works as intended.
3. **Integration Risk:** The refactoring introduces new classes and interfaces that may affect existing integrations, especially those relying on `BuildReferenceMapAdapter`.

## Evidence
- **Performance Concern:** `AbstractLazyLoadRunMap.java:249-251` — The `ConsistentSizeBuildReferenceMapAdapter` uses a full collection scan for `size()`, which can be slow for large maps.
- **Test Coverage:** No new tests in `AbstractLazyLoadRunMapTest.java` or `BuildReferenceMapAdapterTest.java` to validate the behavior of `LoadedOnlyBuildReferenceResolver` and `DefaultBuildReferenceResolver`.
- **Integration Risk:** `BuildReferenceMapAdapter.java:43-328` — Introduction of new interfaces and classes (`BuildReferenceResolver`, `BuildTypeDescriptor`) without clear backward compatibility checks.

## Impact
- **Performance Impact:** The inefficient `size()` method could lead to significant slowdowns in environments with large datasets, affecting overall system performance.
- **Reliability Risk:** Lack of automated tests increases the risk of undetected bugs, potentially leading to runtime errors or incorrect behavior in production.
- **Compatibility Concerns:** Changes to core interfaces and classes may break existing plugins or extensions that depend on the previous behavior.

## Recommendation (Fix / Tests / Risks)
1. **Optimize `size()` Method:** Refactor the `ConsistentSizeBuildReferenceMapAdapter` to provide a more efficient implementation of the `size()` method.
2. **Enhance Test Coverage:** Add unit tests in `AbstractLazyLoadRunMapTest.java` and `BuildReferenceMapAdapterTest.java` to cover new logic introduced by `LoadedOnlyBuildReferenceResolver` and `DefaultBuildReferenceResolver`.
3. **Conduct Integration Testing:** Perform thorough integration testing to ensure that changes do not adversely affect existing plugins or extensions.

## Traceability
- **Code Owners:** @jglick, @timja, @bennettzhu1
```