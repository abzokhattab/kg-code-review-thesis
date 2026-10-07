# Review Note — Evidence-Anchored

**Scope:** This PR introduces an `allowCustomValue` option for dashboard variables, allowing users to control whether custom values can be entered into variable selection lists.

## Problem

1.  **Integration Risk: Lack of Runtime Enforcement for `allowCustomValue` in Variable Selection UI:** The PR introduces the `allowCustomValue` setting in the variable model and its editor forms, but it does not include any logic to enforce this setting in the actual variable value selection UI (e.g., dropdowns, text inputs). If `allowCustomValue` is set to `false`, users can still potentially type in or select values not present in the predefined options, rendering the setting ineffective at runtime. This creates a discrepancy between configuration and behavior.
2.  **Test Gap: Missing URL Synchronization Tests for `allowCustomValue`:** The new `allowCustomValue` property is not explicitly tested for its impact on URL synchronization. Variables are often synchronized with URL parameters, and it's crucial to ensure that this new property does not interfere with how variable values (especially custom ones) are encoded, decoded, and applied via the URL.
3.  **Correctness/Consistency: `allowCustomValue` Applied to All Variable Types Without UI Control:** The schema change adds `allowCustomValue` to the base `VariableModel`, meaning all variable types (including `IntervalVariable`, `ConstantVariable`, `TextBoxVariable`) will inherit this property and default to `true`. However, the UI forms for `IntervalVariable`, `ConstantVariable`, and `TextBoxVariable` do not expose this setting, leading to an implicit `allowCustomValue: true` that cannot be configured by the user. This could be confusing or unintended if these variable types should not support custom values.

## Evidence

*   **Problem 1 (Runtime Enforcement):**
    *   The diff shows additions of `allowCustomValue` to `VariableModel` (packages/grafana-schema/src/raw/dashboard/x/dashboard_types.gen.ts:130), `AdHocVariableModel` (packages/grafana-data/src/types/templateVars.ts:70), and `VariableWithMultiSupport` (packages/grafana-data/src/types/templateVars.ts:127).
    *   UI components like `AdHocVariableForm.tsx`, `CustomVariableForm.tsx`, `DataSourceVariableForm.tsx`, `QueryVariableForm.tsx`, and `SelectionOptionsForm.tsx` include a `VariableCheckboxField` for `allowCustomValue`.
    *   However, there are no changes in the diff to the actual variable value selection components (e.g., `VariableSelectField`, `VariableTextField`, or any logic within `public/app/features/variables/`) that would disable input or prevent selection of non-listed values based on the `allowCustomValue` flag.
*   **Problem 2 (URL Synchronization Tests):**
    *   The `allowCustomValue` property is added to the `VariableModel` and `SceneVariable` states.
    *   The related test file `public/app/features/variables/state/templateVarsChangedInUrl.test.ts` is listed in the knowledge graph but is not modified in this PR. This test suite is critical for verifying URL synchronization behavior.
    *   The `sceneVariablesSetToVariables` function (public/app/features/dashboard-scene/serialization/sceneVariablesSetToVariables.ts:74) correctly serializes `allowCustomValue` into the dashboard model, but its interaction with URL parameters is not covered.
*   **Problem 3 (Consistency Across Variable Types):**
    *   The `allowCustomValue` field is added to the base `VariableModel` interface (packages/grafana-schema/src/raw/dashboard/x/dashboard_types.gen.ts:130) and `defaultVariableModel` (packages/grafana-schema/src/raw/dashboard/x/dashboard_types.gen.ts:194) sets its default to `true`.
    *   The `createSceneVariableFromVariableModel` function (public/app/features/dashboard-scene/utils/variables.ts:138) applies `variable.allowCustomValue ?? true` to `AdHocFiltersVariable`, `CustomVariable`, `QueryVariable`, and `DataSourceVariable`.
    *   However, there are no corresponding UI changes or tests for `IntervalVariable`, `ConstantVariable`, or `TextBoxVariable` forms (e.g., `public/app/features/dashboard-scene/settings/variables/components/IntervalVariableForm.tsx` or `public/app/features/dashboard-scene/settings/variables/components/TextBoxVariableForm.tsx` which are not in the diff) to expose this setting.

## Impact

1.  **Broken User Experience / Misleading Configuration:** Users might configure `allowCustomValue: false` expecting to restrict input, but find that they can still enter custom values, leading to confusion and potential data integrity issues if downstream systems rely on variable values being from a predefined list.
2.  **Data Loss / Incorrect State:** If custom values are entered when `allowCustomValue` is `false`, and these values are then synchronized to the URL, there's a risk that upon reloading the dashboard, the variable state might be incorrect or lead to unexpected behavior if the variable system attempts to validate against `allowCustomValue`. This could lead to dashboards loading with incorrect filters or queries.
3.  **Inconsistent Behavior / Unintended Defaults:** `Interval`, `Constant`, and `TextBox` variables will implicitly allow custom values (due to the `true` default) without any UI control. This might not align with the intended behavior for these variable types and could lead to unexpected flexibility where none was desired or configured.

## Recommendation (Fix / Tests / Risks)

1.  **Fix:** Implement runtime enforcement for `allowCustomValue` in the variable value selection UI.
    *   Modify the components responsible for rendering variable dropdowns/inputs (e.g., `VariableSelectField`, `VariableTextField` in `public/app/features/variables/`) to disable or prevent custom input when the associated variable's `allowCustomValue` property is `false`.
    *   Consider how this interacts with `public/app/features/dashboard/containers/DashboardPage.tsx` which orchestrates variable rendering.
2.  **Tests:** Add specific test cases to cover URL synchronization for `allowCustomValue`.
    *   In `public/app/features/variables/state/templateVarsChangedInUrl.test.ts`, add scenarios where a variable with `allowCustomValue: false` has a custom value in the URL, and verify that it's handled gracefully (e.g., ignored, reset to default, or an error is shown).
    *   Also, test scenarios where `allowCustomValue: true` and a custom value is correctly serialized to and deserialized from the URL.
3.  **Fix / Tests:** Address the consistency of `allowCustomValue` across all variable types.
    *   **Option A (Fix):** If `allowCustomValue` is truly applicable to `Interval`, `Constant`, and `TextBox` variables, add the `VariableCheckboxField` to their respective editor forms (e.g., `public/app/features/dashboard-scene/settings/variables/components/IntervalVariableForm.tsx`).
    *   **Option B (Fix):** If `allowCustomValue` is *not* applicable to these types, remove `allowCustomValue` from the base `VariableModel` and instead add it only to the specific variable types that support it (e.g., `QueryVariableModel`, `CustomVariableModel`, `DataSourceVariableModel`, `AdHocVariableModel`) in `packages/grafana-data/src/types/templateVars.ts`. This would require adjusting the `dashboard_kind.cue` and generated schema.
    *   Add tests to verify the behavior for these variable types, regardless of the chosen option.

## Traceability

Not specified