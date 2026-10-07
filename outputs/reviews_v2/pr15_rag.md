```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the TimeRangePicker component to replace aria-label selectors with data-testid for E2E testing and updates the close calendar button to an IconButton.

## Problem
1. Inconsistent use of `data-testid` and `aria-label` attributes, which may lead to confusion in test selectors.
2. Potential loss of accessibility due to the removal of `aria-label` attributes without ensuring equivalent accessibility support.
3. Changes in layout and styling (e.g., use of `Stack` component) may affect the visual consistency and user experience.

## Evidence
- `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarHeader.tsx:22`: Replaced `aria-label` with `data-testid` for the close button.
- `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimePickerContent.tsx:116`: Changed `aria-label` to `data-testid` for calendar open button.
- `packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarFooter.tsx:10`: Removed custom styles and replaced with `Stack` component.

## Impact
- **Technical Impact:** The removal of `aria-label` attributes could degrade accessibility for screen readers, potentially violating accessibility standards. The use of `data-testid` is not a substitute for accessibility attributes.
- **User Experience:** Changes in layout using `Stack` may alter the visual appearance and alignment, potentially affecting the user interface consistency.

## Recommendation (Fix / Tests / Risks)
1. **Accessibility:** Ensure that all interactive elements have appropriate `aria-label` or equivalent attributes to maintain accessibility.
2. **Testing:** Verify that all E2E tests are updated to use `data-testid` and ensure they cover all user interactions, especially those affected by layout changes.
3. **Visual Consistency:** Review the visual changes introduced by the `Stack` component to ensure they align with the overall design system and do not introduce regressions.

## Traceability
Not specified
```