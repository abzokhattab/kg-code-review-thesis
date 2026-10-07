```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the `OldDataMonitor` to stop saving `Run` objects, aiming to reduce memory pressure by preventing unnecessary loading of completed `WorkflowRun` objects.

## Problem
1. The removal of `RunSaveableReference` and related logic might lead to incomplete cleanup of old data references.
2. The change in `OldDataMonitor`'s data structure from `SaveableReference` to `Saveable` could introduce issues with object identity and persistence.
3. The test coverage for scenarios involving `Run` objects and their lifecycle management appears insufficient.

## Evidence
- **core/src/main/java/hudson/diagnosis/OldDataMonitor.java:75-109**: The transition from `SaveableReference` to direct `Saveable` objects in the `data` map.
- **core/src/main/java/hudson/diagnosis/OldDataMonitor.java:322-390**: Removal of `RunSaveableReference` logic, which previously handled `Run` object references.
- **test/src/test/java/hudson/diagnosis/OldDataMonitorTest.java:57-113**: Tests related to memory management and `Run` object handling are either disabled or removed, indicating potential gaps in test coverage.

## Impact
- The direct use of `Saveable` objects in the `data` map could lead to increased memory usage if `Run` objects are not properly garbage collected.
- Without `RunSaveableReference`, there might be a risk of not correctly identifying and cleaning up old data, leading to potential memory leaks.
- Insufficient testing of `Run` lifecycle changes could result in undetected bugs, especially in scenarios involving build discarding and data persistence.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of `RunSaveableReference` or similar mechanisms to ensure proper cleanup of `Run` objects.
2. Enhance test coverage to include scenarios that specifically test the lifecycle and memory management of `Run` objects.
3. Conduct performance testing to assess the impact of these changes on memory usage and system stability.

## Traceability
Not specified
```