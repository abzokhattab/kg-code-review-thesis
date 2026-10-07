```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a `size` property for the Drawer component to set width percentage and minWidth, deprecating the `width` property.

## Problem
1. The deprecation of the `width` property is not fully backward compatible, potentially affecting existing implementations.
2. The removal of the "expandable" feature is not clearly addressed, which might lead to confusion or incomplete functionality.
3. Lack of comprehensive test coverage for the new `size` property and its interaction with existing features.

## Evidence
- `packages/grafana-ui/src/components/Drawer/Drawer.tsx:45`: The `width` property is deprecated but still used in some instances.
- `packages/grafana-ui/src/components/Drawer/Drawer.tsx:74`: The logic for handling the `expandable` feature is still present but not clearly addressed in the context of the new `size` property.
- `public/app/features/dashboard/components/HelpWizard/HelpWizard.tsx:72`: The `size` property is used without additional tests to ensure its behavior is as expected.

## Impact
- Technical debt may increase due to incomplete deprecation of the `width` property, leading to potential bugs or inconsistencies.
- Users might experience unexpected behavior if the "expandable" feature is not properly integrated or removed.
- Insufficient test coverage could result in undetected issues, especially in edge cases or when integrating with other components.

## Recommendation (Fix / Tests / Risks)
1. Ensure backward compatibility by providing a clear migration path or fallback for the deprecated `width` property.
2. Clarify the status of the "expandable" feature and update the documentation and code accordingly.
3. Add comprehensive tests for the new `size` property, including its interaction with other Drawer features and edge cases.

## Traceability
Not specified
```