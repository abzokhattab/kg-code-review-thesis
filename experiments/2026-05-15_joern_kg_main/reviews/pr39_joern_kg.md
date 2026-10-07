# Review Note — Evidence-Anchored

**Scope:** This PR extends `TxnOffsetCommit` and `WriteTxnMarkers` integration tests to cover v6 (KIP-1319) and threads the topic ID through the `commitTxnOffset` helper.

## Problem
1.  **Incomplete Response Structure Verification:** The `commitTxnOffset` helper now conditionally sets `topicId` and `name` in the `TxnOffsetCommitResponseData` based on the request version. The existing tests primarily verify error codes, but lack explicit assertions for the exact `topicId` and `name` fields in *successful* responses across all relevant API versions (especially the conditional logic for v6+ vs. pre-v6). This could lead to subtle regressions if the response structure deviates from client expectations.
2.  **Untested Topic ID Handling for Pre-v6 Requests:** The `commitTxnOffset` helper now always receives a `topicId` parameter, even for versions < 6 where `topicId` is not part of the wire protocol. While the helper correctly sets `Uuid.ZERO_UUID` in the response for these versions, there are no explicit tests verifying that passing a *non-zero* `topicId` in the *request* for pre-v6 versions doesn't cause unexpected server-side behavior or errors, even if the wire format doesn't include it.
3.  **Ambiguity of `name` field for v6+ responses:** For v6+, the `name` field in the `TxnOffsetCommitResponseData` is explicitly set to an empty string (`""`). While this might be the intended behavior as topic names become deprecated in favor of topic IDs, it's a specific choice that should be explicitly verified against the protocol specification. Without clear tests, there's a risk of inconsistency if clients expect `null` or omission for deprecated fields.

## Evidence
*   `core/src/test/scala/unit/kafka/server/GroupCoordinatorBaseRequestTest.scala:286-287`: Conditional logic for `topicId` and `name` in `TxnOffsetCommitResponseData`.
    ```scala
              .setTopicId(if (version >= 6) topicId else Uuid.ZERO_UUID)
              .setName(if (version < 6) topic else "")
    ```
*   `core/src/test/scala/unit/kafka/server/TxnOffsetCommitRequestTest.scala:195`: Call to `commitTxnOffset` with `topicId` parameter.
    ```scala
          topicId = topicId,
    ```
*   `core/src/test/scala/unit/kafka/server/WriteTxnMarkersRequestTest.scala:124`: Call to `commitTxnOffset` with `topicId` parameter.
    ```scala
          topicId = topicId,
    ```
*   `clients/src/test/java/org/apache/kafka/common/requests/TxnOffsetCommitRequestTest.java`: This client-side test implicitly relies on the wire format and response structure, which could be affected by the server-side changes.

## Impact
*   **Integration Risk:** Clients (especially older ones) might encounter unexpected behavior or parsing errors if the `TxnOffsetCommitResponseData` structure for successful responses (specifically `topicId` and `name` fields) is not precisely as expected across all API versions.
*   **Test Gaps:** Lack of explicit tests for `topicId` handling in pre-v6 requests could hide subtle bugs where the server might incorrectly process or validate the `topicId` even if it's not part of the wire protocol for older versions.
*   **Correctness Risk:** The specific choice of an empty string for the `name` field in v6+ responses, if not explicitly defined and tested, could lead to inconsistencies or misinterpretations by clients expecting `null` or omission for deprecated fields.

## Recommendation (Fix / Tests / Risks)
1.  **Enhance Response Assertions:** In `TxnOffsetCommitRequestTest.scala`, modify the `assertTxnCommitResponse` function (or add a new assertion helper) to explicitly verify the `topicId` and `name` fields in the `TxnOffsetCommitResponseData` for *successful* responses.
    *   For `version >= 6`, assert that `topicId` matches the requested `topicId` and `name` is an empty string.
    *   For `version < 6`, assert that `topicId` is `Uuid.ZERO_UUID` and `name` matches the requested `topic`.
    *   Apply similar assertions in `WriteTxnMarkersRequestTest.scala` if applicable.
2.  **Add Negative Test for Pre-v6 Topic ID:** In `TxnOffsetCommitRequestTest.scala`, add a new test case within `testTxnOffsetCommit` that calls `verifyTxnCommitAndFetch` for a `version < 6` while passing a *random, non-zero* `topicId`. Assert that the request still succeeds (if it should) and the response `topicId` is `Uuid.ZERO_UUID`, or that an appropriate error is returned if the server unexpectedly validates the `topicId` for older versions.
3.  **Clarify and Test V6+ `name` Field:** Confirm with the KIP-1319 specification if an empty string is the *exact* expected value for the `name` field in `TxnOffsetCommitResponseData` for v6+. If so, ensure Recommendation 1 explicitly covers this assertion. If `null` or omission is preferred, adjust the `GroupCoordinatorBaseRequestTest.scala:287` logic and corresponding tests.

## Traceability
Sean Quah