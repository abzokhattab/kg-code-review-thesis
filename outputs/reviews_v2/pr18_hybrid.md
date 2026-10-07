```
# Review Note — Evidence-Anchored

**Scope:** This PR aims to reduce the usage of `StringUtils` from Commons Lang 2 by replacing it with standard Java functionality.

## Problem
1. The replacement logic for `StringUtils.capitalize` does not handle null inputs consistently across all usages.
2. The manual capitalization logic may not fully replicate the behavior of `StringUtils.capitalize` for certain Unicode characters.
3. The changes in test files switch to Commons Lang 3, which might introduce inconsistencies if not uniformly applied across the codebase.

## Evidence
- `core/src/main/java/hudson/model/Descriptor.java:425` and `core/src/main/java/hudson/model/Descriptor.java:467`: Manual capitalization logic is used without null checks.
- `core/src/main/java/hudson/util/FormValidation.java:638`: Similar manual capitalization logic without null checks.
- `core/src/test/java/hudson/PluginWrapperTest.java:192`: Manual capitalization logic used in test setup.

## Impact
- The lack of null checks could lead to `NullPointerException` if null values are passed to these methods.
- The manual capitalization logic might not handle all Unicode characters correctly, potentially altering the behavior of the application.
- Introducing Commons Lang 3 in some test files but not others could lead to inconsistencies and maintenance challenges.

## Recommendation (Fix / Tests / Risks)
1. Add null checks before applying the manual capitalization logic to prevent `NullPointerException`.
2. Consider using a more robust method for capitalization that handles Unicode characters consistently, such as `String.toUpperCase(Locale.ROOT)`.
3. Ensure that the use of Commons Lang 3 is consistent across all test files to avoid discrepancies.

## Traceability
Not specified
```