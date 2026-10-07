```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a feature to lock the multi-value variable options list in Grafana dashboards, preventing custom values from being added.

## Problem
1. Lack of comprehensive test coverage for all variable types that support the new `allowCustomValue` feature.
2. Potential backward compatibility issues with existing dashboards that rely on custom values.
3. Inconsistent handling of the `allowCustomValue` flag across different variable types and components.

## Evidence
- **kinds/dashboard/dashboard_kind.cue:200-202**: Introduction of `allowCustomValue` flag without corresponding tests for all variable types.
- **public/app/features/dashboard-scene/settings/variables/components/AdHocVariableForm.tsx:80-90**: Implementation of the `allowCustomValue` checkbox, but missing tests for edge cases.
- **public/app/features/dashboard-scene/settings/variables/editors/CustomVariableEditor.tsx:25-35**: Handling of `allowCustomValue` in the state, but no migration strategy for existing dashboards.

## Impact
- **Technical Impact**: Without thorough testing, there is a risk of introducing bugs that could affect the stability of dashboards using multi-value variables. Existing dashboards might break if they rely on custom values that are now restricted.
- **User Impact**: Users may experience unexpected behavior if their dashboards previously allowed custom values and now do not, leading to potential data visualization issues.

## Recommendation (Fix / Tests / Risks)
1. **Fix**: Ensure that the `allowCustomValue` flag is consistently applied across all variable types and components.
2. **Tests**: Expand test coverage to include scenarios where `allowCustomValue` is toggled, especially for existing dashboards that might be affected.
3. **Risks**: Implement a migration strategy or warning for users upgrading to this version, highlighting the change in behavior for custom values.

## Traceability
Not specified
```