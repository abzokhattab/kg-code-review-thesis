# Review Note — Evidence-Anchored

**Scope:** This PR introduces a new method `streamLoadedBuilds` to lazily iterate over loaded builds, aiming to optimize `getEstimatedDurationCandidates` by avoiding a full map copy.

## Problem
1.  **Incorrect Sorting in `streamLoadedBuilds()`:** The `streamLoadedBuilds()` method, despite its Javadoc claiming "sorted by newest first", does not guarantee any specific order because it streams values from a `HashMap` (`core.values().stream()`). This directly breaks the logic of `getEstimatedDurationCandidates()`, which explicitly relies on builds being in reverse chronological order to find the most recent candidates.
2.  **Potential Loss of `isUnloadable()` Filter:** The original `getLoadedBuilds()` explicitly filtered out builds where `buildRef.isUnloadable()` was true. The new `streamLoadedBuilds()` only filters `Objects::nonNull` after calling `BuildReference::get()`. If `BuildReference::get()` returns a non-null value for an unloadable build (meaning it's currently loaded but eligible for GC), then `streamLoadedBuilds()` will include builds that the previous `getLoadedBuilds()` implementation would have excluded, potentially changing the set of "loaded builds" considered.
3.  **`getLoadedBuilds()` Still Performs Full Map Copy and Eager Unwrapping:** While `streamLoadedBuilds()` is introduced for lazy iteration, the `getLoadedBuilds()` method itself is refactored to *use* `streamLoadedBuilds()` but then immediately collects *all* results into a new `TreeMap`. This means `getLoadedBuilds()` still performs a full copy of all loaded builds and eagerly unwraps all `BuildReference` objects, negating the "avoid full map copy" benefit for any other callers of `getLoadedBuilds()`. The change from `BuildReferenceMapAdapter` to a direct `TreeMap<Integer, R>` also means all `BuildReference` objects are unwrapped upfront, potentially increasing memory usage for callers of `getLoadedBuilds()`.

## Evidence
*   **Incorrect Sorting:**
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:260` (`streamLoadedBuilds()` implementation: `core.values().stream()`)
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:257` (`streamLoadedBuilds()` Javadoc: "sorted by newest first")
    *   `core/src/main/java/jenkins/model/lazy/LazyBuildMixIn.java:276` (`getEstimatedDurationCandidates()` comment: `// reverse chronological order`)
    *   `core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java:417` (Test `assertEquals(List.of(5, 3, 1), fromStream);` relies on non-guaranteed `HashMap` order)
*   **Potential Loss of Filter:**
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:244` (Original `getLoadedBuilds()` filter: `!buildRef.isUnloadable()`)
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:262` (`streamLoadedBuilds()` filter: `filter(Objects::nonNull)`)
*   **`getLoadedBuilds()` Still Copies:**
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:240-241` (New `getLoadedBuilds()` creates `TreeMap` and calls `forEach` to populate it)
    *   `core/src/main/java/jenkins/model/lazy/AbstractLazyLoadRunMap.java:245` (Original `getLoadedBuilds()` returned `BuildReferenceMapAdapter`)

## Impact
*   **Incorrect Duration Estimation:** If `streamLoadedBuilds()` does not provide builds in reverse chronological order, `getEstimatedDurationCandidates()` will select arbitrary builds, leading to inaccurate or inconsistent duration estimations for queued jobs. This could cause jobs to wait longer than necessary or be scheduled prematurely.
*   **Semantic Change in "Loaded Builds":** Including unloadable builds in the stream could expose internal state that was previously hidden or filtered, potentially leading to unexpected behavior in consumers of `streamLoadedBuilds()` or the refactored `getLoadedBuilds()`.
*   **Limited Performance Improvement:** The performance benefit is restricted only to `getEstimatedDurationCandidates()`. Other parts of Jenkins that call `getLoadedBuilds()` will still incur the cost of a full map copy and eager object unwrapping, potentially even increasing memory pressure compared to the `BuildReferenceMapAdapter` which unwrapped lazily.
*   **Fragile Tests:** The `streamLoadedBuilds` test relies on an implementation detail (HashMap iteration order) that is not guaranteed, making the test prone to failure in different environments or JVM versions, and masking a critical bug in the sorting.

## Recommendation (Fix / Tests / Risks)
1.  **Fix Sorting in `streamLoadedBuilds()`:** Modify `streamLoadedBuilds()` to explicitly sort the stream by build number in reverse order. This can be done using `sorted(Comparator.comparing(this::getNumberOf).reversed())` after filtering for non-null builds.
2.  **Re-evaluate `isUnloadable()` Filter:** Clarify the intended behavior regarding unloadable builds. If `isUnloadable()` builds should be excluded, add `filter(r -> !((BuildReference<R>) core.get(getNumberOf(r))).isUnloadable())` to `streamLoadedBuilds()`. If the intent is to include them, document this change clearly.
3.  **Optimize `getLoadedBuilds()` or Document Limitations:** If `getLoadedBuilds()` is still intended to return a `SortedMap` of *all* loaded builds, consider if the eager unwrapping and full copy are acceptable. If not, `getLoadedBuilds()` might need to return a custom `SortedMap` implementation that wraps the stream and unwraps lazily, similar to the original `BuildReferenceMapAdapter`. Alternatively, clearly document that `getLoadedBuilds()` is still an expensive operation and `streamLoadedBuilds()` should be preferred for partial consumption.
4.  **Improve Test Coverage:**
    *   Add a test for `streamLoadedBuilds()` that explicitly verifies the sorting behavior using a `Comparator` or by asserting the order of builds added in a non-sequential manner (e.g., 1, 5, 3).
    *   Add a test for `getLoadedBuilds()` to ensure its behavior (especially filtering and sorting) remains consistent with the original implementation, or reflects the intended new behavior.
    *   Add a test for `getEstimatedDurationCandidates()` to ensure it correctly identifies candidates after the change, especially with various build results and orders.
5.  **Update `@since` Tag:** Replace `@since TODO` with the actual Jenkins version.

## Traceability
Not specified