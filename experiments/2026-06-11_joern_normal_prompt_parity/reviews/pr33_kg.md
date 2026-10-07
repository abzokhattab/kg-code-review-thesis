```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the `OldDataMonitor` to stop saving `Run` objects, aiming to reduce memory pressure by preventing unnecessary loading of completed `WorkflowRun` objects.

## Problem
1. **Potential Memory Leak**: The removal of `RunSaveableReference` and related logic might lead to unintended retention of `Run` objects in memory.
2. **Incomplete Test Coverage**: The changes in `OldDataMonitor` might not be fully covered by existing tests, especially concerning the new behavior of not saving `Run` objects.
3. **Integration Risks**: The changes could affect other components that rely on `OldDataMonitor` for tracking `Run` objects, potentially leading to unexpected behavior.

## Evidence
- **core/src/main/java/hudson/diagnosis/OldDataMonitor.java:75-142**: Removal of `RunSaveableReference` and related logic that previously managed `Run` object references.
- **test/src/test/java/hudson/diagnosis/OldDataMonitorTest.java:40-113**: Tests related to memory management and `Run` object handling have been disabled or removed, indicating potential gaps in test coverage.

## Impact
- **Technical Impact**: The removal of `Run` tracking could lead to memory leaks if `Run` objects are not properly garbage collected. Additionally, other components relying on `OldDataMonitor` might experience unexpected behavior due to the absence of `Run` references.
- **Risks**: There is a risk of increased memory usage if `Run` objects are not managed correctly. Furthermore, the lack of comprehensive tests could result in undetected issues in production environments.

## Recommendation (Fix / Tests / Risks)
1. **Reintroduce Tests**: Ensure that tests cover the new behavior of `OldDataMonitor`, particularly focusing on memory management and the absence of `Run` references.
2. **Conduct Integration Testing**: Verify that other components interacting with `OldDataMonitor` function correctly without `Run` references.
3. **Monitor Memory Usage**: After deployment, closely monitor memory usage to detect any potential leaks early.

## Traceability
Not specified
```