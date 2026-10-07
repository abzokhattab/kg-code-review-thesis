```
# Review Note — Evidence-Anchored

**Scope:** This PR wires the topic ID through `OffsetMetadataManager` and removes the previous metadata image lookup.

## Problem
1. Removal of metadata image handling without clear replacement or validation.
2. Potential lack of test coverage for scenarios where topic IDs are unresolved or incorrect.

## Evidence
- `GroupCoordinatorShard.java:1081-1106`: Removal of `offsetMetadataManager.onMetadataUpdate` calls.
- `OffsetMetadataManager.java:39-1308`: Removal of `CoordinatorMetadataImage` and related methods.
- `OffsetMetadataManagerTest.java:1273-1304`: Removal of tests verifying `onMetadataUpdate` calls.
- `OffsetMetadataManagerTest.java:1641-1899`: Changes in test methods to use `topicId` directly without fallback checks.

## Impact
- **Technical Impact:** The removal of metadata image handling could lead to issues if topic IDs are not correctly resolved or if there are discrepancies between the topic ID and the actual metadata. This could result in incorrect offset commits or failures in transactional operations.
- **Risk:** Without proper validation or fallback mechanisms, there is a risk of runtime exceptions or incorrect data handling, especially in edge cases where topic metadata might not be fully synchronized.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Reintroduce a mechanism to validate topic IDs against metadata to ensure consistency and correctness.
2. **Tests:** Add comprehensive test cases to cover scenarios where topic IDs might be unresolved or incorrect, ensuring that the system handles these gracefully.
3. **Risks:** Evaluate the risk of removing metadata image handling and consider implementing a fallback or logging mechanism to capture potential discrepancies.

## Traceability
Not specified
```