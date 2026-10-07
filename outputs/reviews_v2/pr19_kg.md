```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the workspace view of a job to use modern SVG icons instead of legacy GIF and PNG icons.

## Problem
1. **Backward Compatibility Concerns:** The removal of legacy icons might affect plugins or custom scripts that rely on these specific icon paths.
2. **Incomplete Test Coverage:** The changes in icon usage are not directly covered by existing tests, which could lead to unnoticed UI regressions.
3. **Potential Integration Issues:** The changes might impact other parts of the system that depend on the old icon paths or classes.

## Evidence
- **Backward Compatibility Concerns:** 
  - `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:659-669` - Legacy icons are replaced with new SVG icons.
  - `core/src/main/java/org/jenkins/ui/icon/IconSet.java:329-355` - Removal of legacy icon references.
- **Incomplete Test Coverage:** 
  - No direct tests in `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` or `core/src/test/java/org/jenkins/ui/icon/IconSetTest.java` that verify the visual changes.
- **Potential Integration Issues:** 
  - `core/src/main/resources/hudson/model/DirectoryBrowserSupport/dir.jelly:39-47` - Changes in icon class names that might affect UI rendering.

## Impact
- **Technical Impact:** The removal of legacy icons could break existing plugins or custom scripts that depend on these icons. Without direct test coverage, UI regressions might go unnoticed, leading to a degraded user experience.
- **Risks:** There is a risk of breaking backward compatibility and introducing UI inconsistencies if the new icons do not render correctly in all contexts.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility:** Consider providing a deprecation period where both old and new icons are available, or document the changes clearly for plugin developers.
2. **Test Coverage:** Add UI tests to verify that the new icons render correctly in all affected views and that there are no visual regressions.
3. **Integration Testing:** Conduct thorough integration testing to ensure that no other parts of the system are adversely affected by these changes.

## Traceability
- **Code Owners:** Not specified
```