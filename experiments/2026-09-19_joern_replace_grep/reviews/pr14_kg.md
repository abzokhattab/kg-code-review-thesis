```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a `size` property to the Drawer component, setting width percentage and minWidth, and deprecates the `width` property.

## Problem
1. The deprecation of the `width` property is not fully backward compatible, potentially affecting existing implementations.
2. The new `size` property lacks comprehensive test coverage, especially for edge cases on different screen sizes.
3. The removal of the "expandable" feature is not clearly addressed, which might lead to confusion or incomplete functionality.

## Evidence
- **packages/grafana-ui/src/components/Drawer/Drawer.tsx:45**: The `width` property is deprecated but still used in some instances, which might lead to inconsistent behavior.
- **public/app/features/dashboard/components/HelpWizard/HelpWizard.tsx:75**: The `size` property is used without corresponding test updates to ensure it behaves correctly across different scenarios.
- **packages/grafana-ui/src/components/Drawer/Drawer.tsx:106**: The logic for handling the expandable feature is still present, but its future is uncertain, leading to potential maintenance issues.

## Impact
- **Technical Impact**: The deprecation of the `width` property without a clear migration path could break existing implementations. The lack of test coverage for the `size` property increases the risk of undetected bugs, especially on smaller screens. Uncertainty around the expandable feature could lead to incomplete or inconsistent user experiences.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility**: Provide a clear migration guide for users transitioning from `width` to `size`, ensuring backward compatibility.
2. **Test Coverage**: Enhance test coverage for the `size` property, including edge cases for various screen sizes and scenarios.
3. **Feature Clarity**: Decide on the future of the expandable feature and update the code and documentation accordingly to avoid confusion.

## Traceability
- **Code Owners**: Not specified
```