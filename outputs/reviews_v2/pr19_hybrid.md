```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the workspace view of a job to use modern SVG icons instead of legacy GIF and PNG icons.

## Problem
1. **Backward Compatibility Concerns**: The removal of legacy icons might affect plugins or custom scripts that rely on these specific icon files.
2. **Icon Size and Style Consistency**: The new SVG icons might not match the size and style of the previous icons, potentially affecting UI layout and consistency.
3. **Test Coverage**: There is no indication that the changes have been tested to ensure that all instances of icon usage are updated and functioning correctly.

## Evidence
- **Backward Compatibility Concerns**: 
  - `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:659-675`: Legacy icons are replaced with new SVG icons.
  - `core/src/main/java/org/jenkins/ui/icon/IconSet.java:329-355`: Removal of legacy icon references.
- **Icon Size and Style Consistency**:
  - `core/src/main/resources/hudson/model/DirectoryBrowserSupport/dir.jelly:39-45`: Change from `icon-go-next icon-sm` to `icon-next icon-md`.
- **Test Coverage**:
  - No new tests or updates to existing tests in `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` or related test files.

## Impact
- **Technical Impact**: The removal of legacy icons could break existing integrations or customizations that depend on these files. Inconsistent icon sizes and styles may lead to UI misalignment or visual discrepancies.
- **Risk**: Without adequate testing, there is a risk of unintentional UI regressions or broken functionality in areas where icons are used.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility**: Consider deprecating the legacy icons instead of immediate removal, providing a transition period for users to adapt.
2. **Icon Size and Style Consistency**: Ensure that the new SVG icons match the size and style of the previous icons to maintain UI consistency.
3. **Test Coverage**: Add or update tests in `DirectoryBrowserSupportTest.java` and other relevant test files to verify that all icon changes are correctly applied and do not introduce regressions.

## Traceability
Not specified
```