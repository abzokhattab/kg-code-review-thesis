```
# Review Note — Evidence-Anchored

**Scope:** This PR replaces an OpenXR initialization failure alert dialog with a warning log message and introduces a project setting to toggle this behavior.

## Problem
1. The new project setting `xr/openxr/startup_alert` is not documented in the user-facing documentation, which could lead to confusion among users.
2. The change in behavior from a blocking alert to a non-blocking log message might not be adequately covered by existing tests, potentially leading to unnoticed failures in OpenXR initialization.

## Evidence
- `doc/classes/ProjectSettings.xml:2378-2381`: The new project setting `xr/openxr/startup_alert` is added but lacks accompanying documentation for users.
- `modules/openxr/register_types.cpp:113-129`: The logic for handling OpenXR initialization failure has been modified to use a warning log message instead of an alert dialog, with a conditional check based on the new setting.

## Impact
- **Technical Impact:** Users may not be aware of the new setting due to lack of documentation, leading to unexpected behavior if they rely on the alert dialog. Additionally, without proper test coverage, there is a risk that OpenXR initialization failures might not be detected promptly, affecting the user experience.
- **Integration Risks:** The change affects how initialization failures are communicated, which could impact workflows that depend on the alert dialog for immediate feedback.

## Recommendation (Fix / Tests / Risks)
1. **Documentation:** Update the user-facing documentation to include information about the new `xr/openxr/startup_alert` setting, explaining its purpose and usage.
2. **Testing:** Ensure that there are automated tests covering both scenarios (alert dialog and warning log message) to verify that OpenXR initialization failures are handled correctly.
3. **User Feedback:** Consider gathering feedback from users who rely on the alert dialog to ensure that the new behavior meets their needs and does not disrupt their workflow.

## Traceability
Not specified
```