```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the behavior of the dashboards sidebar to automatically close when entering edit mode and restore when exiting.

## Problem
1. The logic for toggling the dashboards drawer may not correctly handle cases where the drawer state is changed externally during edit mode.
2. The test coverage does not account for scenarios where the drawer state is manipulated outside the edit mode lifecycle.

## Evidence
- `public/app/features/dashboard-scene/scene/DashboardSceneRenderer.tsx:36-46`: The drawer state is checked and toggled based on the `isEditing` state, but does not account for external changes to the drawer state.
- `public/app/features/scopes/tests/editMode.test.ts:55-67`: Tests only cover the basic transition into and out of edit mode, without simulating external drawer state changes.

## Impact
- If the drawer state is changed by another component or user action while in edit mode, the current logic may not restore the drawer to its intended state upon exiting edit mode. This could lead to inconsistent UI behavior and confusion for users.

## Recommendation (Fix / Tests / Risks)
1. Implement a more robust mechanism to track and restore the drawer state that accounts for external changes during edit mode.
2. Extend test cases to simulate and verify behavior when the drawer state is altered by other components or user actions during edit mode.
3. Consider adding logging or state validation to help diagnose potential issues with drawer state management.

## Traceability
Not specified
```