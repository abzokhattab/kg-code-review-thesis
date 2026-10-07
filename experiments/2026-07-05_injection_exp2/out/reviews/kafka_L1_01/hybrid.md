```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors condition handling in the `DefaultStateUpdater` class to simplify deadline checks.

## Problem
1. The change from `now <= deadline` to `now < deadline` may introduce a logic error if `now` equals `deadline` at the start of the loop.
2. The refactor does not include any updates to related test cases to ensure the new condition is correctly validated.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java:873`: The condition was changed from `now <= deadline` to `now < deadline`.

## Impact
- The change in the loop condition could lead to premature exits from the loop if `now` is exactly equal to `deadline`, potentially causing tasks that should be processed to be skipped.
- Without corresponding test updates, there's a risk that this change could introduce undetected bugs, especially in edge cases where timing is critical.

## Recommendation (Fix / Tests / Risks)
1. Review the logic to ensure that changing the condition to `now < deadline` is indeed the intended behavior and does not skip necessary iterations.
2. Add or update unit tests to cover scenarios where `now` is exactly equal to `deadline` to ensure that the loop behaves as expected.
3. Consider potential impacts on dependent components like `StreamThread` and verify integration tests cover these changes.

## Traceability
Not specified
```