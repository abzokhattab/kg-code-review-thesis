```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the handling of data source template variables to use UIDs instead of names for specifying the current value.

## Problem
1. The change in how data source template variables are represented (using UID instead of name) may break existing dashboards that rely on the previous behavior.
2. Insufficient backward compatibility handling for dashboards that still use the data source name in their JSON configuration.
3. Potential gaps in test coverage for scenarios where both UID and name are used interchangeably.

## Evidence
- `public/app/features/variables/datasource/reducer.ts:45`: The change from using `source.name` to `source.uid` for the `value` field.
- `public/app/features/plugins/datasource_srv.ts:257`: The logic now attempts to resolve data sources by UID, which could lead to issues if UIDs are not consistently used or available.
- `public/app/features/variables/state/actions.test.ts:381-455`: Tests added for scenarios with currentValue specified, but lack of tests for mixed scenarios where both name and UID might be used.

## Impact
- Existing dashboards that expect the data source name to be used as the `value` may break, leading to incorrect data source selections.
- Users may experience unexpected behavior if their dashboards are not updated to use the new UID-based system.
- Potential for increased support requests and user confusion due to the breaking change in behavior.

## Recommendation (Fix / Tests / Risks)
1. Implement a migration strategy or compatibility layer to handle existing dashboards that use data source names.
2. Expand test coverage to include scenarios where both UID and name are used, ensuring backward compatibility.
3. Update documentation to clearly communicate the change and provide guidance on updating existing dashboards.

## Traceability
Not specified
```