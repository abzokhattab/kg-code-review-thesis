```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a notification to the Reduce component in Grafana to inform users about the behavior of the fill(null) function in InfluxQL when "Strict Mode" is selected.

## Problem
1. The notification logic for "Strict Mode" is directly embedded in the component, which could lead to code duplication if similar notifications are needed elsewhere.
2. The current implementation does not include any automated tests to verify the behavior of the new notification feature.
3. The documentation link in the notification is hardcoded, which could lead to maintenance issues if the documentation URL changes.

## Evidence
- `public/app/features/expressions/components/Reduce.tsx:31-45`: The logic for displaying the notification is directly within the component.
- `public/app/features/expressions/components/Reduce.tsx:66-72`: The notification is conditionally rendered based on the mode.
- No changes in test files related to the Reduce component were found in the diff.

## Impact
- **Technical Debt:** Embedding notification logic directly in the component can lead to code duplication and maintenance challenges if similar notifications are needed in other components.
- **Lack of Test Coverage:** Without tests, there's a risk that future changes could break this feature without detection.
- **Maintenance Risk:** Hardcoded URLs can become outdated, leading to broken links and a poor user experience.

## Recommendation (Fix / Tests / Risks)
1. **Refactor Notification Logic:** Consider extracting the notification logic into a separate component or utility function to promote reusability and reduce duplication.
2. **Add Tests:** Implement unit tests for the Reduce component to ensure the notification is displayed correctly when "Strict Mode" is selected.
3. **Use Configurable URLs:** Store the documentation URL in a configuration file or environment variable to facilitate easier updates in the future.

## Traceability
Not specified
```