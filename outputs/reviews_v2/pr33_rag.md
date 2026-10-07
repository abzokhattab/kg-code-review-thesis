```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the `OldDataMonitor` to stop saving `Run` objects, aiming to reduce memory pressure by preventing unnecessary loading of completed `WorkflowRun` objects.

## Problem
1. The removal of `RunSaveableReference` and related logic might lead to incomplete cleanup of old data references.
2. The change in `OldDataMonitor`'s data structure from `SaveableReference` to `Saveable` could introduce issues with object identity and equality checks.
3. The test coverage for scenarios involving `Run` objects and their lifecycle in the context of `OldDataMonitor` appears insufficient.

## Evidence
- **OldDataMonitor.java:292-431**: Removal of `RunSaveableReference` logic without a clear alternative for handling `Run` objects.
- **OldDataMonitor.java:75-113**: Changes in how `Saveable` objects are stored and retrieved, potentially affecting object identity checks.
- **OldDataMonitorTest.java:68-141**: Tests related to memory management and `Run` object handling are either disabled or removed, reducing test coverage.

## Impact
- The removal of `RunSaveableReference` could lead to incomplete cleanup of old data, potentially leaving orphaned references in memory.
- Changes in data handling could lead to incorrect behavior if `Saveable` objects are not correctly identified or compared, possibly causing data inconsistencies.
- Insufficient test coverage increases the risk of undetected regressions, especially in scenarios involving `Run` objects.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of `RunSaveableReference` or provide a clear alternative to ensure proper cleanup of `Run` references.
2. Ensure that the new data handling logic correctly manages object identity and equality to prevent data inconsistencies.
3. Enhance test coverage to include scenarios involving `Run` objects, ensuring that all lifecycle events are adequately tested.

## Traceability
Not specified
```