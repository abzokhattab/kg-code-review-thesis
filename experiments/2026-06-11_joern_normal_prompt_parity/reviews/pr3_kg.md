```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a notification to the Reduce component in Grafana to inform users about the behavior of "Strict Mode" when using the fill(null) function in InfluxQL.

## Problem
1. Lack of test coverage for the new notification feature.
2. Potential user confusion due to insufficient documentation linkage or explanation within the notification.

## Evidence
- **public/app/features/expressions/components/Reduce.tsx:31-45**: The `onModeChanged` function is modified to handle `ReducerMode.Strict`, but there are no corresponding tests to verify this behavior.
- **public/app/features/expressions/components/Reduce.tsx:66-72**: The `strictModeNotification` function is introduced to display an alert, but there is no test to ensure it renders correctly under different conditions.

## Impact
- Without tests, there is a risk that future changes could break the notification feature without detection.
- Users might not fully understand the implications of "Strict Mode" if the notification does not provide enough context or if the documentation link is not prominently highlighted.

## Recommendation (Fix / Tests / Risks)
1. **Add Unit Tests**: Implement unit tests for the `onModeChanged` and `strictModeNotification` functions to ensure they behave as expected.
2. **Enhance Documentation**: Consider adding more detailed information or examples in the notification to help users understand the impact of "Strict Mode" beyond just linking to external documentation.
3. **User Feedback**: Gather user feedback on the clarity and usefulness of the notification to ensure it meets user needs.

## Traceability
Not specified
```