```
# Review Note — Evidence-Anchored

**Scope:** This PR aims to reduce the usage of `StringUtils` from Commons Lang 2 by replacing it with standard Java functionality and Commons Lang 3 where applicable.

## Problem
1. The replacement logic for `StringUtils.capitalize` may not fully replicate the original behavior, especially with non-ASCII characters.
2. The defensive checks for null or empty strings are inconsistent across different files.
3. The change in `PluginWrapperTest` does not handle potential null values for `name` consistently with other parts of the code.

## Evidence
- `core/src/main/java/hudson/model/Descriptor.java:425`: The replacement logic for capitalization may not handle all Unicode characters correctly.
- `core/src/main/java/hudson/util/FormValidation.java:638`: Similar capitalization logic with potential Unicode handling issues.
- `core/src/test/java/hudson/PluginWrapperTest.java:192`: The use of `Character.toTitleCase` without null checks could lead to `NullPointerException`.

## Impact
- Incorrect handling of Unicode characters could lead to unexpected behavior or bugs in string processing, especially in internationalized environments.
- Inconsistent null handling could result in runtime exceptions, affecting the stability of the application.

## Recommendation (Fix / Tests / Risks)
1. Ensure that the capitalization logic correctly handles all Unicode characters, possibly by using `String.toUpperCase(Locale)` with appropriate locale settings.
2. Standardize null and empty string checks across all modified files to prevent potential `NullPointerException`.
3. Add unit tests to cover edge cases, including null inputs and strings with special Unicode characters, to ensure consistent behavior.

## Traceability
Not specified
```