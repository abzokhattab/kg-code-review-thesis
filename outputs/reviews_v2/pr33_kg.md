```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the `OldDataMonitor` to stop saving `Run` objects, aiming to reduce memory pressure by preventing unnecessary loading of completed `WorkflowRun` objects.

## Problem
1. **Potential Memory Leak**: The removal of `SaveableReference` and its associated logic might lead to unintended retention of objects in memory.
2. **Incomplete Test Coverage**: The changes in `OldDataMonitor` might not be fully covered by existing tests, especially concerning the new behavior of not saving `Run` objects.
3. **Integration Risks**: The changes could affect other components that rely on `OldDataMonitor` for tracking `Run` objects, potentially leading to unexpected behavior.

## Evidence
- **core/src/main/java/hudson/diagnosis/OldDataMonitor.java:75-109**: The `SaveableReference` mechanism is removed, which previously helped manage memory by not holding strong references to `Run` objects.
- **test/src/test/java/hudson/diagnosis/OldDataMonitorTest.java:40-113**: Tests related to memory management and `Run` object handling are disabled or removed, indicating potential gaps in test coverage.
- **test/src/test/java/hudson/model/ComputerTest.java:256-259**: The `doDiscard` method is modified, but without additional tests to verify its new behavior.

## Impact
- **Technical Impact**: The removal of `SaveableReference` could lead to increased memory usage if `Run` objects are not properly garbage collected. This might exacerbate memory pressure issues rather than alleviate them.
- **Risk of Regression**: Other components that depend on `OldDataMonitor` might experience regressions if they expect `Run` objects to be tracked and managed as before.

## Recommendation (Fix / Tests / Risks)
1. **Reintroduce Memory Management Tests**: Ensure that tests are in place to verify that `Run` objects are not retained in memory unnecessarily.
2. **Expand Test Coverage**: Add tests to cover the new behavior of `OldDataMonitor`, particularly focusing on scenarios where `Run` objects are no longer saved.
3. **Review Integration Points**: Conduct a thorough review of components that interact with `OldDataMonitor` to ensure they are not adversely affected by these changes.

## Traceability
Not specified
```