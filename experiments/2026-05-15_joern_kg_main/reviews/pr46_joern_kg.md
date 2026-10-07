# Review Note — Evidence-Anchored

**Scope:** This PR adds undo/redo functionality for camera movements made in Pilot Mode within the 3D editor viewport.

## Problem
1.  **Loss of Undo History on External Camera Movement:** The current implementation discards an active pilot undo session without committing it if the camera is moved externally while pilot mode is active. This can lead to lost undo history for user-initiated pilot movements.
2.  **Granularity Discrepancy and Potential for Excessive Undo Steps:** The PR description states "The camera transform is committed to the undo/redo manager after 500" (presumably milliseconds), but the code commits after 150ms of *idle time*. This discrepancy, combined with the idle-time-based commit, could lead to a large number of granular undo steps for what a user perceives as a single, slightly paused camera adjustment.
3.  **Lack of Dedicated Test Coverage:** There are no explicit tests for the new undo/redo logic in Pilot Mode, leaving this new feature vulnerable to regressions and making it difficult to verify correct behavior across various editor states and user interactions.

## Evidence
*   **Problem 1 (Loss of Undo History):**
    *   `editor/scene/3d/node_3d_editor_plugin.cpp:3583`: Inside `_notification(int p_what)` for `NOTIFICATION_PROCESS`, when `_camera_moved_externally()` is true, the code sets `pilot_undo_session_active = false; pilot_undo_idle_time = 0.0;` without calling `_pilot_commit_undo_session()`.
    *   The `_camera_moved_externally()` check can be triggered by external scripts or other editor tools that directly manipulate the `Camera3D` node's transform.
*   **Problem 2 (Granularity Discrepancy):**
    *   PR Description: "The camera transform is committed to the undo/redo manager after 500"
    *   `editor/scene/3d/node_3d_editor_plugin.cpp:3072`: `_pilot_tick_undo_session` checks `if (pilot_undo_idle_time > 0.15)`.
    *   `editor/scene/3d/node_3d_editor_plugin.cpp:3072`: `_pilot_commit_undo_session` uses `UndoRedo::MERGE_ENDS`.
*   **Problem 3 (Lack of Test Coverage):**
    *   No test files are referenced in the provided structural context that specifically cover `Node3DEditorViewport`'s pilot mode undo/redo functionality. The existing call graph shows interactions with `3d/camera_3d_editor_plugin.cpp` and `3d/gizmos/camera_3d_gizmo_plugin.cpp`, but no corresponding test files are listed.

## Impact
1.  **Data Loss / Unexpected Behavior:** Users performing pilot camera movements might find their undo history incomplete or missing if another part of the editor or a script modifies the camera's transform concurrently. This breaks the expected "undo" contract.
2.  **Poor User Experience / Bloated Undo History:** The discrepancy between the stated 500ms and the implemented 150ms idle time, combined with the `MERGE_ENDS` flag, could lead to a very fine-grained undo history. Users might have to press undo multiple times to revert what they perceive as a single continuous action, or conversely, a brief pause might prematurely commit an action they intended to continue.
3.  **Increased Risk of Regressions:** Without dedicated tests, future changes to `Node3DEditorViewport` or related camera/editor logic could inadvertently break the pilot mode undo/redo feature, leading to silent failures that are hard to detect and debug.

## Recommendation (Fix / Tests / Risks)
1.  **Fix (Problem 1):** Before resetting `pilot_undo_session_active` in `_notification` when `_camera_moved_externally()` is true, call `_pilot_commit_undo_session()`. This ensures that any active pilot movement is recorded as an undo step before the external change takes precedence.
2.  **Clarify/Adjust (Problem 2):**
    *   **Option A (Clarify):** Update the PR description to accurately reflect the `0.15` second idle time for committing.
    *   **Option B (Adjust):** Re-evaluate the `0.15` second idle time. If the intention was 500ms (0.5s), adjust `_pilot_tick_undo_session` accordingly. Consider if a longer idle time or a different commit trigger (e.g., on explicit user action like releasing a key/mouse button, or a total movement duration threshold) would provide a better user experience for undo granularity.
3.  **Tests (Problem 3):** Add new editor tests to cover the pilot mode undo/redo functionality.
    *   Create a test scenario in a new file like `test/editor/test_node_3d_editor_viewport.gd` (or similar C++ test if appropriate for editor tests) that:
        *   Activates pilot mode for a `Camera3D` node.
        *   Simulates camera movement (e.g., by calling `_cursor_interpolated` with different transforms).
        *   Simulates idle time to trigger `_pilot_commit_undo_session` via `_pilot_tick_undo_session`.
        *   Verifies that `EditorUndoRedoManager::get_singleton()->undo()` correctly reverts the camera's transform.
        *   Tests edge cases like `_camera_moved_externally()` (after implementing fix 1), switching cameras via `switch_preview_camera`, and exiting pilot mode via `_toggle_pilot_preview` or `_toggle_camera_preview`.

## Traceability
Not specified