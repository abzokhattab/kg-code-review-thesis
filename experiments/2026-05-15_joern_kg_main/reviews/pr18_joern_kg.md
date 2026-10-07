# Review Note — Evidence-Anchored

**Scope:** This PR aims to reduce the usage of `org.apache.commons.lang.StringUtils` by replacing `capitalize` and `uncapitalize` calls with standard Java platform functionality, specifically `Character.toTitleCase`.

## Problem
1.  **Inconsistent Dependency Management Goal:** The PR description states the goal is to "reduce usages of Commons Lang 2 in hopes that we may eventually be able to remove this outdated library from core." However, several test files are updated to use `org.apache.commons.lang3.StringUtils` instead of `org.apache.commons.lang.StringUtils`. This introduces or reinforces a dependency on `commons-lang3` in test code, which, while potentially an upgrade, does not align with the stated goal of *removing* `commons-lang` (version 2) from the project's overall dependency footprint.
2.  **Untested Reflection-based Method Resolution:** The capitalization logic in `hudson.model.Descriptor` and `hudson.util.FormValidation` is critical as it's used to dynamically construct method names for reflection (e.g., `doFillFooItems`, `doAutoCompleteFoo`, `doCheckBar`). While the new `Character.toTitleCase` logic appears to mimic `StringUtils.capitalize` behavior, there are no specific tests added or existing tests verified to cover these reflection paths with diverse inputs, especially non-ASCII or edge-case Unicode characters, which could lead to silent failures in UI rendering or validation.
3.  **Behavioral Change in Test Utility Nullability:** The `PluginWrapperBuilder` constructor in `hudson.PluginWrapperTest.java` now explicitly enforces non-null `name` using `Objects.requireNonNull`. While this improves robustness within the test utility, it changes the behavior for a `null` input to the builder, which previously would have been handled by `StringUtils.capitalize(null)` returning `null`. Although this is in a test file, it's a behavioral change that could affect existing test scenarios if `null` was ever implicitly or explicitly passed.

## Evidence
*   **Inconsistent Dependency Management Goal:**
    *   Diff: `test/src/test/java/hudson/cli/DisablePluginCommandTest.java:41` shows `import org.apache.commons.lang3.StringUtils;`. Similar changes are present in `test/src/test/java/hudson/security/HudsonPrivateSecurityRealmTest.java`, `test/src/test/java/jenkins/security/apitoken/LegacyApiTokenAdministrativeMonitorTest.java`, and `test/src/test/java/org/kohsuke/stapler/BindTest.java`.
    *   PR Description: "reduce usages of Commons Lang 2 in hopes that we may eventually be able to remove this outdated library from core."
*   **Untested Reflection-based Method Resolution:**
    *   Diff: `core/src/main/java/hudson/model/Descriptor.java:427` and `core/src/main/java/hudson/model/Descriptor.java:469` show the new capitalization logic `field == null || field.isEmpty() ? field : Character.toTitleCase(field.charAt(0)) + field.substring(1);`.
    *   Diff: `core/src/main/java/hudson/util/FormValidation.java:641` shows the same new capitalization logic.
    *   Structural Context: `hudson/model/Descriptor.java::calcFillSettings` and `hudson/model/Descriptor.java::calcAutoCompleteSettings` use the capitalized field name to construct method names for `ReflectionUtils.getPublicMethodNamed`.
    *   Structural Context: `hudson/util/FormValidation.java::CheckMethod` constructor uses the capitalized field name to construct method names for `ReflectionUtils.getPublicMethodNamed`.
    *   Related Tests: `test/src/test/java/hudson/model/DescriptorTest.java` and `core/src/test/java/hudson/util/FormValidationTest.java` exist but do not explicitly cover these reflection paths with diverse string inputs (e.g., `éfield`, `1field`).
*   **Behavioral Change in Test Utility Nullability:**
    *   Diff: `core/src/test/java/hudson/PluginWrapperTest.java:151` shows `this.name = Objects.requireNonNull(name);` added to the `PluginWrapperBuilder` constructor.
    *   Diff: `core/src/test/java/hudson/PluginWrapperTest.java:192` shows the new capitalization logic `Character.toTitleCase(name.charAt(0)) + name.substring(1);` which would not be reached for a `null` `name` due to the `requireNonNull` check.

## Impact
*   **Inconsistent Dependency Management Goal:** The PR's stated goal of removing `commons-lang2` from core is undermined if `commons-lang3` is introduced or expanded as a dependency, even if only in test scope. This could lead to confusion about the project's dependency roadmap and potentially increase the overall dependency footprint if both `commons-lang2` and `commons-lang3` are present.
*   **Untested Reflection-based Method Resolution:** Subtle differences in capitalization behavior, especially for non-ASCII or specific Unicode characters, could cause `ReflectionUtils.getPublicMethodNamed` to fail to find the intended methods. This would lead to silent failures where UI elements (e.g., fill-in-the-blank fields, auto-completion suggestions) or form validations simply do not appear or function, degrading user experience and potentially leading to data integrity issues.
*   **Behavioral Change in Test Utility Nullability:** While likely benign, this change could cause `NullPointerException`s in existing or future tests that might have inadvertently or intentionally passed `null` to the `PluginWrapperBuilder` constructor, requiring test refactoring.

## Recommendation (Fix / Tests / Risks)
1.  **Clarify Dependency Strategy:**
    *   **Fix:** Either revert the `commons-lang3` changes in the `test/src/test/java` files if the sole goal is to remove `commons-lang2` entirely, or update the PR description to explicitly state that the goal includes upgrading to `commons-lang3` in test scope as a step towards a broader dependency cleanup.
2.  **Add Comprehensive Reflection Tests:**
    *   **Tests:** Add new test cases to `test/src/test/java/hudson/model/DescriptorTest.java` that specifically invoke `Descriptor.calcFillSettings` and `Descriptor.calcAutoCompleteSettings` with various `field` names. These should include:
        *   Names starting with lowercase ASCII (e.g., "foo").
        *   Names starting with uppercase ASCII (e.g., "Foo").
        *   Names starting with numbers (e.g., "1foo").
        *   Names starting with Unicode characters that have titlecase forms (e.g., "éfield", "Ǆfield" using U+01C4, U+01C5, U+01C6, U+01C7, U+01C8, U+01C9, U+01CA, U+01CB, U+01CC).
        *   Verify that the correct `doFill...Items` or `doAutoComplete...` methods are found via reflection.
    *   **Tests:** Similarly, add new test cases to `core/src/test/java/hudson/util/FormValidationTest.java` to verify the `hudson.util.FormValidation.CheckMethod` constructor's ability to resolve `doCheck...` methods using diverse `fieldName` inputs, including the Unicode and edge cases mentioned above.
3.  **Document Test Utility Change:**
    *   **Risk:** Acknowledge the `Objects.requireNonNull(name)` change in `core/src/test/java/hudson/PluginWrapperTest.java` in the PR description or commit message, noting that `null` is no longer accepted for the `name` parameter in `PluginWrapperBuilder`. No code change is strictly necessary unless `null` inputs were a valid, intended test scenario.

## Traceability
Not specified