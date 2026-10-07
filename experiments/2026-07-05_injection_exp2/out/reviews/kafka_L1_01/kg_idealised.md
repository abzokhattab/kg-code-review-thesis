```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the condition handling logic in the `DefaultStateUpdater` class of the Kafka Streams library.

## Problem
1. The change from `now <= deadline` to `now < deadline` in the while loop condition may alter the intended behavior of the loop.
2. There is no evidence of additional test coverage to verify the behavior change in edge cases where `now` equals `deadline`.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java:873`: The condition in the while loop was changed from `now <= deadline` to `now < deadline`.

## Impact
- The change could lead to premature exit from the loop when `now` is exactly equal to `deadline`, potentially causing tasks to be skipped or not processed as expected.
- This could introduce subtle timing-related bugs, especially in scenarios where precise timing is critical for task processing.

## Recommendation (Fix / Tests / Risks)
1. Review the logic to ensure that the change from `<=` to `<` is intentional and aligns with the desired behavior.
2. Add or update unit tests to cover scenarios where `now` is exactly equal to `deadline` to ensure the loop behaves as expected in these edge cases.
3. Consider adding comments or documentation to clarify the reasoning behind this condition change for future maintainers.

## Traceability
- Code Owner: Kafka Streams Team
```