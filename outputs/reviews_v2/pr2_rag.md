```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the handling of data source template variables to use UIDs instead of names for specifying the current value.

## Problem
1. Inconsistent handling of data source UIDs and names in template variables.
2. Potential backward compatibility issues with existing dashboards relying on data source names.
3. Insufficient test coverage for scenarios involving both UIDs and names.

## Evidence
- `public/app/features/plugins/datasource_srv.ts:254-258`: The code now attempts to resolve data sources using both names and UIDs, which could lead to ambiguity if not handled correctly.
- `public/app/features/variables/datasource/reducer.ts:42-47`: The change to use UIDs in the `value` field might break existing dashboards that expect the name.
- `public/app/features/variables/state/actions.test.ts:381-455`: Tests added for UID handling, but scenarios involving mixed UID and name usage are not comprehensively covered.

## Impact
- Existing dashboards that rely on data source names may break if they are not updated to use the new UID-based approach.
- Potential for confusion and errors if both UIDs and names are used interchangeably without clear guidelines.
- Risk of integration issues with other parts of the system that may still expect data source names.

## Recommendation (Fix / Tests / Risks)
1. Ensure backward compatibility by providing a migration path or clear documentation for updating existing dashboards.
2. Expand test coverage to include scenarios where both UIDs and names are used, ensuring consistent behavior.
3. Consider adding logging or warnings when a data source is resolved using a name instead of a UID to aid in debugging.

## Traceability
Not specified
```