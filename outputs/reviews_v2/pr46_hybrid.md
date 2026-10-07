```
# Review Note — Evidence-Anchored

**Scope:** This PR adds undo/redo support for camera movements in Pilot Mode within the Godot Engine editor.

## Problem
1. The undo session management logic may not handle rapid toggling of the pilot preview mode correctly.
2. The `_pilot_commit_undo_session` function is called in multiple places, which could lead to redundant or conflicting undo actions.
3. Lack of test coverage for the new undo/redo functionality, which could lead to undetected bugs.

## Evidence
- `node_3d_editor_plugin.cpp:3244` and `node_3d_editor_plugin.cpp:4856`: `_pilot_commit_undo_session` is called when toggling camera preview and pilot preview, which might conflict if toggled rapidly.
- `node_3d_editor_plugin.cpp:3583`: `_pilot_tick_undo_session` is called every frame, which could lead to performance issues if not managed properly.
- `node_3d_editor_plugin.cpp:3072-3100`: The logic for starting and committing undo sessions is complex and could benefit from additional testing to ensure all edge cases are handled.

## Impact
- The current implementation could lead to inconsistent undo states if the pilot preview is toggled rapidly, potentially causing user confusion or data loss.
- Redundant calls to `_pilot_commit_undo_session` might result in unnecessary performance overhead and complex undo histories.
- Without proper testing, there is a risk of introducing regressions or bugs that could affect the stability of the editor.

## Recommendation (Fix / Tests / Risks)
1. Implement a debounce mechanism to handle rapid toggling of the pilot preview mode to ensure consistent undo states.
2. Review and refactor the calls to `_pilot_commit_undo_session` to minimize redundancy and ensure they are only called when necessary.
3. Add unit tests and integration tests to cover the new undo/redo functionality, focusing on edge cases such as rapid toggling and simultaneous camera movements.

## Traceability
Not specified
```