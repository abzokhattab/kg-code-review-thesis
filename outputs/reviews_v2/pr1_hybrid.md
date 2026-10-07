```
# Review Note — Evidence-Anchored

**Scope:** This PR replaces an OpenXR initialization alert dialog with a warning log message and introduces a project setting to toggle this behavior.

## Problem
1. The new project setting `xr/openxr/startup_alert` is not documented in the user-facing documentation, which could lead to confusion.
2. The change in behavior from a blocking alert to a non-blocking log message might not be adequately tested, especially in scenarios where the alert is critical for user awareness.

## Evidence
- `doc/classes/ProjectSettings.xml:2381`: The new setting `xr/openxr/startup_alert` is added but lacks documentation for users.
- `modules/openxr/register_types.cpp:114-128`: The logic for displaying the alert or logging a warning is implemented, but there is no indication of additional test coverage for this change.

## Impact
- Users may not be aware of the new setting due to lack of documentation, leading to unexpected behavior if they rely on the alert dialog.
- The change from a modal alert to a log message could result in users missing critical initialization failures, especially if they do not regularly check logs.

## Recommendation (Fix / Tests / Risks)
1. **Documentation**: Update the user documentation to include the new `xr/openxr/startup_alert` setting, explaining its purpose and usage.
2. **Testing**: Ensure there are automated tests that verify both the alert and log message behaviors under different initialization failure scenarios.
3. **User Feedback**: Consider gathering user feedback on this change to ensure it meets the needs of the broader user base, especially those who might rely on the alert for debugging.

## Traceability
Not specified
```