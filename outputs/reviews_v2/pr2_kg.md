```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the handling of data source template variables to use UIDs instead of names for specifying the current value in Grafana dashboards.

## Problem
1. **Backward Compatibility Concerns:** The change from using data source names to UIDs for the `value` field in template variables may break existing dashboards that rely on the previous behavior.
2. **Insufficient Test Coverage for Edge Cases:** While tests have been added, there may be edge cases not covered, particularly around dashboards that dynamically generate or modify data source variables.
3. **Potential Integration Issues:** The change in how data source variables are resolved could impact other parts of the system that expect the `value` to be the data source name.

## Evidence
- **Backward Compatibility:** Changes in `public/app/features/variables/datasource/reducer.ts` (line 47) alter the `value` field from name to UID.
- **Test Coverage:** New tests in `public/app/features/plugins/tests/datasource_srv.test.ts` (lines 191-203) cover some scenarios but may not account for all possible configurations.
- **Integration Concerns:** Modifications in `public/app/features/plugins/datasource_srv.ts` (lines 257-258) change how data source settings are retrieved, potentially affecting other modules that depend on this behavior.

## Impact
- **Technical Impact:** Existing dashboards that use `${datasourceVariable}` to display or use the data source name will break unless updated to `${datasourceVariable:text}`.
- **Risk of Regression:** There is a risk that dashboards relying on the old behavior will not function correctly, leading to user confusion and potential data misinterpretation.
- **Integration Risks:** Other components or plugins that interact with data source variables might experience unexpected behavior due to the change in how values are resolved.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility:** Implement a migration strategy or compatibility layer to handle existing dashboards that use the old format.
2. **Expand Test Coverage:** Add tests for edge cases, such as dashboards with dynamically generated data source variables or those that modify variables at runtime.
3. **Integration Testing:** Conduct thorough integration testing with other components that use data source variables to ensure no unintended side effects occur.

## Traceability
- **Code Owners:** Not specified
```