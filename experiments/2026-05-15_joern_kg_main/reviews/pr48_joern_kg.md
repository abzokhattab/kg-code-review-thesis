# Review Note — Evidence-Anchored

**Scope:** This PR refactors `AbstractLazyLoadRunMap` to optimize `getLoadedBuilds()` by returning an adapter that avoids copying all builds, and introduces new interfaces for build reference resolution and type description.

## Problem

1.  **Performance Regression in `getLoadedBuilds().size()`:** The change to `AbstractLazyLoadRunMap.getLoadedBuilds()` now returns a `ConsistentSizeBuildReferenceMapAdapter`. This adapter's `size()` method explicitly warns that it performs a full collection scan and can be very slow. Any existing code that calls `size()` on the map returned by `getLoadedBuilds()` will now experience a significant performance degradation, especially in large Jenkins instances.
2.  **Potential Inconsistency in `CopyOnWriteMap` `hashCode`/`equals`/`toString`:** The `hashCode()`, `equals()`, and `toString()` methods in `CopyOnWriteMap` have been changed to operate directly on the internal `core` map instead of first creating a `copy()`. While `CopyOnWriteMap` is designed for thread-safe reads, directly accessing `core` might expose intermediate states during a write operation, potentially leading to inconsistent results for these methods if the map is modified concurrently.
3.  **Subtle Logic Change in `LazyBuildMixIn.getEstimatedDurationCandidates()`:** The refactoring of `getEstimatedDurationCandidates()` alters the strategy for selecting builds. The new logic iterates once, prioritizing `UNSTABLE` or better builds, then filling remaining slots with `FAILURE` or better builds. This is a change from the previous two-pass iteration with explicit `candidates.contains(build)` checks, which could result in a different set of up to three candidate builds being returned, potentially affecting duration estimations.

## Evidence

*   **Problem 1:**
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:251`: `getLoadedBuilds()` now returns `new ConsistentSizeBuildReferenceMapAdapter(...)`.
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:50` (within `ConsistentSizeBuildReferenceMapAdapter`): The `size()` method's Javadoc explicitly states: "Avoid using this method as it performs a full collection scan and can be very slow for large maps. Suitable for tests only."
*   **Problem 2:**
    *   `core/src/main/java/hudson/util/CopyOnWriteMap.java:172`: `hashCode()` changed from `copy().hashCode()` to `core.hashCode()`.
    *   `core/src/main/java/hudson/util/CopyOnWriteMap.java:176`: `equals()` changed from `copy().equals(obj)` to `core.equals(obj)`.
    *   `core/src/main/java/hudson/util/CopyOnWriteMap.java:180`: `toString()` changed from `copy().toString()` to `core.toString()`.
*   **Problem 3:**
    *   `core/src/main/java/jenkins/model/lazy/LazyBuildMixIn.java:273-297`: The entire `getEstimatedDurationCandidates()` method has been rewritten, changing the iteration and selection logic for `candidates` and `failureCandidates`.

## Impact

*   **Problem 1:** Any code path, such as `hudson.model.AbstractProject.getBuilds().size()` (which calls `_getRuns().getLoadedBuilds().size()`), that relies on `getLoadedBuilds().size()` will now iterate over all loaded builds, leading to a performance bottleneck and increased CPU usage, especially for jobs with many builds.
*   **Problem 2:** If `CopyOnWriteMap` instances are used in contexts where `hashCode()` or `equals()` are called concurrently with write operations (e.g., `hudson.logging.LogRecorderManager.setRecorders` which uses `CopyOnWriteMap.replaceBy`), these methods might return inconsistent results, potentially breaking collection contracts or leading to unexpected behavior.
*   **Problem 3:** The change in candidate selection for `LazyBuildMixIn.getEstimatedDurationCandidates()` could lead to different builds being chosen for duration estimation. This might result in less accurate or inconsistent build duration predictions, affecting user experience and potentially downstream automation that relies on these estimations.

## Recommendation (Fix / Tests / Risks)

1.  **Address `getLoadedBuilds().size()` Performance:**
    *   **Fix:** Review all callers of `AbstractLazyLoadRunMap.getLoadedBuilds().size()`. For example, `hudson.model.AbstractProject.getBuilds()` returns a `RunMap` which extends `AbstractLazyLoadRunMap`. If `size()` is not strictly required, replace it with `streamLoadedBuilds().count()` or `isEmpty()` as appropriate. If `size()` is truly needed, consider if the `ConsistentSizeBuildReferenceMapAdapter` is the correct return type for `getLoadedBuilds()` or if a different approach is needed.
    *   **Tests:** Add a performance test to `core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java` that specifically measures the execution time of `getLoadedBuilds().size()` for a large number of builds (e.g., 10,000 builds) to ensure it meets performance expectations.
2.  **Restore `CopyOnWriteMap` Consistency:**
    *   **Fix:** Revert the changes to `hashCode()`, `equals()`, and `toString()` in `core/src/main/java/hudson/util/CopyOnWriteMap.java` to use `copy()` to ensure these methods operate on a consistent snapshot of the map, aligning with the Copy-On-Write pattern.
    *   **Tests:** Add specific unit tests to `core/src/test/java/hudson/util/CopyOnWriteMapTest.java` to verify the consistency of `hashCode()`, `equals()`, and `toString()` under concurrent modification scenarios.
3.  **Verify `getEstimatedDurationCandidates()` Logic:**
    *   **Fix:** Clarify whether the change in candidate selection logic for `LazyBuildMixIn.getEstimatedDurationCandidates()` is intentional. If so, document the new selection criteria clearly. If not, revert to the previous logic or adjust to match the original intent.
    *   **Tests:** Add comprehensive unit tests to `test/src/test/java/jenkins/model/lazy/LazyBuildMixInTest.java` with various build result scenarios (e.g., many `SUCCESS`, few `UNSTABLE`, many `FAILURE` builds) to explicitly verify the exact set of builds returned by `getEstimatedDurationCandidates()` under the new logic, ensuring it aligns with the desired behavior.

## Traceability

Not specified