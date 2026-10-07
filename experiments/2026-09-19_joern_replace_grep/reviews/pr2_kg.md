```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the handling of data source template variables in Grafana dashboards to use UIDs instead of names for specifying the current value.

## Problem
1. **Backward Compatibility Concerns**: The change from using data source names to UIDs for the `value` field in template variables may break existing dashboards that rely on the previous behavior.
2. **Insufficient Test Coverage for Edge Cases**: While tests have been added, there may be insufficient coverage for scenarios where dashboards are migrated from older versions or where data source names and UIDs are not aligned.
3. **Potential Integration Issues**: The change affects multiple components and services that interact with data source variables, which could lead to integration issues if not thoroughly tested.

## Evidence
- **Backward Compatibility**: Changes in `public/app/features/variables/datasource/reducer.ts` (line 47) alter the `value` field from name to UID, which impacts how dashboards are rendered.
- **Test Coverage**: New tests in `public/app/features/plugins/tests/datasource_srv.test.ts` (lines 191-273) cover some scenarios but may not account for all edge cases.
- **Integration Impact**: Modifications in `public/app/features/plugins/datasource_srv.ts` (lines 257-258) and `public/app/features/variables/state/actions.ts` (lines 523-525) indicate changes in core services that could affect other dependent modules.

## Impact
- **Technical Impact**: Existing dashboards that use the data source name in the `value` field may not function correctly without updates, potentially leading to incorrect data source selections.
- **Risk of Breakage**: Dashboards relying on the previous behavior will need to be updated, which could be error-prone and time-consuming for users.
- **Integration Risks**: Changes in core services could lead to unexpected behavior in other parts of the application if not properly integrated and tested.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility Layer**: Implement a compatibility layer that allows dashboards using the old format to continue functioning without modification.
2. **Comprehensive Testing**: Expand test coverage to include scenarios where dashboards are migrated from older versions and where data source names and UIDs are not aligned.
3. **Integration Testing**: Conduct thorough integration testing across all affected components to ensure seamless operation and identify any potential issues early.

## Traceability
- **Code Owners**: Not specified
```