```
# Review Note — Evidence-Anchored

**Scope:** This PR aims to reduce the usage of `StringUtils` from Commons Lang 2 by replacing it with standard Java functionality and Commons Lang 3 where applicable.

## Problem
1. The replacement logic for `StringUtils.capitalize` may not fully replicate the original behavior in all edge cases.
2. The defensive coding approach in production code might introduce unnecessary complexity.
3. Potential lack of comprehensive test coverage for the new capitalization logic.

## Evidence
- **core/src/main/java/hudson/model/Descriptor.java:425, 467**: The replacement logic for `StringUtils.capitalize` uses `Character.toTitleCase`, which might not handle all Unicode characters as expected.
- **core/src/main/java/hudson/util/FormValidation.java:638**: Similar replacement logic is applied, which could lead to inconsistencies if not thoroughly tested.
- **core/src/test/java/hudson/PluginWrapperTest.java:192**: The test case uses a simplified capitalization logic that might not cover all scenarios.

## Impact
- The new capitalization logic might not handle all Unicode characters correctly, potentially leading to unexpected behavior in internationalized environments.
- Increased complexity in production code due to defensive programming could make future maintenance harder.
- Insufficient test coverage might lead to undetected bugs, especially in edge cases involving Unicode characters.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Review and ensure the new capitalization logic handles all relevant Unicode cases, possibly by adding more comprehensive tests.
2. **Tests:** Expand test cases to cover edge cases, particularly those involving Unicode characters, to ensure the new logic behaves as expected.
3. **Risks:** Consider simplifying the defensive coding approach in production code to reduce complexity, while ensuring that edge cases are covered by tests.

## Traceability
- Code Owners: Not specified
```