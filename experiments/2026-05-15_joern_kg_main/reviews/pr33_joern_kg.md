# Review Note — Evidence-Anchored

**Scope:** This PR modifies `OldDataMonitor` to stop tracking `Run` objects, aiming to reduce memory consumption by preventing `WorkflowRun` objects from being held in memory after completion.

## Problem
1.  **Memory Leak Risk for Non-Run Saveables:** The core change from `ConcurrentMap<SaveableReference, VersionRange>` to `ConcurrentMap<Saveable, VersionRange>` means that `Saveable` objects (other than `Run`s, which are now filtered) will be held by strong references in the `OldDataMonitor.data` map. The original `SaveableReference` interface, with its `SimpleSaveableReference` implementation, was designed to allow garbage collection of the referenced `Saveable` if no other strong references existed, preventing memory leaks for *all* `Saveable` types. This change reintroduces a memory leak risk for `Saveable` objects like `Item`s, `Job`s, `View`s, `Computer`s, `ToolInstallation`s, etc., if they are reported and not explicitly discarded or saved.
2.  **Missing Test Coverage for Run Filtering:** The PR removes existing tests (`memory()`, `unlocatableRun()`) that specifically verified the behavior of `Run` objects with `OldDataMonitor`. While the intent is to *stop* reporting `Run`s, there is no new test case that explicitly verifies that `Run` objects are *not* reported and do *not* appear in the `OldDataMonitor.getData()` map after the changes. This leaves a critical aspect of the PR's goal untested.
3.  **Loss of Job-Specific Run Cleanup Logic:** The `remove` method previously contained logic to iterate through a `Job`'s builds and remove their corresponding entries from `odm.data` when the `Job` itself was deleted. This specific cleanup logic has been removed. Although `Run` objects are now explicitly filtered from being reported, this removal means that if a `Run` *were* to somehow be reported (e.g., through an unforeseen code path or a future regression), there would be no mechanism to automatically clean up its entry when its parent `Job` is deleted.

## Evidence
*   **Memory Leak Risk:**
    *   `core/src/main/java/hudson/diagnosis/OldDataMonitor.java:35`: `private ConcurrentMap<SaveableReference, VersionRange> data = new ConcurrentHashMap<>();` changed to `private ConcurrentMap<Saveable, VersionRange> data = new ConcurrentHashMap<>();`
    *   `core/src/main/java/hudson/diagnosis/OldDataMonitor.java:348-388`: The `SaveableReference` interface and its implementations (`SimpleSaveableReference`, `RunSaveableReference`) have been removed.
    *   `core/src/main/java/hudson/diagnosis/OldDataMonitor.java:366`: `Saveable s = entry.getKey().get();` changed to `var s = entry.getKey();` in `saveAndRemoveEntries`, directly accessing the `Saveable` object.
    *   `core/src/main/java/hudson/util/RobustReflectionConverter.java`, `core/src/main/java/hudson/util/XStream2.java`, `core/src/main/java/hudson/util/RobustCollectionConverter.java`, `core/src/main/java/hudson/util/RobustMapConverter.java`: These files call `hudson/diagnosis/OldDataMonitor.java::report(Saveable obj, Collection<Throwable> errors)` and `hudson/diagnosis/OldDataMonitor.java::report(Saveable obj, String version)` for various `Saveable` types, which will now be strongly referenced.
*   **Missing Test Coverage:**
    *   `test/src/test/java/hudson/diagnosis/OldDataMonitorTest.java:40-50`: The `memory()` test, which specifically asserted `WeakReference` behavior for `FreeStyleBuild` (a `Run` subclass), has been removed.
    *   `test/src/test/java/hudson/diagnosis/OldDataMonitorTest.java:113-123`: The `unlocatableRun()` test, which tested `Run` deletion and reporting, has been removed.
*   **Loss of Job-Specific Run Cleanup:**
    *   `core/src/main/java/hudson/diagnosis/OldDataMonitor.java:115-123`: The `remove` method previously contained `if (isDelete && obj instanceof Job<?, ?>) { for (Run r : ((Job<?, ?>) obj).getBuilds()) { odm.data.remove(referTo(r)); } }` which has been removed.

## Impact
1.  **Memory Leak for Non-Run Saveables:** Any `Saveable` object (e.g., `hudson.model.Item`, `hudson.model.Job`, `hudson.model.View`, `hudson.model.Computer`, `hudson.tools.ToolInstallation`, `hudson.model.CauseAction`, `hudson.model.ParametersAction`) that encounters a deserialization issue and is reported to `OldDataMonitor` will now be held strongly in memory. This prevents these objects from being garbage collected, potentially leading to increased heap usage and memory pressure over time, similar to the problem this PR aims to solve for `Run`s.
2.  **Untested Critical Behavior:** Without explicit tests, there's no automated verification that `Run` objects are correctly ignored by `OldDataMonitor`. A future change or regression could inadvertently cause `Run` objects to be reported again, reintroducing the memory leak problem without immediate detection.
3.  **Incomplete Cleanup:** While the primary goal is to prevent `Run`s from being reported, the removal of the `Job`-specific cleanup means that if a `Run` *were* to be reported, its entry would persist even after its parent `Job` is deleted, leading to stale data in the monitor and a potential memory leak for that specific `Run` object.

## Recommendation (Fix / Tests / Risks)
1.  **Reintroduce Weak References for Non-Run Saveables:**
    *   Revert the change to `ConcurrentMap<Saveable, VersionRange>` and instead use `ConcurrentMap<SaveableReference, VersionRange>` as before.
    *   Modify the `referTo(Saveable s)` method to return a `SimpleSaveableReference` (which should use a `WeakReference` internally) for all `Saveable` types *except* `Run`s. For `Run`s, it should return `null` or a special "ignored" reference, or the `report` methods should continue to filter them out *before* calling `referTo`.
    *   Ensure `SimpleSaveableReference` correctly wraps `Saveable` objects in a `WeakReference` to allow garbage collection.
2.  **Add New Test for Run Filtering:**
    *   Add a new test case to `test/src/test/java/hudson/diagnosis/OldDataMonitorTest.java` that creates a `FreeStyleBuild` (a `Run`), reports it to `OldDataMonitor` (e.g., by simulating a deserialization error), and then asserts that `OldDataMonitor.get().getData().keySet()` *does not* contain the `Run` object. This explicitly verifies the `if (obj instanceof Run<?, ?>) { return; }` logic in `hudson/diagnosis/OldDataMonitor.java::report`.
3.  **Re-evaluate Job-Specific Run Cleanup:**
    *   Given the explicit filtering of `Run`s in `report` methods, the removal of the `Job`-specific cleanup logic might be acceptable. However, it's a behavioral change that should be explicitly documented or confirmed as intended. If the `WeakReference` approach is reintroduced (as per recommendation 1), then the `Job`-specific cleanup logic should also be reconsidered for reintroduction to ensure comprehensive cleanup.

## Traceability
Not specified