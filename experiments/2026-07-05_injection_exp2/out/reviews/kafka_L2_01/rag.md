```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `start` method in `DefaultStateUpdater` by changing the condition for throwing an `IllegalStateException`.

## Problem
1. The logic change from `stateUpdaterThread == null` to `stateUpdaterThread != null` may introduce incorrect behavior.
2. The condition now contradicts the intended logic of ensuring the state updater starts only when the thread is not already running.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java:775`: The condition change from `stateUpdaterThread == null` to `stateUpdaterThread != null`.

## Impact
- The change could lead to the `IllegalStateException` being thrown incorrectly, preventing the `DefaultStateUpdater` from starting under valid conditions.
- This could result in application downtime or failure to process streams as expected, especially if the state updater is a critical component in the processing pipeline.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the logic to ensure the condition accurately reflects the intended behavior of starting the updater only when `stateUpdaterThread` is `null`.
2. Add unit tests to cover scenarios where the `stateUpdaterThread` is both `null` and non-`null` to ensure the exception is thrown correctly.
3. Verify the change against existing integration tests to ensure no unintended side effects are introduced.

## Traceability
Not specified
```