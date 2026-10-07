```
# Review Note — Evidence-Anchored

**Scope:** This PR wires the topic ID through `OffsetMetadataManager` and updates the offset record and `TxnOffsetCommit` response.

## Problem
1. Removal of `metadataImage` handling without clear replacement or validation.
2. Potential lack of validation for topic existence when topic ID is directly used.
3. Insufficient test coverage for scenarios where topic ID resolution fails.

## Evidence
- `GroupCoordinatorShard.java:1081-1106`: Removal of `offsetMetadataManager.onMetadataUpdate` calls.
- `OffsetMetadataManager.java:39-440`: Removal of `metadataImage` and related methods without replacement.
- `OffsetMetadataManagerTest.java:1641-1899`: Removal of test `testConsumerGroupTransactionalOffsetCommitWithUnresolvedTopicId`.

## Impact
- The removal of `metadataImage` handling could lead to scenarios where topic existence is not validated, potentially causing runtime errors if a topic ID is incorrect or outdated.
- Without proper validation, there is a risk of committing offsets to non-existent topics, leading to data inconsistency.
- The lack of tests for unresolved topic IDs might result in undetected bugs in production.

## Recommendation (Fix / Tests / Risks)
1. Reintroduce a mechanism to validate topic existence when using topic IDs, possibly by checking against a metadata store.
2. Add tests to cover scenarios where topic ID resolution fails, ensuring that appropriate exceptions are thrown.
3. Review the integration with other components to ensure that the removal of `metadataImage` does not introduce inconsistencies.

## Traceability
Not specified
```