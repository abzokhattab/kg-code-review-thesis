```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors code to replace usages of `StringUtils#capitalize` and `StringUtils#uncapitalize` with standard Java methods, aiming to reduce dependency on Commons Lang 2.

## Problem
1. The replacement logic for `StringUtils.capitalize` may not fully replicate the original behavior, especially for edge cases involving Unicode characters.
2. The defensive coding approach in production code may introduce unnecessary complexity and potential performance overhead.
3. Lack of comprehensive test coverage for the new logic, particularly for edge cases and Unicode handling.

## Evidence
- **core/src/main/java/hudson/model/Descriptor.java:425, 467**: Replaced `StringUtils.capitalize` with custom logic using `Character.toTitleCase`.
- **core/src/main/java/hudson/util/FormValidation.java:638**: Similar replacement with potential for different behavior on edge cases.
- **core/src/test/java/hudson/PluginWrapperTest.java:192**: Test code uses `Character.toTitleCase` without additional checks, which may not cover all scenarios.

## Impact
- The new implementation may not handle all Unicode characters correctly, potentially leading to unexpected behavior in internationalized environments.
- Increased complexity in production code could lead to maintenance challenges and obscure bugs.
- Insufficient test coverage increases the risk of regressions, especially in scenarios not covered by existing tests.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Review and ensure the new logic correctly handles all edge cases, including Unicode characters, to match the behavior of `StringUtils.capitalize`.
2. **Tests:** Add unit tests specifically targeting edge cases and Unicode scenarios to validate the new logic.
3. **Risks:** Consider simplifying the defensive coding approach if it does not significantly contribute to robustness, to reduce complexity and potential performance impact.

## Traceability
Not specified
```