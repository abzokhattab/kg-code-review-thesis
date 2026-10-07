```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the workspace view of a job to use modern SVG icons instead of legacy GIF and PNG icons.

## Problem
1. **Backward Compatibility Concerns:** The removal of legacy icons might affect older systems or plugins that rely on these specific icon files.
2. **Incomplete Icon Replacement:** There might be instances where the new SVG icons are not correctly referenced or displayed, leading to broken UI elements.
3. **Test Coverage Gaps:** The changes in icon references might not be fully covered by existing tests, risking untested UI behavior.

## Evidence
- **Backward Compatibility Concerns:**
  - `war/src/main/webapp/images/16x16/folder-error.gif` and similar files are deleted without deprecation warnings or backward compatibility measures.
- **Incomplete Icon Replacement:**
  - `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:659-675`: Changes in icon references might not be reflected in all dependent files.
- **Test Coverage Gaps:**
  - No new tests added in `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` or related test files to verify the new icon paths.

## Impact
- **Technical Impact:** The removal of legacy icons without backward compatibility measures could lead to broken UI elements in environments that have not yet transitioned to the new icons. This could affect user experience and potentially break integrations with plugins or custom scripts that expect the old icons.
- **Risk of UI Breakage:** If any references to the old icons remain in the codebase or in external dependencies, it could result in missing icons or broken UI components.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility:** Consider providing a fallback mechanism or deprecation warning for the removed icons to ensure backward compatibility.
2. **Comprehensive Testing:** Add tests to verify that all UI components correctly display the new SVG icons, especially in `DirectoryBrowserSupportTest.java`.
3. **Documentation Update:** Update documentation to inform users and developers about the icon changes and any necessary steps they need to take to adapt to these changes.

## Traceability
- **Code Owners:** Not specified
```