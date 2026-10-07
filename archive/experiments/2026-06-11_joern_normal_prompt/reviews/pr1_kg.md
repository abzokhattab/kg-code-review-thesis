```
# Review Note — Evidence-Anchored

**Scope:** This PR replaces the OpenXR operating system alert dialog with a warning log message and adds a project setting to control the alert display.

## Problem
1. The new project setting `xr/openxr/startup_alert` is added but lacks documentation or user guidance.
2. The change introduces a potential silent failure mode if the warning log is missed by users, especially if the alert is disabled.

## Evidence
- `doc/classes/ProjectSettings.xml:2381`: Addition of `xr/openxr/startup_alert` setting without accompanying documentation.
- `modules/openxr/register_types.cpp:114-126`: Replacement of the alert dialog with a warning log message and conditional alert based on the new setting.

## Impact
- Users may not be aware of the new setting due to lack of documentation, leading to confusion or missed configuration opportunities.
- If the alert is disabled, users might not notice critical initialization failures, potentially leading to runtime issues without clear diagnostics.

## Recommendation (Fix / Tests / Risks)
1. **Documentation:** Add detailed documentation for the `xr/openxr/startup_alert` setting, explaining its purpose and usage.
2. **User Feedback:** Consider adding a more prominent notification mechanism when the alert is disabled, such as a console message or a log entry at a higher verbosity level.
3. **Testing:** Ensure there are tests verifying both the alert and warning log behaviors, especially under different configurations of the new setting.

## Traceability
Not specified
```