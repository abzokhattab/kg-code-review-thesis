```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the workspace view of a job to use modern SVG icons instead of legacy GIF and PNG icons.

## Problem
1. Inconsistent icon class naming conventions.
2. Potential missing icon definitions in the `IconSet`.
3. Lack of backward compatibility for removed icons.

## Evidence
- `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:663-667`: The icon class names for folders and documents have been updated, but the naming convention is inconsistent with existing patterns.
- `core/src/main/java/org/jenkins/ui/icon/IconSet.java:329-355`: Removal of icon definitions without ensuring all usages are updated or deprecated.
- `core/src/main/resources/hudson/model/DirectoryBrowserSupport/dir.jelly:39`: Change in icon class from `icon-go-next` to `icon-next` without verifying if `icon-next` is defined elsewhere.

## Impact
- **Technical Impact:** The inconsistent naming conventions could lead to confusion and maintenance challenges. Missing icon definitions might result in broken UI elements if the new icons are not properly registered. Removing icons without backward compatibility could break existing plugins or customizations relying on these icons.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure all new icon class names follow a consistent naming convention and are registered in `IconSet`.
2. **Tests:** Add tests to verify that all icons are correctly displayed in the UI and that no broken links exist.
3. **Risks:** Consider providing a deprecation period for removed icons to allow dependent plugins or customizations to adapt.

## Traceability
Not specified
```