# Review Note — Evidence-Anchored

**Scope:** This PR introduces a new project setting (`xr/openxr/startup_alert`) to control whether an operating system alert dialog is displayed when OpenXR initialization fails, replacing the unconditional alert with a warning log message and an optional alert.

## Problem
1.  **Untested Conditional Logic and Project Setting:** The new `xr/openxr/startup_alert` project setting and its conditional logic for displaying the OS alert are not covered by automated tests. This introduces a risk of regressions or unexpected behavior if the setting is misconfigured or the logic changes.
2.  **Potential for Blocking in Headless/CLI Environments:** While the PR aims to improve developer workflow by making the alert optional, the default value for `xr/openxr/startup_alert` is `true`. This means that in headless or command-line interface (CLI) environments, where `OS::get_singleton()->alert` can be problematic (e.g., blocking execution, failing to display), the alert will still be shown by default, potentially hindering automated processes or server deployments.

## Evidence
*   **modules/openxr/register_types.cpp:113-122:** Contains the new conditional logic `if (init_show_startup_alert) { OS::get_singleton()->alert(init_error_message); }` which is not covered by tests.
*   **main/main.cpp:1830:** Defines the default value for the new setting as `GLOBAL_DEF_BASIC("xr/openxr/startup_alert", true);`.
*   **Structural Context - Absence of Test Files:** The provided knowledge graph context does not list any test files that would cover the `modules/openxr/register_types.cpp` changes or the `xr/openxr/startup_alert` setting.
*   **Structural Context - `main.cpp::is_cmdline_tool`:** This function indicates the presence of CLI/headless execution paths where an `OS::get_singleton()->alert` could be disruptive.

## Impact
*   **Regression Risk:** Without tests, future changes to OpenXR initialization or project settings could inadvertently break the intended behavior of the `startup_alert` setting, leading to either always-on or always-off alerts, or incorrect logging.
*   **Developer Workflow Disruption:** In automated build systems, CI/CD pipelines, or server deployments that might attempt to initialize OpenXR (even if unintentionally), the default `true` setting could still cause `OS::get_singleton()->alert` to block execution or cause failures, negating part of the PR's intended benefit for non-interactive environments.
*   **Untested User Experience:** The user experience of configuring and observing the `startup_alert` setting remains untested, potentially leading to confusion or unexpected behavior for users.

## Recommendation (Fix / Tests / Risks)
1.  **Add Automated Tests:**
    *   Create a new test file (e.g., `tests/test_openxr_settings.cpp`) or extend an existing relevant test suite.
    *   Add a test case that sets `xr/openxr/startup_alert` to `false` and verifies that `OS::get_singleton()->alert` is *not* called when `openxr_api->initialize` fails within `initialize_openxr_module`.
    *   Add another test case that sets `xr/openxr/startup_alert` to `true` and verifies that `OS::get_singleton()->alert` *is* called under the same failure conditions.
    *   Verify that `WARN_PRINT` is always called regardless of the setting.
2.  **Re-evaluate Default Setting for Headless/CLI:**
    *   Consider changing the default value of `xr/openxr/startup_alert` to `false` in `main/main.cpp:1830` to prioritize non-blocking behavior, especially for automated workflows.
    *   Alternatively, within `modules/openxr/register_types.cpp`, add an explicit check for headless mode (e.g., `if (OS::get_singleton()->is_headless() || Main::is_cmdline_tool())`) and suppress the `OS::get_singleton()->alert` regardless of the `startup_alert` setting if in such a mode. This would ensure that `OS::get_singleton()->alert` is never called in non-interactive contexts.

## Traceability
Not specified