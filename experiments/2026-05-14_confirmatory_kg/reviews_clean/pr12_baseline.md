```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies test configurations to skip symbolic link tests on Windows developer machines while ensuring they run on CI environments.

## Problem
1. The current approach relies on developers manually setting an environment variable (`DISABLE_SYMLINK_TESTS`) when running tests in an IDE, which may lead to inconsistent test results.
2. The removal of `WindowsUtil.isWindowsSymlinkSupported()` may affect other parts of the codebase that rely on this utility for symlink support checks.

## Evidence
- `core/src/test/java/hudson/FilePathTest.java:1131`: The test now checks for the `DISABLE_SYMLINK_TESTS` environment variable.
- `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java:593`: Similar change to check the environment variable instead of using `WindowsUtil`.
- `test/src/test/java/hudson/model/WindowsUtil.java`: The entire file has been deleted, removing the utility function for checking symlink support.
- `pom.xml:577`: A new Maven profile is added to set the `DISABLE_SYMLINK_TESTS` environment variable on Windows.

## Impact
- Developers may forget to set the `DISABLE_SYMLINK_TESTS` variable, leading to test failures and confusion.
- The removal of `WindowsUtil` could break other tests or functionalities that depend on checking symlink support on Windows, potentially leading to undetected issues in CI environments.

## Recommendation (Fix / Tests / Risks)
1. Consider automating the setting of the `DISABLE_SYMLINK_TESTS` variable within IDEs or provide clear documentation to ensure developers are aware of this requirement.
2. Review the codebase for any dependencies on `WindowsUtil.isWindowsSymlinkSupported()` and refactor them to use the new approach or provide an alternative utility.
3. Add integration tests to ensure that the new configuration behaves as expected across different environments and IDEs.

## Traceability
Not specified
```