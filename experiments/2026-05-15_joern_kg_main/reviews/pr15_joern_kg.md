# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `TimeRangePicker` component to use `data-testid` for E2E selectors, updates the calendar's close button to an `IconButton`, and makes associated styling adjustments.

## Problem

1.  **Widespread E2E Test Failures Due to Unupdated Selectors:** The core purpose of this PR is to change E2E selectors from `aria-label` to `data-testid`. While the selector definitions in `packages/grafana-e2e-selectors` and some unit tests are updated, numerous critical E2E Playwright tests are listed as dependent but are not updated in the diff. These tests will likely fail because they are still attempting to locate elements using the old `aria-label` attributes, which have been removed or changed in the component implementation.
2.  **Incomplete Internationalization (i18n) for New UI Strings:** New user-facing strings for the calendar's close button tooltip and the input calendar's open button `aria-label` have been introduced. While English and pseudo-locales are updated, several other key locales have empty translations, leading to a degraded user experience for non-English users.
3.  **Potential Visual Regressions and Missing Test Coverage for Calendar UI Changes:** The PR includes significant refactoring of the calendar's styling and component structure, including the removal of `useStyles2` and a "lmao" comment indicating a hardcoded pixel adjustment. The change from a generic `Button` to an `IconButton` in the calendar header also introduces styling and accessibility considerations that may not be fully covered by existing tests.

## Evidence

*   **Problem 1 (E2E Test Failures):**
    *   `packages/grafana-e2e-selectors/src/selectors/components.ts`: Changes `TimePicker.fromField`, `TimePicker.toField`, `TimePicker.calendar.label`, `TimePicker.calendar.openButton`, and `TimePicker.calendar.closeButton` from `aria-label` to `data-testid` values.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimeRangeContent.tsx:113`: Changes `aria-label={selectors.components.TimePicker.calendar.openButton}` to `data-testid={selectors.components.TimePicker.calendar.openButton}`.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimeRangeContent.tsx:130`: Changes `aria-label={selectors.components.TimePicker.fromField}` to `data-testid={selectors.components.TimePicker.fromField}`.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarHeader.tsx:20`: Changes `aria-label={selectors.components.TimePicker.calendar.closeButton}` to `data-testid={selectors.components.TimePicker.calendar.closeButton}`.
    *   **Structural Context:** `e2e-playwright/various-suite/explore.spec.ts`, `e2e-playwright/various-suite/navigation.spec.ts`, `e2e-playwright/various-suite/keybinds.spec.ts`, `e2e-playwright/various-suite/prometheus-config.spec.ts`, `e2e-playwright/various-suite/solo-route.spec.ts`, `e2e-playwright/various-suite/loki-table-explore-to-dash.spec.ts`, `e2e-playwright/various-suite/return-to-previous.spec.ts`, `e2e-playwright/various-suite/prometheus-variable-editor.spec.ts`, `e2e-playwright/various-suite/verify-i18n.spec.ts` are listed as files that depend on these changes but are not updated in the diff. These E2E tests likely call components like `TimeRangeContent` and `TimePickerCalendar` and will fail to find elements.
*   **Problem 2 (Incomplete i18n):**
    *   `public/locales/de-DE/grafana.json:1249`, `public/locales/es-ES/grafana.json:1255`, `public/locales/fr-FR/grafana.json:1255`, `public/locales/zh-Hans/grafana.json:1243`: The new i18n keys `time-picker.calendar.close` and `time-picker.range-content.open-input-calendar` are added with empty string values.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarHeader.tsx:20`: Uses `tooltip={t('time-picker.calendar.close', 'Close calendar')}`.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimeRangeContent.tsx:113`: Uses `aria-label={t('time-picker.range-content.open-input-calendar', 'Open calendar')}`.
*   **Problem 3 (Visual Regressions/Missing Tests):**
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarFooter.tsx`: Removes `useStyles2(getFooterStyles)`.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarHeader.tsx`: Removes `useStyles2(getHeaderStyles)` and changes `Button` to `IconButton`.
    *   `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimePickerCalendar.tsx:22`: Contains the comment `// lmao` next to a hardcoded pixel value `546px` for positioning, indicating a potentially fragile styling solution.
    *   **Structural Context:** `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimePickerCalendar.test.tsx` is a related test file but is not included in the diff, suggesting that specific tests for these UI/styling changes might be missing.

## Impact

*   **Problem 1:** This will lead to widespread E2E test failures across the Grafana application, blocking CI/CD pipelines and potentially allowing critical regressions in time range selection functionality to go undetected in production.
*   **Problem 2:** Users interacting with Grafana in `de-DE`, `es-ES`, `fr-FR`, or `zh-Hans` locales will see untranslated text for the calendar close button tooltip and the "Open calendar" `aria-label` for the time range input fields, leading to a poor and inconsistent user experience.
*   **Problem 3:** The significant styling and component changes, particularly the hardcoded pixel values and the `IconButton` integration, introduce a high risk of visual regressions in the TimeRangePicker calendar. Without dedicated tests in `TimePickerCalendar.test.tsx`, these regressions could break the layout or user interaction, especially across different screen sizes, themes, or future component updates.

## Recommendation (Fix / Tests / Risks)

1.  **Update E2E Playwright Tests:**
    *   Update all relevant E2E Playwright tests in `e2e-playwright/various-suite/*.spec.ts` (e.g., `explore.spec.ts`, `navigation.spec.ts`, `keybinds.spec.ts`) to use the new `data-testid` selectors defined in `packages/grafana-e2e-selectors/src/selectors/components.ts`.
    *   Ensure that any `getByLabelText` calls in these E2E tests are updated to use the new `aria-label` values (e.g., 'From', 'To', 'Open calendar', 'Close calendar') where `data-testid` is not applicable or `aria-label` is still used for accessibility (e.g., in `TimeRangeContent.tsx` for the calendar open button).
2.  **Complete i18n Translations:**
    *   Provide appropriate translations for the new i18n keys `time-picker.calendar.close` and `time-picker.range-content.open-input-calendar` in `public/locales/de-DE/grafana.json`, `public/locales/es-ES/grafana.json`, `public/locales/fr-FR/grafana.json`, and `public/locales/zh-Hans/grafana.json`.
3.  **Enhance Calendar UI Test Coverage and Review Styling:**
    *   Add specific unit tests to `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimePickerCalendar.test.tsx` to verify the rendering, styling, and interaction of the `IconButton` in `CalendarHeader` and the overall layout of the calendar. These tests should cover both the `isFullscreen` (tooltip) and modal display modes.
    *   Review the styling adjustments in `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimePickerCalendar.tsx` (specifically the `546px` value) to ensure they are robust, responsive, and not prone to breaking with future changes or different screen sizes. Consider using more flexible layout methods (e.g., Flexbox, Grid, or theme-based spacing) instead of hardcoded pixel values.

## Traceability

Not specified