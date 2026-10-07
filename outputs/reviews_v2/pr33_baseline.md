```
# Review Note — Evidence-Anchored

**Scope:** This PR stops saving `Run`s in `OldDataMonitor` to address memory pressure issues in Jenkins.

## Problem
1. The removal of `RunSaveableReference` and related logic might lead to incomplete cleanup of old data references.
2. The change in `OldDataMonitor` to not track `Run`s could potentially overlook scenarios where `Run` data might still be relevant for monitoring or debugging purposes.

## Evidence
- `OldDataMonitor.java:388-460`: Removal of `RunSaveableReference` and related logic without clear replacement for handling `Run` references.
- `OldDataMonitor.java:212-215`: Conditional logic to skip `Run` objects in `report` methods, which might lead to missing important data.

## Impact
- The removal of `Run` tracking could lead to scenarios where old data issues related to `Run`s are not reported, potentially missing critical debugging information.
- Without proper handling of `Run` references, there might be a risk of not fully cleaning up old data, leading to potential memory leaks or incomplete data monitoring.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of tracking `Run` objects in `OldDataMonitor` and ensure that any critical data is not overlooked.
2. Consider implementing alternative mechanisms to handle `Run` references if they are deemed necessary for certain monitoring scenarios.
3. Add comprehensive tests to ensure that the removal of `Run` tracking does not lead to missed data issues or memory leaks.

## Traceability
Not specified
```