```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a notification to the Reduce component in Grafana to inform users about the behavior of "Strict Mode" when using the fill(null) function in InfluxQL.

## Problem
1. The notification logic for "Strict Mode" is directly embedded in the component, which could lead to code duplication if similar notifications are needed elsewhere.
2. The notification does not appear to be covered by any automated tests, which could lead to regressions or missed notifications in future updates.

## Evidence
- `public/app/features/expressions/components/Reduce.tsx:30-72`: The logic for displaying the notification is directly within the component, which could be refactored for reusability.
- `public/app/features/expressions/components/Reduce.tsx:66-72`: There is no indication of test coverage for the new notification logic.

## Impact
- **Technical Debt**: Embedding notification logic directly in the component can lead to maintenance challenges and code duplication if similar notifications are needed in other components.
- **Risk of Regression**: Without automated tests, future changes to the component or related logic might inadvertently break the notification feature, leading to user confusion.

## Recommendation (Fix / Tests / Risks)
1. **Refactor**: Consider extracting the notification logic into a separate component or utility function to promote reusability and maintainability.
2. **Add Tests**: Implement unit tests to cover the notification logic, ensuring that it appears under the correct conditions and with the correct content.
3. **Documentation**: Ensure that any changes to the notification logic are reflected in the documentation to aid future developers in understanding the feature.

## Traceability
Not specified
```