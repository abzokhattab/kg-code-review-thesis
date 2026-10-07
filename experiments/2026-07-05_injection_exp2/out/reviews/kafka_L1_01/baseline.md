```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the condition handling logic in the `DefaultStateUpdater` class to simplify deadline checks.

## Problem
1. Potential off-by-one error in deadline handling.
2. Lack of clarity on the impact of changing the condition from `<=` to `<`.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java:874`: The condition was changed from `now <= deadline` to `now < deadline`.

## Impact
- The change from `<=` to `<` could lead to the loop terminating one iteration earlier than previously, potentially causing tasks to be skipped if they are expected to be processed exactly at the deadline time. This could result in incomplete processing of tasks if the deadline is critical for task execution.

## Recommendation (Fix / Tests / Risks)
1. Review the logic to ensure that the change from `<=` to `<` does not unintentionally skip necessary processing at the deadline.
2. Add a test case to verify behavior at the exact deadline time to ensure tasks are not skipped.
3. Consider documenting the rationale for this change to clarify the intended behavior and prevent future misunderstandings.

## Traceability
Not specified
```