```
# Review Note — Evidence-Anchored

**Scope:** This PR wires the topic ID through `OffsetMetadataManager` and updates the offset record and `TxnOffsetCommit` response.

## Problem
1. Removal of metadata image handling may lead to issues if topic ID resolution is required elsewhere.
2. The test coverage for scenarios where topic ID resolution fails seems to be reduced.

## Evidence
- `group-coordinator/src/main/java/org/apache/kafka/coordinator/group/GroupCoordinatorShard.java:1081-1106`: Removal of `offsetMetadataManager.onMetadataUpdate`.
- `group-coordinator/src/main/java/org/apache/kafka/coordinator/group/OffsetMetadataManager.java:39-432`: Removal of `metadataImage` and related methods.
- `group-coordinator/src/test/java/org/apache/kafka/coordinator/group/OffsetMetadataManagerTest.java:1641-1899`: Removal of test `testConsumerGroupTransactionalOffsetCommitWithUnresolvedTopicId`.

## Impact
- The removal of metadata image handling could lead to issues if other parts of the system still rely on this for topic ID resolution.
- Reduced test coverage for unresolved topic ID scenarios increases the risk of undetected bugs in these cases.

## Recommendation (Fix / Tests / Risks)
1. Ensure that all parts of the system that previously relied on metadata image for topic ID resolution are updated to use the new approach.
2. Reintroduce tests for scenarios where topic ID resolution fails to ensure robustness.
3. Consider adding integration tests to verify the end-to-end behavior of the system with the new changes.

## Traceability
Not specified
```