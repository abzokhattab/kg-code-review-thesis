# Review Note — Evidence-Anchored

**Scope:** This pull request adds a UI notification within the `Reduce` expression component to inform users about the behavior of "Strict Mode" and updates the component's internal logic to handle the selection of this mode.

## Problem
1.  **Test Gap: Conditional UI Rendering of Strict Mode Notification:** The new `Alert` component, which conditionally displays information about `ReducerMode.Strict`, lacks specific unit or integration tests to verify its correct rendering and visibility based on the selected reducer mode. This could lead to the notification not appearing when expected or appearing incorrectly for other modes.
2.  **Test Gap: `onModeChanged` Logic for Strict Mode:** While the `onModeChanged` function now explicitly handles `ReducerMode.Strict`, there are no dedicated tests to ensure that selecting this mode correctly updates the `ExpressionQuerySettings` via the `onChange` prop. This is crucial for ensuring the expression query executes with the intended strict behavior.
3.  **Integration Risk: Unverified Documentation Link:** The `Alert` component includes a direct link to Grafana documentation. This link's correctness, accessibility, and relevance to the "Strict Mode" behavior described are not verified, posing a risk of user frustration if the link is broken or misleading.

## Evidence
*   **Problem 1 (Conditional UI Rendering):**
    *   `public/app/features/expressions/components/Reduce.tsx:66-84` (Definition of `strictModeNotification` function)
    *   `public/app/features/expressions/components/Reduce.tsx:88` (Rendering of `strictModeNotification` within the `Reduce` component)
    *   No dedicated unit test file for `public/app/features/expressions/components/Reduce.tsx` is listed in "Related Tests".
    *   `e2e-playwright/panels-suite/panelEdit_transforms.spec.ts` (E2E test, but typically not granular enough for conditional UI element rendering verification).
*   **Problem 2 (`onModeChanged` Logic):**
    *   `public/app/features/expressions/components/Reduce.tsx:33-36` (New `case ReducerMode.Strict` within the `onModeChanged` function)
    *   `features/expressions/components/Reduce.tsx::onModeChanged` (The function responsible for updating settings based on mode selection)
    *   `features/expressions/components/Reduce.tsx::onModeChanged → features/expressions/components/Reduce.tsx::onSettingsChanged` (Call graph showing the flow of settings updates)
    *   `packages/grafana-data/src/transformations/fieldReducer.test.ts` and `public/app/plugins/datasource/elasticsearch/hooks/useStatelessReducer.test.tsx` (Related reducer tests, but do not specifically cover the `Reduce.tsx` component's UI interaction with settings).
*   **Problem 3 (Documentation Link):**
    *   `public/app/features/expressions/components/Reduce.tsx:75-81` (Anchor tag with `href="https://grafana.com/docs/grafana/latest/panels-visualizations/query-transform-data/expression-queries/#sum"`)
    *   `public/locales/en-US/grafana.json:2784` (Translation key for the link text)

## Impact
1.  **Problem 1:** Users might not receive critical information about `ReducerMode.Strict` behavior if the notification fails to render, or they might be confused by its presence when other modes are selected, leading to a degraded user experience and potential misinterpretation of data.
2.  **Problem 2:** If the `onModeChanged` function does not correctly propagate the `ReducerMode.Strict` setting, the underlying expression query might not apply the intended strict transformation, leading to incorrect data results without any immediate visual indication to the user.
3.  **Problem 3:** A broken or irrelevant documentation link can lead to user frustration, increase support requests, and undermine the credibility of the in-app guidance provided by the `Alert` component.

## Recommendation (Fix / Tests / Risks)
1.  **Tests (UI Conditional Rendering):** Create a new unit test file `public/app/features/expressions/components/Reduce.test.tsx`. Add tests within this file to:
    *   Assert that the `Alert` component is rendered when `query.settings.mode` is `ReducerMode.Strict`.
    *   Assert that the `Alert` component is *not* rendered when `query.settings.mode` is any other `ReducerMode` (e.g., `ReducerMode.ReplaceNonNumbers`, `ReducerMode.DropNonNumbers`).
2.  **Tests (`onModeChanged` Logic):** In the new `public/app/features/expressions/components/Reduce.test.tsx` file, add a test case that:
    *   Simulates a user selecting `ReducerMode.Strict` via the `Select` component.
    *   Asserts that the `onChange` prop (which is called by `features/expressions/components/Reduce.tsx::onModeChanged`) is invoked with an `ExpressionQuerySettings` object where `mode` is `ReducerMode.Strict`.
3.  **Risk Mitigation (Documentation Link):** Manually verify the documentation link `https://grafana.com/docs/grafana/latest/panels-visualizations/query-transform-data/expression-queries/#sum` to ensure it is active, points to the correct section, and accurately describes the `Reduce Strict mode` behavior, especially concerning `fill(null)` and `NaN` for InfluxQL.

## Traceability
Not specified