```
# Review Note — Evidence-Anchored

**Scope:** This PR aims to reduce the usage of `StringUtils` by replacing it with native Java methods.

## Problem
1. The replacement logic for `StringUtils.capitalize` is manually implemented and may not handle all edge cases.
2. The manual capitalization logic is repeated in multiple places, leading to potential maintenance challenges.
3. The change from `org.apache.commons.lang.StringUtils` to `org.apache.commons.lang3.StringUtils` in test files may introduce inconsistencies if not uniformly applied across the codebase.

## Evidence
- **core/src/main/java/hudson/model/Descriptor.java:425** and **core/src/main/java/hudson/model/Descriptor.java:467**: Manual capitalization logic replaces `StringUtils.capitalize`.
- **core/src/main/java/hudson/util/FormValidation.java:638**: Similar manual capitalization logic is used.
- **core/src/test/java/hudson/PluginWrapperTest.java:192**: Manual capitalization logic is applied to plugin attributes.
- **test/src/test/java/hudson/cli/DisablePluginCommandTest.java:41** and other test files: Transition from `org.apache.commons.lang.StringUtils` to `org.apache.commons.lang3.StringUtils`.

## Impact
- The manual capitalization logic may not handle all Unicode characters correctly, potentially leading to incorrect behavior in internationalized environments.
- Repeated logic increases the risk of bugs and makes future changes more error-prone.
- Inconsistent use of `StringUtils` versions across the codebase could lead to confusion and potential integration issues.

## Recommendation (Fix / Tests / Risks)
1. Consider using `Character.toUpperCase` with `Locale` to ensure proper handling of international characters.
2. Refactor the capitalization logic into a utility method to avoid code duplication and simplify maintenance.
3. Ensure consistent usage of `StringUtils` across the entire codebase to prevent integration issues.

## Traceability
Not specified
```