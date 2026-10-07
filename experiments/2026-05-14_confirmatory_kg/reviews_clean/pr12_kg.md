```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies test configurations to skip symlink tests on Windows developer machines while ensuring they run on CI environments.

## Problem
1. The removal of `WindowsUtil.java` may affect other tests or functionalities that rely on checking symlink support on Windows.
2. The current approach requires developers to manually set an environment variable (`DISABLE_SYMLINK_TESTS`) when running tests in an IDE, which could lead to inconsistent test results if not properly documented or communicated.

## Evidence
- **test/src/test/java/hudson/model/WindowsUtil.java**: Entire file deleted, which previously provided utility methods for checking symlink support on Windows.
- **pom.xml:574-577**: Introduction of a Maven profile to set the `DISABLE_SYMLINK_TESTS` environment variable.
- **core/src/test/java/hudson/FilePathTest.java:1128**: Modified test to skip based on the `DISABLE_SYMLINK_TESTS` environment variable.
- **test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java:590, 731, 805**: Tests modified to skip based on the `DISABLE_SYMLINK_TESTS` environment variable.

## Impact
- **Technical Impact**: Removing `WindowsUtil.java` could break other tests or functionalities that depend on it for symlink support checks. Developers might face challenges running tests consistently if they are unaware of the need to set the environment variable manually.
- **Risk**: Potential for inconsistent test results across different environments, especially for new developers who might not be aware of the manual setup required.

## Recommendation (Fix / Tests / Risks)
1. **Reintroduce `WindowsUtil.java`**: Consider keeping the utility class or refactor its functionality into another utility class to maintain symlink support checks.
2. **Documentation**: Clearly document the need for setting the `DISABLE_SYMLINK_TESTS` environment variable in developer guides or README files to ensure developers are aware of the requirement.
3. **Automate Environment Setup**: Explore automating the environment variable setup for IDEs to reduce manual steps and potential errors.

## Traceability
- Code Owners: Not specified
```