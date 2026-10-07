```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `DefaultStateUpdater` by altering the condition for starting the state updater thread.

## Problem
1. The logic change in the `start` method might introduce a bug by reversing the intended check for `stateUpdaterThread`.
2. The change lacks accompanying test updates or additions to verify the new logic.

## Evidence
- **streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java:775**: The condition was changed from `stateUpdaterThread == null` to `stateUpdaterThread != null`.

## Impact
- The reversed condition could lead to the `start` method throwing an `IllegalStateException` under incorrect circumstances, potentially causing the state updater to fail to start when it should.
- This could disrupt the processing of streams, leading to data processing errors or application crashes.

## Recommendation (Fix / Tests / Risks)
1. Verify the intended logic for starting the `stateUpdaterThread` and ensure the condition aligns with the design requirements.
2. Add or update unit tests to cover scenarios where the `stateUpdaterThread` should or should not be started, ensuring the logic behaves as expected.
3. Review integration tests that involve `DefaultStateUpdater` to confirm they account for this logic change.

## Traceability
- Not specified
```