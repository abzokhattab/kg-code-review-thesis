```
# Review Note — Evidence-Anchored

**Scope:** This PR adds a notification to the Reduce component in Grafana to inform users about the behavior of "Strict Mode" when using the fill(null) function in InfluxQL.

## Problem
1. Lack of test coverage for the new notification feature.
2. Potential user confusion due to insufficient context or guidance in the notification message.

## Evidence
- **public/app/features/expressions/components/Reduce.tsx:31-45**: The `onModeChanged` function is modified to handle `ReducerMode.Strict`, but there are no corresponding tests to verify this behavior.
- **public/app/features/expressions/components/Reduce.tsx:66-72**: The `strictModeNotification` function is introduced to display an alert, but there is no test to ensure it renders correctly under different conditions.

## Impact
- Without tests, there is a risk that future changes could break the notification feature without detection.
- Users might not fully understand the implications of "Strict Mode" if the notification lacks clarity or context, leading to potential misconfigurations or unexpected results.

## Recommendation (Fix / Tests / Risks)
1. **Add Unit Tests**: Implement unit tests for the `onModeChanged` and `strictModeNotification` functions to ensure they behave as expected.
2. **Enhance Notification Content**: Consider providing more detailed guidance or examples in the notification to help users understand the impact of "Strict Mode" and how to address NaN results.
3. **Documentation Update**: Ensure that the documentation linked in the notification is comprehensive and up-to-date to prevent user confusion.

## Traceability
Not specified
```