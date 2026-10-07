```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a feature to lock the options list for multi-value variables in dashboards, preventing the addition of custom values.

## Problem
1. Lack of comprehensive test coverage for the new `allowCustomValue` feature across all variable types.
2. Potential inconsistency in handling the `allowCustomValue` property across different variable types and forms.
3. Absence of documentation updates to reflect the new feature and its implications.

## Evidence
- `public/app/features/dashboard-scene/settings/variables/components/AdHocVariableForm.tsx:85`: The `allowCustomValue` checkbox is conditionally rendered, but not all forms have corresponding tests.
- `public/app/features/dashboard-scene/settings/variables/components/CustomVariableForm.test.tsx:42`: Tests for `allowCustomValue` are present but not exhaustive across all variable types.
- `public/app/features/dashboard-scene/settings/variables/editors/AdHocFiltersVariableEditor.tsx:39`: The `allowCustomValue` state is set, but its integration with other components is not fully tested.

## Impact
- Incomplete test coverage could lead to undetected bugs when users interact with the new feature, especially across different variable types.
- Inconsistent handling of the `allowCustomValue` property might result in unexpected behavior or UI inconsistencies.
- Users may be unaware of the new feature or how to use it effectively without updated documentation.

## Recommendation (Fix / Tests / Risks)
1. Expand test coverage to include all variable types and ensure the `allowCustomValue` feature is consistently tested.
2. Review and ensure consistent handling of the `allowCustomValue` property across all relevant components and forms.
3. Update the documentation to include details about the new feature, its default behavior, and how users can configure it.

## Traceability
Not specified
```