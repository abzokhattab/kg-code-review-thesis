```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a feature to lock the options list for multi-value variables in Grafana dashboards, preventing the addition of custom values.

## Problem
1. Lack of comprehensive test coverage for the new `allowCustomValue` feature across all variable types.
2. Potential backward compatibility issues with existing dashboards that rely on custom values.

## Evidence
- `public/app/features/dashboard-scene/settings/variables/components/AdHocVariableForm.tsx:85`: The `allowCustomValue` checkbox is added but lacks tests for all scenarios.
- `public/app/features/dashboard-scene/utils/variables.ts:138`: Defaulting `allowCustomValue` to `true` might not be explicitly tested for backward compatibility.
- `public/app/features/dashboard-scene/settings/variables/editors/CustomVariableEditor.tsx:35`: The state management for `allowCustomValue` is introduced but not thoroughly validated in tests.

## Impact
- **Technical Impact:** If not properly tested, the feature might introduce bugs where custom values are unexpectedly allowed or disallowed, affecting user workflows.
- **Risk:** Existing dashboards that depend on custom values might break if the default behavior changes or if the feature is not correctly integrated.

## Recommendation (Fix / Tests / Risks)
1. **Tests:** Expand test coverage to include scenarios where `allowCustomValue` is toggled for all variable types, ensuring expected behavior.
2. **Backward Compatibility:** Verify that existing dashboards with custom values are not affected by the introduction of this feature.
3. **Documentation:** Update documentation to clearly explain the new feature and its default behavior to users.

## Traceability
Not specified
```