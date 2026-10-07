# Review Note — Evidence-Anchored

**Scope:** This PR introduces a `size` property (`sm`, `md`, `lg`) to the `Drawer` component, which sets percentage-based width and a minimum width, and deprecates the existing `width` prop. It also removes the `inline` prop and updates several existing `Drawer` usages.

## Problem

1.  **Integration Risk: Unhandled `inline` prop removal and `width` prop precedence.**
    The `inline` prop has been removed from `Drawer.tsx` and `Drawer.story.tsx`, and the `getContainer` prop for `RcDrawer` is now hardcoded to `'.main-view'`. This change will break any existing usages of `inline` drawers that are not updated in this PR. Furthermore, the deprecated `width` prop still takes precedence over the new `size` prop if both are provided, or if `width` is still used without `size`. This can lead to unexpected behavior if consumers migrate partially or expect `size` to always apply.

2.  **Documentation and Implementation Discrepancies for `size` prop.**
    The `Drawer.mdx` documentation for the `size` prop specifies `width` in `vh` units (viewport height), e.g., `sm: width = 25vh`. However, the implementation in `Drawer.tsx` uses `vw` units (viewport width), e.g., `width: '25vw'`. Additionally, the `min-width` value for the `md` size is documented as `568px` in `Drawer.mdx` but implemented as `theme.spacing(66)` (which is `528px` assuming `theme.spacing(1)` is 8px) in `Drawer.tsx`.

3.  **Incomplete Test Coverage for New `size` Prop and Implicit Changes.**
    The new `size` prop's behavior (percentage width, min-width, and media queries) is not explicitly tested. Several existing `Drawer` usages (e.g., `InspectContent`, `SaveDashboardDrawer`) had their `width` prop removed and now implicitly default to `size="md"`. This change in behavior is not explicitly verified in their respective test files. The removal of the `InLine` story from `Drawer.story.tsx` also removes a visual test for inline drawers.

## Evidence

*   **Problem 1 (Inline/Width Precedence):**
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:29`: The `inline?: boolean;` prop is removed from the `Props` interface.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:60`: `inline = false` is removed from the component's prop destructuring.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:69`: `getContainer={inline ? undefined : 'body'}` is changed to `getContainer={'.main-view'}`, removing the dynamic container logic.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:64`: `fixedWidth = isExpanded ? '100%' : width ?? '';` shows that if `width` is provided, it will be used.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:65`: `const rootClass = cx(styles.drawer, !fixedWidth && styles.sizes[size]);` indicates that `styles.sizes[size]` (which applies the `size` prop's styling) is only applied if `fixedWidth` is falsy (i.e., `width` is `undefined`, `null`, or an empty string).
    *   `packages/grafana-ui/src/components/Drawer/Drawer.story.tsx:142-169`: The `InLine` story is completely removed.
    *   **Structural Context:** Callers like `public/app/core/components/AppChrome/News/NewsDrawer.tsx`, `public/app/core/components/AppChrome/TopBar/ProfileButton.tsx`, `public/app/features/inspector/InspectJSONTab.tsx`, `public/app/features/dashboard/components/Inspector/PanelInspector.tsx`, and `public/app/features/dashboard/components/HelpWizard/utils.ts` are not updated in the diff and may still be using the `width` or `inline` props.

