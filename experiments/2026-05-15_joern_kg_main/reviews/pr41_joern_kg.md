# Review Note — Evidence-Anchored

**Scope:** This PR introduces a new `ShareGroupDLQMetadataCacheHelper` interface and its implementation, `ShareCoordinatorMetadataCacheHelperImpl`, to provide DLQ-related metadata. It also updates `ShareGroupDLQStateManager` to use this helper and adds plumbing in `BrokerServer` and `GroupConfigManager` to expose DLQ configurations.

## Problem
1.  **DLQ Produce Requests Are Never Sent:** The `ShareGroupDLQStateManager`'s `SendThread` logic prevents actual produce requests from being generated and sent if the DLQ topic already exists. This means the core functionality of dead-letter queuing records will not work.
2.  **Incomplete DLQ Topic Creation Logic:** The `CreateTopicsRequest` generated for auto-creating DLQ topics is empty, lacking the necessary topic name, partitions, and replication factor. Additionally, the request is sent to a random broker instead of the controller, which is less robust.
3.  **Untested `ShareGroupDLQStateManager` Functionality:** The `ShareGroupDLQStateManager` class, which orchestrates DLQ operations including validation, topic creation, and record production, lacks dedicated unit or integration tests, leaving critical logic unverified.

## Evidence
*   **Problem 1 (Produce Requests Not Sent):**
    *   `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:149` (`SendThread.generateRequests()`): The method returns `List.of()` if `!handler.dlqTopicExists()` is false (i.e., the DLQ topic exists), preventing any `ProduceRequest` from being generated.
    *   `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:132` (`ProduceRequestHandler.onComplete()`): This method is empty, meaning the `CompletableFuture` returned by `dlq()` is never completed based on the actual produce request's success or failure.
    *   `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:129` (`ProduceRequestHandler.result()`): Returns `CompletableFuture.completedFuture(null)`, which is not the future returned by `dlq()`, further indicating a disconnect in future completion.
*   **Problem 2 (Incomplete Topic Creation):**
    *   `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:108` (`ShareGroupDLQStateManagerHandler.createTopicBuilder()`): Initializes `CreateTopicsRequest` with an empty `CreateTopicsRequestData`, which will result in an invalid or no-op topic creation request.
    *   `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:155` (`SendThread.randomNode()`): Selects a random `Node` from `cacheHelper.getClusterNodes()` to send the `CreateTopicsRequest`, rather than targeting the cluster controller.
*   **Problem 3 (Untested State Manager):**
    *   No new test file `server-common/src/test/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManagerTest.java` is present in the diff or related tests.
    *   Existing tests like `core/src/test/java/kafka/server/share/ShareCoordinatorMetadataCacheHelperImplTest.java` and `group-coordinator/src/test/java/org/apache/kafka/coordinator/group/GroupConfigManagerTest.java` cover only the helper and config manager, not the `ShareGroupDLQStateManager`'s operational logic.

## Impact
*   **Problem 1:** The primary function of the DLQ manager—to dead-letter records—will silently fail or hang indefinitely for callers of `ShareGroupDLQStateManager.dlq(ShareGroupDLQRecordParameter param)` if the DLQ topic already exists. This renders the DLQ feature non-functional in its current state.
*   **Problem 2:** Automatic creation of DLQ topics will fail, preventing DLQ functionality for share groups that rely on this feature. This will lead to `CreateTopicsRequest` errors and potentially `Errors.BROKER_NOT_AVAILABLE` exceptions being completed exceptionally to the `dlq()` future, even if a broker is available, due to the request being malformed or misdirected.
*   **Problem 3:** The complex state management, request generation, and completion handling within `ShareGroupDLQStateManager` are entirely unverified. This introduces significant risk of runtime errors, unexpected behavior, and regressions, making it difficult to ensure the correctness and reliability of the DLQ feature.

## Recommendation (Fix / Tests / Risks)
1.  **Fix `SendThread.generateRequests()` and `ProduceRequestHandler.onComplete()`:**
    *   Modify `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:149` (`SendThread.generateRequests()`) to correctly generate and enqueue a `ProduceRequest` when `handler.dlqTopicExists()` is true.
    *   Implement `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:132` (`ProduceRequestHandler.onComplete(ClientResponse response)`) to complete the `CompletableFuture<Void>` (passed in the constructor) based on the `response.responseBody().error()` or success.
    *   Ensure `ProduceRequestHandler.result()` returns the actual `CompletableFuture<Void>` that `dlq()` returns.
2.  **Complete DLQ Topic Creation Logic:**
    *   In `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:108` (`ShareGroupDLQStateManagerHandler.createTopicBuilder()`), populate the `CreateTopicsRequestData` with the DLQ topic name (from `param.groupId()` and `cacheHelper.shareGroupDlqTopic()`), desired partitions, and replication factor. These values should likely come from broker configurations or KIP-1191 related defaults.
    *   Modify `server-common/src/main/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManager.java:155` (`SendThread.randomNode()`) to instead retrieve and target the cluster controller node for `CreateTopicsRequest` for improved reliability.
3.  **Add Comprehensive Tests for `ShareGroupDLQStateManager`:**
    *   Create a new test file, e.g., `server-common/src/test/java/org/apache/kafka/server/share/dlq/ShareGroupDLQStateManagerTest.java`.
    *   Add unit tests to verify the behavior of `ShareGroupDLQStateManager.dlq()` under various scenarios, including:
        *   Successful record production when the DLQ topic exists.
        *   Successful auto-creation of a DLQ topic followed by record production.
        *   Error handling for `validateDlqTopic()` failures.
        *   Error handling for `CreateTopicsRequest` failures (e.g., controller not available, invalid topic config).
        *   Error handling for `ProduceRequest` failures (e.g., topic not found, network errors).
4.  **Review `isDlqEnabledOnTopic` Type Handling:**
    *   In `core/src/main/java/kafka/server/share/ShareCoordinatorMetadataCacheHelperImpl.java:69` (`isDlqEnabledOnTopic`), consider explicitly parsing the `Object isEnabled` to a `String` and then to a `Boolean` (e.g., `Boolean.parseBoolean(isEnabled.toString())`) to handle cases where topic configurations are stored as strings, which is common in Kafka.

## Traceability
Reviewers: Apoorv Mittal <apoorvmittal10@gmail.com>, Andrew Schofield <aschofield@confluent.io>