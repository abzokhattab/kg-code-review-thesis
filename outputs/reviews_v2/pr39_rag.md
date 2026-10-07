```
# Review Note — Evidence-Anchored

**Scope:** This PR extends the `TxnOffsetCommit` and `WriteTxnMarkers` integration tests to cover version 6 (KIP-1319) and introduces new error cases.

## Problem
1. Lack of validation for `topicId` in older versions (v0-v5) where it should not be used.
2. Potential inconsistency in handling `UNKNOWN_TOPIC_ID` error for versions below v6.
3. Insufficient test coverage for edge cases related to `topicId` handling in mixed-version environments.

## Evidence
- `GroupCoordinatorBaseRequestTest.scala:line 288`: `topicId` is set for all versions, but older versions should not use it.
- `TxnOffsetCommitRequestTest.scala:line 138`: `UNKNOWN_TOPIC_ID` is only checked for v6+, but there is no fallback handling for older versions.
- `TxnOffsetCommitRequestTest.scala:line 100`: The loop iterates over all versions, but `topicId` is passed without conditional checks for version compatibility.

## Impact
- Using `topicId` in versions that do not support it could lead to unexpected behavior or errors.
- Inconsistent error handling might cause confusion or incorrect error reporting in logs, complicating debugging.
- Lack of comprehensive tests for mixed-version scenarios could lead to undetected bugs in production environments.

## Recommendation (Fix / Tests / Risks)
1. Add conditional logic to ensure `topicId` is only used in v6+ requests.
2. Implement fallback error handling for `UNKNOWN_TOPIC_ID` in versions below v6.
3. Expand test cases to include scenarios where `topicId` is incorrectly used in older versions to ensure robust error handling.

## Traceability
Not specified
```