*   **Problem 2 (Doc/Impl Discrepancies):**
    *   `packages/grafana-ui/src/components/Drawer/Drawer.mdx:26-28`: Documents `width = 25vh`, `50vh`, `75vh` for `sm`, `md`, `lg` respectively.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:170`, `177`, `184`: Implements `width: '25vw'`, `50vw`, `75vw` respectively.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.mdx:27`: Documents `md: ... min-width = 568px`.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.tsx:179`: Implements `minWidth: theme.spacing(66)` (which is `528px`).

*   **Problem 3 (Incomplete Test Coverage):**
    *   `packages/grafana-ui/src/components/Drawer/Drawer.story.tsx`: No new stories or explicit tests are added to verify the `size` prop's `width`, `min-width`, or media query behavior.
    *   `packages/grafana-ui/src/components/Drawer/Drawer.story.tsx:142-169`: The `InLine` story is removed, eliminating visual testing for this scenario.
    *   `public/app/features/dashboard/components/Inspector/InspectContent.tsx:68`: The `width="50%"` prop is removed, implicitly defaulting to `size="md"`.
    *   `public/app/features/dashboard/components/SaveDashboard/SaveDashboardDrawer.tsx:131`: The `width={'40%'}` prop is removed, implicitly defaulting to `size="md"`.
    *   **Structural Context:** `public/app/features/dashboard/components/SaveDashboard/SaveDashboardDrawer.test.tsx`, `public/app/features/dashboard-scene/saving/SaveDashboardDrawer.test.tsx`, `public/app/features/dashboard/components/HelpWizard/HelpWizard.test.tsx`, and `public/app/features/dashboard-scene/inspect/HelpWizard/HelpWizard.test.tsx` do not appear to contain specific assertions for the drawer's width or size behavior after these changes. `e2e-playwright/various-suite/inspect-drawer.spec.ts` could be affected by the implicit size change of `InspectContent`.

## Impact

*   **Problem 1:** Existing drawers using the `inline` prop will no longer render correctly or might break entirely, as `getContainer` is now fixed to `'.main-view'`. If a consumer provides both `width` and `size`, the `width` will silently override the `size` behavior, leading to confusion and unexpected styling. If a consumer provides `width` but no `size`, the `size` prop's new responsive behavior (min-width, media queries) will not be applied, potentially leading to poor scaling on smaller screens, which this PR aims to fix.
*   **Problem 2:** Misleading documentation will cause developers to have incorrect expectations about the drawer's behavior, leading to frustration and incorrect usage. The `md` size will be slightly narrower than documented, potentially affecting layout.
*   **Problem 3:** Regressions in drawer sizing, especially on different screen sizes or when `min-width` thresholds are hit, might go unnoticed. The implicit change to `size="md"` for `InspectContent` and `SaveDashboardDrawer` might introduce unintended layout shifts or usability issues that are not caught by existing tests. Lack of visual or functional tests for the `inline` prop's removal could lead to undetected breakage in components that previously relied on it.

## Recommendation (Fix / Tests / Risks)

1.  **Address `inline` prop removal and `width` precedence:**
    *   **Fix:** Re-evaluate the removal of the `inline` prop. If it's truly no longer supported, ensure a comprehensive migration plan or a clear error/warning for its usage. If it's intended to be replaced by a different mechanism, document it.
    *   **Fix:** Modify the logic in `packages/grafana-ui/src/components/Drawer/Drawer.tsx` so that the `size` prop takes precedence if both `width` and `size` are provided, or at least emit a console warning if both are used.
    *   **Risk Mitigation:** Explicitly check the following callers for `inline` or `width` usage and update them as necessary: `public/app/core/components/AppChrome/News/NewsDrawer.tsx`, `public/app/core/components/AppChrome/TopBar/ProfileButton.tsx`, `public/app/features/inspector/InspectJSONTab.tsx`, `public/app/features/dashboard/components/Inspector/PanelInspector.tsx`, and `public/app/features/dashboard/components/HelpWizard/utils.ts`.

2.  **Correct documentation and implementation discrepancies:**
    *   **Fix:** Update `packages/grafana-ui/src/components/Drawer/Drawer.mdx` to correctly state `vw` units for width instead of `vh`.
    *   **Fix:** Align the `min-width` value for `md` size in `packages/grafana-ui/src/components/Drawer/Drawer.tsx` to match the documented `568px`, or update the documentation to reflect the implemented `528px`.

3.  **Enhance test coverage:**
    *   **Tests:** Enhance `packages/grafana-ui/src/components/Drawer/Drawer.story.tsx` with new stories for each `size` (`sm`, `md`, `lg`) and include scenarios that demonstrate the `min-width` behavior and media query responsiveness. Consider adding a dedicated unit test file for `Drawer.tsx` to assert computed styles for different `size` props and viewport widths.
    *   **Tests:** Update `public/app/features/dashboard/components/SaveDashboard/SaveDashboardDrawer.test.tsx` and `public/app/features/dashboard/components/HelpWizard/HelpWizard.test.tsx` to include assertions that verify the drawer's width/size behavior now that they implicitly default to `size="md"` or explicitly use `size="lg"`.
    *   **Tests:** Review `e2e-playwright/various-suite/inspect-drawer.spec.ts` to ensure it covers the visual layout and responsiveness of the `InspectContent` drawer, which now defaults to `size="md"`.
    *   **Tests:** If the `inline` prop is truly removed, add a test that explicitly fails if `inline` is passed to `Drawer` to prevent future accidental usage.

## Traceability
Not specified