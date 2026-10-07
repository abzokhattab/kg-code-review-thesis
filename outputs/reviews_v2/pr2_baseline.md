```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the handling of data source template variables in Grafana dashboards to use UIDs instead of names for specifying the current value.

## Problem
1. Lack of backward compatibility for dashboards relying on data source names.
2. Insufficient test coverage for scenarios involving legacy dashboards.
3. Potential confusion due to changes in how data source variables are interpolated.

## Evidence
- `public/app/features/plugins/datasource_srv.ts:257-258`: The code now checks for UIDs in addition to names, which could break existing dashboards that rely solely on names.
- `public/app/features/variables/datasource/reducer.ts:45`: The change to use UIDs in the `value` field may not be backward compatible with dashboards that expect names.
- `e2e/dashboards-suite/new-datasource-variable.spec.ts:41`: The test checks for UID usage but does not cover scenarios where dashboards might still use names.

## Impact
- Existing dashboards that rely on data source names for template variables may break or behave unexpectedly.
- Users may experience confusion due to changes in variable interpolation, potentially leading to incorrect data being displayed.
- The risk of introducing bugs in dashboards that have not been updated to use the new UID-based system.

## Recommendation (Fix / Tests / Risks)
1. Implement a fallback mechanism to ensure backward compatibility with dashboards using data source names.
2. Expand test coverage to include scenarios with legacy dashboards that use names instead of UIDs.
3. Update documentation to clearly explain the changes and guide users on how to update their dashboards.

## Traceability
Not specified
```