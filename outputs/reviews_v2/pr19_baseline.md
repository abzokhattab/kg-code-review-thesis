```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the workspace view of a job to use modern SVG icons instead of legacy GIF and PNG icons.

## Problem
1. Potential missing SVG assets for new icon references.
2. Inconsistent icon class naming conventions that may lead to styling issues.

## Evidence
- `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:663-667`: References to new SVG icons (`folder.svg`, `document.svg`, `folder-delete.svg`, `document-delete.svg`) without confirmation of their existence in the assets.
- `core/src/main/resources/hudson/model/DirectoryBrowserSupport/dir.jelly:42`: Change from `icon-go-next` to `icon-next` without ensuring the new class is defined and styled appropriately.

## Impact
- If the SVG assets are missing, the icons will not render, leading to a broken UI in the workspace view.
- Inconsistent or undefined icon class names can result in styling issues, causing icons to appear incorrectly or not at all.

## Recommendation (Fix / Tests / Risks)
1. Verify that all referenced SVG icons (`folder.svg`, `document.svg`, `folder-delete.svg`, `document-delete.svg`) are present in the assets directory.
2. Ensure that all new icon class names (`icon-next`, `icon-document`) are defined in the CSS and styled correctly.
3. Add tests to verify that the icons render correctly in the UI, possibly using a UI testing framework to automate this check.

## Traceability
Not specified
```