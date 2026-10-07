```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a `size` property to the Drawer component, setting width percentage and minWidth, and deprecates the `width` property.

## Problem
1. The deprecation of the `width` property is not fully backward compatible, potentially affecting existing implementations.
2. The new `size` property lacks comprehensive test coverage, especially for edge cases on different screen sizes.
3. The removal of the "expandable" feature is not clearly addressed, which could lead to confusion or incomplete functionality.

## Evidence
- **Deprecation Concerns:** `packages/grafana-ui/src/components/Drawer/Drawer.tsx:45-46` - The `width` property is deprecated without a clear migration path for existing users.
- **Test Coverage:** No new tests are added in `public/app/features/dashboard/components/HelpWizard/HelpWizard.test.tsx` or other related test files to cover the new `size` property.
- **Expandable Feature:** The PR description mentions potentially removing the "expandable" feature, but this is not reflected in the code changes.

## Impact
- **Backward Compatibility:** Existing codebases using the `width` property may break or behave unexpectedly without a clear migration strategy.
- **Functionality Risks:** Without adequate test coverage, the new `size` property might not handle all edge cases, leading to UI issues on various screen sizes.
- **User Confusion:** The unclear status of the "expandable" feature could lead to inconsistent user experiences or incomplete drawer functionality.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility:** Provide a clear migration guide for users transitioning from `width` to `size`, possibly with a deprecation warning.
2. **Test Coverage:** Add comprehensive tests for the `size` property, covering different screen sizes and ensuring consistent behavior.
3. **Feature Clarity:** Clearly decide and document the status of the "expandable" feature, ensuring the code reflects this decision.

## Traceability
- **Code Owners:** Not specified
```