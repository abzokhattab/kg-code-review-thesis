```
# Review Note — Evidence-Anchored

**Scope:** This PR replaces an OpenXR initialization failure alert dialog with a warning log message and introduces a project setting to toggle this behavior.

## Problem
1. The new project setting `xr/openxr/startup_alert` is not documented in the user-facing documentation, which could lead to confusion among users.
2. The change introduces a potential silent failure mode if the warning log message is missed, especially in non-interactive environments or automated testing setups.

## Evidence
- `doc/classes/ProjectSettings.xml:2381`: The new project setting `xr/openxr/startup_alert` is added but lacks accompanying documentation for users.
- `modules/openxr/register_types.cpp:114-129`: The alert dialog is replaced with a warning log message, which may not be visible in all environments.

## Impact
- Users may not be aware of the new setting due to lack of documentation, leading to unexpected behavior if they rely on the alert dialog.
- In environments where log messages are not actively monitored, the failure to initialize OpenXR could go unnoticed, potentially causing downstream issues in applications relying on VR functionality.

## Recommendation (Fix / Tests / Risks)
1. **Documentation:** Update the user-facing documentation to include information about the new `xr/openxr/startup_alert` setting, explaining its purpose and usage.
2. **Testing:** Ensure that there are automated tests that verify the behavior of the system when OpenXR fails to initialize, both with the alert enabled and disabled.
3. **Monitoring:** Consider implementing a mechanism to ensure that critical warnings are not missed in non-interactive environments, such as logging to a centralized system or providing an option to escalate warnings to errors in certain contexts.

## Traceability
Not specified
```