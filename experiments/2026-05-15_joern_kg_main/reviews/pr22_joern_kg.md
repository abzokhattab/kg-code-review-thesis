# Review Note — Evidence-Anchored

**Scope:** This pull request moves `AbstractResetIntegrationTest` and its subclasses (`ResetIntegrationTest`, `ResetIntegrationWithSslTest`) from the `streams:integration-tests` module to the `tools` module, along with updating build dependencies and replacing Hamcrest assertions with JUnit assertions.

## Problem
1.  **Compilation Failure for `FineGrainedAutoResetIntegrationTest`:** The `AbstractResetIntegrationTest` class, which is likely a superclass for other integration tests, has been moved to the `tools` module. However, `FineGrainedAutoResetIntegrationTest.java` remains in the `streams:integration-tests` module and is not updated to reflect this change. This will cause a compilation failure for `FineGrainedAutoResetIntegrationTest` as it will no longer be able to find its superclass.
2.  **Unnecessary `hamcrest` runtime dependency:** The PR explicitly replaces `org.hamcrest.MatcherAssert.assertThat` calls with `org.junit.jupiter.api.Assertions.assertEquals` and `assertTrue` in the moved test files, indicating an intent to reduce or remove direct `hamcrest` usage. However, `testRuntimeOnly libs.hamcrest` is added to the `tools` module's `build.gradle` dependencies without clear justification for its continued necessity.

## Evidence
*   **Problem 1 (Compilation Failure):**
    *   **Diff:** `streams/integration-tests/src/test/java/org/apache/kafka/streams/integration/AbstractResetIntegrationTest.java` was renamed to `tools/src/test/java/org/apache/kafka/tools/AbstractResetIntegrationTest.java` (lines 1-2 in diff).
    *   **Structural Context:** `streams/integration-tests/src/test/java/org/apache/kafka/streams/integration/FineGrainedAutoResetIntegrationTest.java` is listed as a file that depends on changes.
    *   **Structural Context:** The `build.gradle` diff adds `testImplementation project(':streams:integration-tests').sourceSets.test.output` to `project(':tools')` (line 2500), but there is no corresponding `testImplementation project(':tools')` added to `project(':streams:integration-tests')`. This means `streams:integration-tests` cannot access classes in `tools`.
*   **Problem 2 (Hamcrest Dependency):**
    *   **Diff:** `tools/src/test/java/org/apache/kafka/tools/AbstractResetIntegrationTest.java` shows replacements like `assertThat(resultRerun, equalTo(result))` with `assertEquals(result, resultRerun)` (e.g., line 247, 307, 308, 310).
    *   **Diff:** `tools/src/test/java/org/apache/kafka/tools/ResetIntegrationTest.java` shows similar replacements (e.g., line 210, 219, 259, 306, 348).
    *   **Diff:** `build.gradle` (line 2516) adds `testRuntimeOnly libs.hamcrest` to `project(':tools')`.

## Impact
*   **Problem 1:** The `streams:integration-tests` module will fail to compile, specifically `FineGrainedAutoResetIntegrationTest.java`, leading to a broken build and potential regression of the fine-grained auto-reset functionality if this test is not run.
*   **Problem 2:** While not critical, an unnecessary `testRuntimeOnly` dependency can increase build times, artifact size, and potentially introduce dependency conflicts in the future. It also contradicts the apparent intent of removing direct `hamcrest` usage from the moved tests.

## Recommendation (Fix / Tests / Risks)
1.  **Fix `FineGrainedAutoResetIntegrationTest` compilation:**
    *   **Option A (Preferred):** Move `streams/integration-tests/src/test/java/org/apache/kafka/streams/integration/FineGrainedAutoResetIntegrationTest.java` to `tools/src/test/java/org/apache/kafka/tools/` and update its package declaration to `org.apache.kafka.tools`. This aligns it with its superclass and the other moved reset tests.
    *   **Option B:** If `FineGrainedAutoResetIntegrationTest` must remain in `streams:integration-tests`, then add `testImplementation project(':tools')` to the `project(':streams:integration-tests')` block in `build.gradle` and update the import statement in `FineGrainedAutoResetIntegrationTest.java` to `import org.apache.kafka.tools.AbstractResetIntegrationTest;`.
2.  **Review `hamcrest` dependency:**
    *   Investigate if `libs.hamcrest` is genuinely required by any other test classes within the `tools` module (e.g., by searching for `org.hamcrest` imports or `assertThat` calls in `tools/src/test/java`). If no other usage is found, remove `testRuntimeOnly libs.hamcrest` from `build.gradle` for `project(':tools')`.

## Traceability
Not specified