# Review Note — Evidence-Anchored

**Scope:** This PR updates the workspace view and artifact lists to use modern SVG icons instead of legacy GIF/PNG images, and removes the old image files and their `IconSet` registrations.

## Problem
1.  **Critical Integration Risk: Missing IconSet Registrations for New Icons.** The PR introduces new icon class names (`icon-document`, `icon-folder-delete`, `icon-document-delete`, `icon-next`) in `DirectoryBrowserSupport.java` and the Jelly views, but these new classes are not registered in `org.jenkins.ui.icon.IconSet.java`. The `IconSet` is responsible for mapping these class names to actual SVG URLs, and without these definitions, the icons will fail to render.
2.  **Test Gap: Incomplete IconSet and DirectoryBrowserSupport Test Updates.** The existing tests for `IconSet` and `DirectoryBrowserSupport` are not updated to reflect the changes. This leaves the new icon mappings untested and doesn't verify the removal of old icon definitions or the correct behavior of `DirectoryBrowserSupport.Entry.getIconClassName()` with the new class names.
3.  **Potential Integration Risk: Direct Usage of `DirectoryBrowserSupport.Entry.getIconName()` by Plugins.** The `getIconName()` method in `DirectoryBrowserSupport.Entry` now returns `.svg` filenames directly. While the primary rendering path uses `getIconClassName()` with `<l:icon>`, any plugins or custom views that might directly call `DirectoryBrowserSupport.Entry.getIconName()` to construct image URLs (e.g., `images/16x16/${entry.getIconName()}`) will break if they expect PNG/GIF or if the SVG files are not located in the expected `images/16x16` directory.

## Evidence
*   **Problem 1 (Missing IconSet Registrations):**
    *   `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:668` changes `icon-text` to `icon-document`.
    *   `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:669` changes `icon-folder-error` to `icon-folder-delete`.
    *   `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:670` changes `icon-text-error` to `icon-document-delete`.
    *   `core/src/main/resources/hudson/model/DirectoryBrowserSupport/dir.jelly:42` changes `icon-go-next` to `icon-next`.
    *   The diff for `core/src/main/java/org/jenkins/ui/icon/IconSet.java` shows removals of old icon definitions but no corresponding additions for `icon-document`, `icon-folder-delete`, `icon-document-delete`, or `icon-next`.
    *   The call-graph edge `hudson/Functions.java::tryGetIcon → org/jenkins/ui/icon/IconSet.java::getIconByClassSpec` confirms that `l:icon` tags rely on `IconSet` for resolution.
*   **Problem 2 (Test Gap):**
    *   `core/src/main/java/org/jenkins/ui/icon/IconSet.java` has several lines removed (e.g., `329`, `343`, `355`).
    *   `core/src/test/java/org/jenkins/ui/icon/IconSetTest.java` and `core/src/test/java/org/jenkins/ui/icon/IconSetJenkins68805Test.java` are listed as related tests but are not modified in the PR.
    *   `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:667-670` modifies the `getIconClassName()` method.
    *   `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` is a related test but is not modified in the PR.
*   **Problem 3 (Direct Usage of `getIconName()`):**
    *   `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:660` changes `folder.png` to `folder.svg` and `text.png` to `document.svg`.
    *   `core/src/main/java/hudson/model/DirectoryBrowserSupport.java:662` changes `folder-error.png` to `folder-delete.svg` and `text-error.png` to `document-delete.svg`.
    *   The structural context does not explicitly show callers of `DirectoryBrowserSupport.Entry.getIconName()`, suggesting it might be used in less common or plugin-specific scenarios.

## Impact
*   **Problem 1:** The workspace view and artifact lists will display broken or missing icons for folders, files, and error states, leading to a degraded user experience and visual regressions. The "go next" icon in the directory browser will also be missing.
*   **Problem 2:** The lack of updated tests means that the new icon system's correctness and the successful removal of old assets are not verified, increasing the risk of future regressions or unexpected behavior.
*   **Problem 3:** Any plugins or custom UI components that relied on the specific `.png` or `.gif` filenames returned by `DirectoryBrowserSupport.Entry.getIconName()` will break, potentially leading to broken images or runtime errors in those extensions.

## Recommendation (Fix / Tests / Risks)
1.  **Fix Missing IconSet Registrations:** Add the new icon class names (`icon-document`, `icon-folder-delete`, `icon-document-delete`, `icon-next`) and their corresponding SVG paths to `core/src/main/java/org/jenkins/ui/icon/IconSet.java`. Ensure they are registered with the correct SVG URLs (e.g., `document.svg`, `folder-delete.svg`, `document-delete.svg`, `next.svg`).
2.  **Update IconSet Tests:** Modify `core/src/test/java/org/jenkins/ui/icon/IconSetTest.java` and `core/src/test/java/org/jenkins/ui/icon/IconSetJenkins68805Test.java` to:
    *   Assert that the *new* icon classes (`icon-document`, `icon-folder-delete`, `icon-document-delete`, `icon-next`) are correctly registered and resolve to their respective SVG URLs.
    *   Assert that the *removed* icon classes (`icon-folder-error`, `icon-text-error`, `icon-text`) are no longer resolvable or are handled gracefully (e.g., return a default missing icon).
3.  **Update DirectoryBrowserSupport Tests:** Modify `test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java` to include assertions that `DirectoryBrowserSupport.Entry.getIconClassName()` returns the *new* expected icon class names (`icon-document`, `icon-folder-delete`, `icon-document-delete`) for various file and folder states (readable, unreadable).
4.  **Mitigate `getIconName()` Risk:** Add a comment to `DirectoryBrowserSupport.Entry.getIconName()` explaining that it now returns SVG filenames and that `getIconClassName()` should be preferred for UI rendering via `<l:icon>`. Consider adding a deprecation warning if `getIconName()` is not intended for direct use.

## Traceability
Not specified