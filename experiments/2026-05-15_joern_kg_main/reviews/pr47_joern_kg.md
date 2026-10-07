# Review Note — Evidence-Anchored

**Scope:** This PR aims to ensure that the temporary offline cause of Jenkins agents is retained when configuration is reapplied (e.g., via Configuration as Code) or after a Jenkins restart.

## Problem
1.  **Incomplete Fix for Jenkins Restarts:** The PR's core logic copies the `temporaryOfflineCause` from an `oldNode` to a `newNode` during `Jenkins.get().setNodes()`. This correctly addresses the scenario where configuration is reapplied *without* a full Jenkins restart, as the `oldNode` would still be the live, in-memory object retaining its offline cause. However, the PR description explicitly mentions "restarting Jenkins" as a scenario where the cause is lost. If the `OfflineCause` itself is not persisted to disk (as implied by "offline cause is not maintained in the yaml"), then after a full Jenkins restart, the `oldNode` loaded from disk would *not* have the `temporaryOfflineCause`. In this case, copying a `null` cause would not achieve the stated goal of retaining it across restarts.
2.  **Insufficient Test Coverage for CLI Interactions:** Jenkins agents can be taken offline via CLI commands, which would set the `temporaryOfflineCause`. The current test `NodesTest.java::setNodesRetainsOfflineCause` only covers the `setNodes` method directly. There is no test verifying that an offline cause set via CLI is correctly retained when `setNodes` is subsequently called (e.g., by CasC re-application).

## Evidence
*   **Problem 1 (Incomplete Fix for Restarts):**
    *   **Diff:** `core/src/main/java/jenkins/model/Nodes.java:124` adds `node.setTemporaryOfflineCause(oldNode.getTemporaryOfflineCause());`. This line copies the cause from `oldNode`.
    *   **PR Description:** "So the offline cause is lost when reapplying casc or restarting Jenkins." and "This change retains the offline cause in those cases."
    *   **Structural Context:** The `OfflineCause` class and its persistence mechanism (e.g., `XStream` annotations or explicit save/load in `Node.java`'s `save` or `onLoad` methods) are not visible in the diff or explicitly mentioned as being persisted. If `OfflineCause` is not persisted, `oldNode.getTemporaryOfflineCause()` would return `null` after a restart.
*   **Problem 2 (Insufficient Test Coverage for CLI Interactions):**
    *   **Diff:** `core/src/main/java/hudson/model/Node.java:280` changes `setTemporaryOfflineCause` to `public`, making it accessible for various callers, including CLI commands.
    *   **Structural Context:**
        *   `test/src/test/java/hudson/cli/OfflineNodeCommandTest.java`
        *   `test/src/test/java/hudson/cli/OnlineNodeCommandTest.java`
        *   `test/src/test/java/hudson/cli/WaitNodeOfflineCommandTest.java`
        *   These test files indicate that CLI commands are a common way to manage node offline status, which would involve setting the `temporaryOfflineCause` on a `Node` object. The current PR's test `test/src/test/java/jenkins/model/NodesTest.java::setNodesRetainsOfflineCause` does not simulate CLI interaction.

## Impact
1.  **Problem 1 (Incomplete Fix for Restarts):** If `OfflineCause` is not persisted, users will continue to lose the temporary offline cause of agents after a Jenkins restart, despite the PR's stated intent. This leads to an inconsistent user experience where CasC re-application works as expected, but a full restart does not. Agents might come back online without their intended offline cause, or the cause might be reset to a default, requiring manual re-configuration.
2.  **Problem 2 (Insufficient Test Coverage for CLI Interactions):** If a user takes an agent offline using a CLI command (e.g., `OfflineNodeCommand`) and then CasC configuration is reapplied, the offline cause set by the CLI might be inadvertently overwritten or lost if the `setNodes` logic doesn't correctly handle this interaction. This could lead to confusion and unexpected agent behavior.

## Recommendation (Fix / Tests / Risks)
1.  **Address Restart Persistence:**
    *   **Fix/Clarification:** Determine if `OfflineCause` is intended to be persisted to disk. If yes, ensure `OfflineCause` and its subclasses are properly `XStream` serializable and that the `temporaryOfflineCause` field in `hudson/model/Node.java` is persisted/loaded. If no, update the PR description to clarify that this fix specifically addresses re-application of configuration *without* a full Jenkins restart, and that `OfflineCause` is intentionally transient across restarts.
    *   **Tests:** If the intent is for the cause to survive restarts, add a new test case to `test/src/test/java/jenkins/model/NodesRestartTest.java`. This test should:
        *   Create a `DumbSlave` and set its `temporaryOfflineCause` using `agentA.setTemporaryOfflineCause(new OfflineCause.UserCause(user, "unitTest"));`.
        *   Simulate a Jenkins restart (e.g., using `r.jenkins.reload()`).
        *   Verify that `Jenkins.get().getNode("nodeA").getTemporaryOfflineCause()` is still present and correct after the restart.
2.  **Add CLI Integration Test:**
    *   **Tests:** Extend `test/src/test/java/jenkins/model/NodesTest.java` or create a new test in `test/src/test/java/hudson/cli/OfflineNodeCommandTest.java` to cover the interaction.
        *   Scenario: Take an agent offline using `hudson.cli.OfflineNodeCommand`.
        *   Then, simulate CasC re-application by calling `Jenkins.get().setNodes()` with a new `DumbSlave` instance for the same agent.
        *   Verify that the `temporaryOfflineCause` (including its reason and user) is still present and correct after `setNodes`.

## Traceability
Not specified