```
# Review Note — Evidence-Anchored

**Scope:** This PR replaces an OpenXR initialization failure alert dialog with a warning log message and introduces a project setting to toggle this behavior.

## Problem
1. The new project setting `xr/openxr/startup_alert` is not documented in the user-facing documentation, which could lead to confusion.
2. The change in behavior from a blocking alert to a non-blocking log message might not be adequately tested for all user scenarios, especially for those relying on the alert for critical feedback.

## Evidence
- `doc/classes/ProjectSettings.xml:2378-2381`: The new setting `xr/openxr/startup_alert` is added but lacks accompanying documentation for users.
- `modules/openxr/register_types.cpp:113-129`: The logic for handling the OpenXR initialization failure has been modified to use a warning log message instead of an alert dialog, with a conditional check based on the new setting.

## Impact
- Users may not be aware of the new setting due to lack of documentation, leading to unexpected behavior if they rely on the alert dialog.
- The change from a modal alert to a log message could result in missed critical feedback during development, especially if the console is not actively monitored.

## Recommendation (Fix / Tests / Risks)
1. **Documentation**: Update the user-facing documentation to include details about the new `xr/openxr/startup_alert` setting and its implications.
2. **Testing**: Ensure comprehensive testing is conducted to verify that the new behavior does not negatively impact workflows that depend on immediate feedback from the alert dialog.
3. **User Feedback**: Consider gathering feedback from users who rely on OpenXR to ensure the change aligns with their needs and does not introduce workflow disruptions.

## Traceability
Not specified
```