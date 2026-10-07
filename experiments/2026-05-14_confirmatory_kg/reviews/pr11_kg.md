# Review Note — Evidence-Anchored

**Scope:** This PR introduces a `streamLoadedBuilds` method to `AbstractLazyLoadRunMap` and modifies `LazyBuildMixIn.getEstimatedDurationCandidates()` to use this new stream, aiming to avoid expensive full map copies for retrieving recent builds.

## Integration Risk
*   **`core/src/main/java/hudson/model/RunMap.java`**: This class extends `AbstractLazyLoadRunMap`. It inherits the modified `getLoadedBuilds()` method. While the public API signature (`SortedMap<Integer, R>`) remains the same, the internal implementation of `getLoadedBuilds()` has changed from lazy resolution of `R` objects via `BuildReferenceMapAdapter` to eager resolution of all `R` objects into a new `TreeMap`. Any code calling `RunMap.getLoadedBuilds()` (or `AbstractLazyLoadRunMap.getLoadedBuilds()`) will now incur the cost of eagerly loading and copying all `R` objects, potentially leading to a performance regression if those callers do not need all builds immediately.
*   **`core/src/main/java/hudson/model/Job.java`**, **`core/src/main/java/hudson/model/AbstractProject.java`**, **`core/src/main/java/jenkins/model/ParameterizedJobMixIn.java`**: These core classes frequently interact with `RunMap` or `AbstractLazyLoadRunMap` to access build history. If they call `getLoadedBuilds()`, they will be subject to the eager loading and full map copy, which could introduce performance overhead for operations that rely on this method.
*   **`core/src/test/java/jenkins/model/lazy/FakeMap.java`**, **`core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java`**, **`test/src/test/java/hudson/model/SimpleJobTest.java`**, **`test/src/test/java/jenkins/model/lazy/LazyBuildMixInTest.java`**: These are test files. While they depend on the changed code, any breakage would be caught by tests rather than causing runtime issues in production. `LazyBuildMixInTest.java` specifically tests `LazyBuildMixIn`, which now uses the new `streamLoadedBuilds()` method.

## Test Coverage Assessment
*   **`core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java`**:
    *   **`streamLoadedBuilds()`**: The new test `streamLoadedBuilds()` adequately covers the basic functionality, ordering, and short-circuiting behavior of the `streamLoadedBuilds()` method.
    *   **`getLoadedBuilds()`**: Existing tests for `getLoadedBuilds()` (e.g., `getLoadedBuilds()`, `getLoadedBuilds_empty()`, `getLoadedBuilds_with_unloaded()`) verify the functional correctness and content of the returned map. However, they do not specifically test the *performance characteristics* or the change from lazy to eager resolution of `R` objects within `getLoadedBuilds()`. This is a significant gap given the PR's performance-oriented goal.
*   **`test/src/test/java/jenkins/model/lazy/LazyBuildMixInTest.java`**: This test file covers `LazyBuildMixIn`. It is crucial that this file contains tests for `getEstimatedDurationCandidates()` that verify its functional correctness and, ideally, its performance improvement when dealing with a large number of builds, ensuring the `streamLoadedBuilds()` optimization is effective. Without specific tests for `getEstimatedDurationCandidates()`'s performance, the benefit of the PR for this method is not explicitly verified.

## Problem
1.  **Performance Regression for `getLoadedBuilds()`**: The `getLoadedBuilds()` method, despite the PR's intent to optimize build retrieval, has been re-implemented to eagerly load and copy *all* `R` objects into a new `TreeMap`. This replaces the previous lazy resolution mechanism provided by `BuildReferenceMapAdapter`. This change introduces a potential performance regression for any callers of `getLoadedBuilds()` that do not need all `R` objects immediately, as it now performs a full map copy and eager resolution, which is exactly what the PR aimed to avoid for `getEstimatedDurationCandidates()`.
2.  **Incomplete Test Coverage for Performance Changes**: There are no specific performance tests for the modified `getLoadedBuilds()` method in `AbstractLazyLoadRunMapTest.java`. This means a potential performance regression introduced by the eager loading could go unnoticed. Similarly, while `LazyBuildMixInTest.java` should cover the functional aspects of `getEstimatedDurationCandidates()`, there's no explicit verification of the performance improvement it was designed to achieve.
3.  **Missing `@since` Tag for New API**: The newly introduced `streamLoadedBuilds()` method is marked with `@since TODO`, which needs to be updated to the correct Jenkins version.

## Evidence
*   **`core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:249-259`**: Original implementation of `getLoadedBuilds()` using `BuildReferenceMapAdapter` (before PR).
*   **`core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:251-252`**: New implementation of `getLoadedBuilds()` which now eagerly populates a `TreeMap<Integer, R>` by calling `streamLoadedBuilds()`.
*   **`core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:261-265`**: Definition of the new `streamLoadedBuilds()` method, including the `@since TODO` tag.
*   **`core/src/main/java/hudson/model/RunMap.java`**: This file extends `AbstractLazyLoadRunMap`, making it a direct consumer of the changed `getLoadedBuilds()` behavior.
*   **`core/src/main/java/hudson/model/Job.java`**: A key dependent class that likely interacts with `RunMap` and its build retrieval methods.
*   **`core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java`**: Test file for `AbstractLazyLoadRunMap`, which lacks performance tests for `getLoadedBuilds()`.
*   **`test/src/test/java/jenkins/model/lazy/LazyBuildMixInTest.java`**: Test file for `LazyBuildMixIn`, which should verify the performance benefits of `getEstimatedDurationCandidates()`.

## Impact
*   **Performance Degradation**: Callers of `getLoadedBuilds()` (e.g., within `RunMap`, `Job`, `AbstractProject`) will now experience increased CPU and memory overhead due to the eager loading and full map copy, potentially negating the overall performance goals of the PR for other parts of the system.
*   **Unverified Optimizations**: Without specific performance tests, the intended performance benefits for `getEstimatedDurationCandidates()` might not be fully realized or could regress in the future without detection.
*   **API Documentation Inconsistency**: The `@since TODO` tag leaves the API documentation incomplete for the new `streamLoadedBuilds()` method.

## Recommendation
1.  **Revert `getLoadedBuilds()` change or provide an alternative**: Revert the changes to `getLoadedBuilds()` in `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java` to restore its original lazy resolution behavior via `BuildReferenceMapAdapter`. If an eager `SortedMap` is genuinely needed by some callers, consider introducing a *separate* method (e.g., `getAllLoadedBuildsEagerly()`) and deprecating `getLoadedBuilds()` if its lazy nature is no longer desired for all use cases. The current change to `getLoadedBuilds()` reintroduces the very performance issue the PR aimed to solve.
2.  **Add Performance Test for `getLoadedBuilds()`**: Introduce a new performance test in `core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java` that specifically measures the execution time and memory allocation of `getLoadedBuilds()` with a large number of builds (e.g., 10,000+). This test should establish a baseline and fail if performance significantly degrades.
3.  **Enhance `LazyBuildMixInTest.java` for `getEstimatedDurationCandidates()` Performance**: Add a performance-focused test to `test/src/test/java/jenkins/model/lazy/LazyBuildMixInTest.java` for `getEstimatedDurationCandidates()`. This test should simulate a large build history and verify that the method's execution time is significantly faster than it would be with a full map copy, confirming the benefit of `streamLoadedBuilds()`.
4.  **Update `@since` Tag**: Replace `@since TODO` with the actual Jenkins version (e.g., `@since 2.4XX`) for the `streamLoadedBuilds()` method in `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java`.

## Traceability
Not specified