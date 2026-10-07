```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external code that relies on this class if it's not intended to be internal.
2. Lack of clarity on whether the change requires updates to documentation or external dependencies that might use this class.

## Evidence
- `packages/grafana-data/src/events/types.ts:44`: The class `BusEventWithPayload` has been renamed to `BusEventWithPayloadInternal`.

## Impact
- If `BusEventWithPayload` is used externally, renaming it could break existing integrations or plugins that depend on this class.
- Without proper documentation or communication, users of the API might face unexpected errors or require urgent fixes on their end.

## Recommendation (Fix / Tests / Risks)
1. Verify if `BusEventWithPayload` is used externally and assess the impact of this change on external codebases.
2. Update any relevant documentation to reflect the change in class name.
3. Consider adding a deprecation notice for `BusEventWithPayload` if it is being phased out, providing users with a transition period.

## Traceability
- Code ownership is likely under the Grafana data team, but specific owners are not specified.
```