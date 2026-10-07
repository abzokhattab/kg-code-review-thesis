# Review Note — Evidence-Anchored

**Scope:** This PR introduces a mechanism to skip symbolic link-related tests on Windows developer machines while ensuring these tests always run in CI environments.

## Problem
1.  **Loss of Specific CI Configuration Assertion:** The removal of `WindowsUtil.assertConfiguration` means that if a Windows CI environment is misconfigured and does not support symbolic links, the tests will fail with a generic `IOException` or `UnsupportedOperationException` rather than a more explicit assertion message indicating a CI configuration issue.
2.  **Reliance on Environment Variable for Test Skipping:** The mechanism relies on the `DISABLE_SYMLINK_TESTS` environment variable. While the `pom.xml` profile is designed to manage this, an explicit override of this environment variable in a CI pipeline could inadvertently skip critical security tests.
3.  **Potential for Misinterpretation of Test Failures:** Without the explicit `isWindowsSymlinkSupported()` check, a test failure on a Windows CI machine due to symlink issues might initially be harder to diagnose as a configuration problem versus a code bug, although the stack trace would eventually point to it.

## Evidence
*   **Loss of Specific CI Configuration Assertion:**
    *   `diff --git a/test/src/test/java/hudson/model/WindowsUtil.java b/test/src/test/java/hudson/model/WindowsUtil.java` (entire file deleted)
    *   Specifically, the `assertConfiguration` method: `private static void assertConfiguration(boolean supported) { if (System.getenv("CI") != null) { assertTrue(supported, "Jenkins CI configurations must enable symlinks on Windows"); } }`
*   **Reliance on Environment Variable for Test Skipping:**
    *   `core/src/test/java/hudson/FilePathTest.java:1130` (`assumeTrue(Functions.isWindows() && !"true".equals(System.getenv("DISABLE_SYMLINK_TESTS")))`)
    *   `core/src/test/java/jenkins/security/Security3657Test.java:29` (`assumeFalse("true".equals(System.getenv("DISABLE_SYMLINK_TESTS")))`) (and many other lines in this file)
    *   `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java:593` (`assumeFalse("true".equals(System.getenv("DISABLE_SYMLINK_TESTS")))`) (and other lines in this file)
    *   `test/src/test/java/hudson/tasks/ArtifactArchiverTest.java:285` (`assumeFalse("true".equals(System.getenv("DISABLE_SYMLINK_TESTS")))`) (and other lines in this file)
*   **Potential for Misinterpretation of Test Failures:**
    *   `diff --git a/test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java b/test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` (line 24, removal of `import static hudson.model.WindowsUtil.isWindowsSymlinkSupported;`)
    *   `diff --git a/test/src/test/java/hudson/tasks/ArtifactArchiverTest.java b/test/src/test/java/hudson/tasks/ArtifactArchiverTest.java` (line 24, removal of `import static hudson.model.WindowsUtil.isWindowsSymlinkSupported;`)

## Impact
1.  **Reduced Diagnostic Clarity:** In CI environments, a failure due to missing symlink support will now result in a lower-level exception (e.g., `IOException` or `UnsupportedOperationException`) instead of a clear assertion message specifically stating that "Jenkins CI configurations must enable symlinks on Windows." This might slightly increase debugging time for CI failures.
2.  **Security Risk (Low):** While the `pom.xml` profile is correctly configured to prevent skipping in CI, an explicit, malicious, or accidental override of the `DISABLE_SYMLINK_TESTS` environment variable in a CI pipeline could lead to critical security tests being skipped without immediate detection, potentially allowing regressions related to symbolic link vulnerabilities to go unnoticed. This risk is mitigated by standard CI practices and pipeline security.
3.  **Developer Experience:** The primary goal of improving developer experience on Windows is achieved, as developers can now easily disable these tests.

## Recommendation (Fix / Tests / Risks)
1.  **Consider Reintroducing Specific CI Assertion (Optional):** While not strictly necessary for correctness, consider adding a more explicit check for symlink support within a dedicated CI-only test or a custom JUnit `Assumption` that provides a clearer error message if symlinks are not supported on a Windows CI agent. This would restore the diagnostic clarity provided by the removed `WindowsUtil.assertConfiguration`.
2.  **Document Environment Variable Usage:** Add a clear note in the project's `CONTRIBUTING.md` or `README.md` about the `DISABLE_SYMLINK_TESTS` environment variable, its purpose, and the expectation that it should *not* be set in CI environments.
3.  **Review CI Pipeline Configuration:** Ensure that CI pipeline configurations are robust against accidental or malicious setting of `DISABLE_SYMLINK_TESTS=true`. This is a general CI best practice but is highlighted by the reliance on an environment variable for test skipping.

## Traceability
Not specified