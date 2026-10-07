# Review Note — Evidence-Anchored

**Scope:** This pull request updates datasource template variables to use datasource UIDs as their internal values, while maintaining display names, and enhances the datasource service to resolve datasources by either name or UID.

## Problem

1.  **Regression for Renamed Datasources in Existing Dashboards:** The updated logic for validating variable selection state (`validateVariableSelectionState`) may cause datasource variables in existing dashboards to incorrectly resolve if the underlying datasource has been renamed. If an existing dashboard's datasource variable was saved with the datasource *name* as its `current.value`, and that datasource is later renamed, the variable will fail to find a matching option by `text` (new name) or `value` (UID). This will cause the variable to fall back to the first available option, leading to unexpected behavior or incorrect data display.

2.  **Incomplete E2E Test Coverage for Migration:** The existing E2E tests cover the new behavior where datasource variable options use UIDs. However, there is no explicit E2E test to verify the backward compatibility for *existing* dashboards where datasource variables were saved with datasource *names* as their values. This leaves a critical upgrade path untested, which could lead to regressions for users upgrading Grafana.

3.  **Misleading Test Helper for Datasource UIDs:** The `getDataSourceInstanceSetting` helper in `public/app/features/variables/shared/testing/helpers.ts` now assigns the `name` directly to the `uid` property. While convenient for some tests, this conflates the distinct concepts of datasource `name` and `uid`. In real-world scenarios, these are separate identifiers, and this helper could lead to less robust tests that don't accurately reflect how datasources are identified and resolved, potentially masking issues where `name` and `uid` are expected to be different.

## Evidence

*   **Regression for Renamed Datasources:**
    *   `public/app/features/variables/datasource/reducer.ts:45`: `options.push({ text: source.name, value: source.uid, selected: false });` (Variable options now store UID as value).
    *   `public/app/features/variables/state/actions.ts:522`: `option = variableInState.options?.find((v: VariableOption) => v.text === text || v.value === value);` (Selection logic prioritizes current text/value matching option text/value).
    *   `public/app/features/variables/state/actions.test.ts`: The new test cases for `validateVariableSelectionState` (lines 381-450) primarily test scenarios where `currentValue` is a UID or matches an existing `text`. It does not explicitly cover a scenario where `currentValue` is an *old name* that no longer matches `v.text` or `v.value` (UID).
    *   `public/app/features/plugins/datasource_srv.ts:257`: `const dsSettings = !Array.isArray(dsValue) && (this.settingsMapByName[dsValue] || this.settingsMapByUid[dsValue]);` (Datasource resolution logic, while flexible, doesn't help `validateVariableSelectionState` find an option if its `value` is an old name).

*   **Incomplete E2E Test Coverage:**
    *   `e2e/dashboards-suite/new-datasource-variable.spec.ts`: This E2E test verifies the *new* behavior of datasource variables using UIDs but does not include a scenario for loading an *existing* dashboard with a datasource variable whose `current.value` is a datasource *name*.
    *   `e2e-playwright/dashboards-suite/new-datasource-variable.spec.ts` (from structural context): This Playwright E2E test also focuses on new behavior.

*   **Misleading Test Helper:**
    *   `public/app/features/variables/shared/testing/helpers.ts:5`: `uid: name,` (Assigns `name` to `uid` in test helper).
    *   `public/app/features/plugins/tests/datasource_srv.test.ts:103`: This test correctly defines `DDDD` with `name: 'DDDD'` and `uid: 'uid-code-DDDD'`, demonstrating the distinction, but the helper change could encourage less rigorous testing elsewhere.

## Impact

1.  **Data Loss/Incorrect Display:** Users with existing dashboards that use datasource template variables might experience their variables defaulting to the first option or an incorrect datasource if the referenced datasource has been renamed since the dashboard was saved. This can lead to dashboards displaying incorrect data or breaking entirely.
2.  **Regression Risk:** Without E2E tests for existing dashboards, there's a higher risk of regressions for a common upgrade scenario, potentially impacting a large number of users.
3.  **Reduced Test Fidelity:** The `getDataSourceInstanceSetting` helper's `uid: name` assignment could lead to tests that pass under false assumptions, as they don't accurately simulate real-world datasource configurations where `name` and `uid` are distinct. This could hide future bugs related to datasource identification.

## Recommendation (Fix / Tests / Risks)

1.  **Fix Renamed Datasource Resolution:**
    *   Modify `public/app/features/variables/state/actions.ts::validateVariableSelectionState` to include a fallback mechanism. If `option` is not found by `v.text === text` or `v.value === value`, attempt to resolve the `getCurrentValue(variableInState)` using `datasource_srv.getInstanceSettings` (which can resolve by name or UID). If `datasource_srv.getInstanceSettings` returns a valid datasource, then find the option in `variableInState.options` whose `value` matches the resolved datasource's `uid`. This ensures that old `current.value` (names) are correctly mapped to new `option.value` (UIDs).

2.  **Add E2E Test for Existing Dashboards:**
    *   Create a new E2E test in `e2e/dashboards-suite/` (e.g., `existing-datasource-variable-migration.spec.ts`) that:
        *   Imports a dashboard JSON file where a datasource variable's `current.value` is explicitly set to a datasource *name* (e.g., "gdev-prometheus").
        *   Verifies that after loading, the variable correctly resolves to the expected datasource (by its UID internally, but displaying its name).
        *   Include a scenario where the datasource is *renamed* in `devenv/datasources.yaml` (e.g., `gdev-prometheus` becomes `gdev-renamed-prometheus`) and verify the variable still resolves correctly based on its original name or UID.

3.  **Refine Test Helper:**
    *   Update `public/app/features/variables/shared/testing/helpers.ts::getDataSourceInstanceSetting` to accept an optional `uid` parameter, defaulting to a generated unique UID if not provided, rather than defaulting to the `name`. This would encourage tests to explicitly define distinct `name` and `uid` when necessary, improving test realism.

## Traceability
Not specified