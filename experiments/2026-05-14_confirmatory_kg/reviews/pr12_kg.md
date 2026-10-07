# Review Note — Evidence-Anchored

**Scope:** This PR introduces a mechanism to skip symbolic link-dependent tests on Windows developer machines by setting an environment variable via a Maven profile, while ensuring these tests run in CI environments. It also removes a redundant utility class for Windows symlink detection.

## Integration Risk
*   **`core/src/test/java/hudson/UtilTest.java`**: This file is listed as dependent but is not modified in the diff. If it previously imported or called `hudson.model.WindowsUtil.isWindowsSymlinkSupported()`, it would now fail to compile or run. This needs verification.
*   **`core/src/test/java/hudson/RemoveWindowsDirectoryJunctionTest.java`**: Similar to `UtilTest.java`, if this file relied on the deleted `hudson.model.WindowsUtil.isWindowsSymlinkSupported()`, it would now be broken.
*   **`core/src/test/java/hudson/os/WindowsUtilTest.java`**: This test file is for `core/src/main/java/hudson/os/WindowsUtil.java`. While `core/src/main/java/hudson/os/WindowsUtil.java` is not changed, if `core/src/test/java/hudson/os/WindowsUtilTest.java` had any indirect dependency on the *deleted* `test/src/test/java/hudson/model/WindowsUtil.java` (e.g., for setup or shared utilities), it could be affected.
*   **`core/src/main/java/hudson/os/WindowsUtil.java`**: This is the main utility class for Windows OS operations. It is highly unlikely to depend on a test utility class (`hudson.model.WindowsUtil`), but its own symlink detection logic (if any) could be implicitly affected if the general assumption about symlink support changes across the codebase.
*   **`test/src/test/java/hudson/tasks/LogRotatorTest.java`**: If this file imported or called `hudson.model.WindowsUtil.isWindowsSymlinkSupported()`, it would now fail.

The diff shows that `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` and `test/src/test/java/hudson/tasks/ArtifactArchiverTest.java` (which are also dependents of the deleted `WindowsUtil.java`) have been correctly updated to remove the dependency. `core/src/test/java/hudson/FilePathTest.java` is also updated. The risk lies with other dependent files not explicitly shown in the diff.

## Test Coverage Assessment
*   **`core/src/test/java/hudson/os/WindowsUtilTest.java`**: This test file is listed as covering changed code. However, the PR's core changes involve the introduction of the `DISABLE_SYMLINK_TESTS` environment variable and a new Maven profile in `pom.xml` to manage its activation. `core/src/test/java/hudson/os/WindowsUtilTest.java` tests `core/src/main/java/hudson/os/WindowsUtil.java`, which is not modified in this PR. Therefore, this test file does **not** cover the new logic for skipping symlink tests based on the `DISABLE_SYMLINK_TESTS` environment variable, nor does it verify the `pom.xml` profile's activation conditions (Windows + not CI). Coverage is inadequate for the new functionality.

## Problem
1.  **Untested Maven Profile and Environment Variable Logic**: The new mechanism to disable symlink tests on Windows developer machines (via `pom.xml` profile and `DISABLE_SYMLINK_TESTS` environment variable) is not covered by any tests. This leaves the core functionality of the PR unverified, especially the `!env.CI` condition for profile activation.
2.  **Potential Unhandled Dependencies on Deleted Utility**: While the diff shows updates for some files that used `hudson.model.WindowsUtil.isWindowsSymlinkSupported()`, there are other files listed in the structural context as dependents that are not modified in the diff. These files (`core/src/test/java/hudson/UtilTest.java`, `core/src/test/java/hudson/RemoveWindowsDirectoryJunctionTest.java`, `core/src/test/java/hudson/tasks/LogRotatorTest.java`) might still be importing or calling methods from the now-deleted `test/src/test/java/hudson/model/WindowsUtil.java`, leading to compilation or runtime errors.

## Evidence
*   **Untested Logic**:
    *   `pom.xml:176-178` (environment variable passing)
    *   `pom.xml:574-585` (new Maven profile `disable-symlink-tests` with `os` and `!env.CI` activation)
    *   `core/src/test/java/hudson/FilePathTest.java:1130` (usage of `System.getenv("DISABLE_SYMLINK_TESTS")`)
    *   `core/src/test/java/jenkins/security/Security3657Test.java:29` (usage of `System.getenv("DISABLE_SYMLINK_TESTS")`)
    *   `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java:593` (usage of `System.getenv("DISABLE_SYMLINK_TESTS")`)
    *   `core/src/test/java/hudson/os/WindowsUtilTest.java` (listed as covering changed code, but not modified to test the new logic)
*   **Potential Unhandled Dependencies**:
    *   `test/src/test/java/hudson/model/WindowsUtil.java` (deleted file)
    *   `core/src/test/java/hudson/UtilTest.java` (dependent, not modified)
    *   `core/src/test/java/hudson/RemoveWindowsDirectoryJunctionTest.java` (dependent, not modified)
    *   `test/src/test/java/hudson/tasks/LogRotatorTest.java` (dependent, not modified)

## Impact
*   **Untested Logic**: The core functionality of conditionally skipping tests on Windows developer machines may not work as intended, leading to continued test failures for new contributors or unexpected test skips in CI environments if the `!env.CI` condition is misconfigured.
*   **Potential Unhandled Dependencies**: Compilation failures or runtime `NoClassDefFoundError` exceptions could occur in dependent test files that were not updated to reflect the deletion of `test/src/test/java/hudson/model/WindowsUtil.java`, breaking the build for other modules.

## Recommendation
1.  **Add dedicated integration tests for the new symlink skipping mechanism**: Create a new test class (e.g., `SymlinkTestSkippingIntegrationTest.java`) that specifically verifies the `DISABLE_SYMLINK_TESTS` environment variable and the `pom.xml` profile. This test should:
    *   Run a simple symlink-dependent test on Windows with `mvn test` (expect skip).
    *   Run the same test on Windows with `CI=true mvn test` (expect run).
    *   Run the same test on a non-Windows OS (expect run).
    *   This ensures the `pom.xml` profile activation logic (`<os><family>windows</family></os>` and `<property><name>!env.CI</name></property>`) and the environment variable propagation are correct.
2.  **Verify all dependents of `hudson.model.WindowsUtil.java`**: Perform a global search for imports or calls to `hudson.model.WindowsUtil` or `isWindowsSymlinkSupported()` across the entire codebase, specifically checking `core/src/test/java/hudson/UtilTest.java`, `core/src/test/java/hudson/RemoveWindowsDirectoryJunctionTest.java`, `core/src/test/java/hudson/os/WindowsUtilTest.java`, and `test/src/test/java/hudson/tasks/LogRotatorTest.java`. Update any remaining call sites or remove imports as necessary.

## Traceability
Not specified