```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the Kafka codebase to remove JDK 8 compatibility and fully support JDK 11.

## Problem
1. Removal of Java version checks may lead to unexpected behavior on non-JDK 11 environments.
2. The removal of `Java` utility class methods and related tests might affect backward compatibility and test coverage.
3. Changes in SSL protocol defaults could impact existing configurations and compatibility with older clients.

## Evidence
- **clients/src/main/java/org/apache/kafka/common/config/SslConfigs.java:54**: Removal of conditional logic for SSL protocol based on Java version.
- **clients/src/main/java/org/apache/kafka/common/utils/Java.java:16-47**: Complete removal of Java version parsing and compatibility checks.
- **clients/src/test/java/org/apache/kafka/common/utils/JavaTest.java:20-69**: Removal of tests related to Java version compatibility.

## Impact
- **Technical Impact**: The removal of Java version checks could lead to runtime errors or unexpected behavior if the code is executed in environments not fully compatible with JDK 11. This could affect users who have not yet upgraded their Java version.
- **Risk**: There is a risk of breaking backward compatibility for users who are still on older Java versions. Additionally, the changes in SSL protocol defaults might lead to compatibility issues with clients expecting different protocol versions.

## Recommendation (Fix / Tests / Risks)
1. **Fix**: Consider maintaining a minimal version check to ensure that the code does not run in unsupported environments, or provide clear documentation on the required Java version.
2. **Tests**: Reintroduce tests that verify behavior on different Java versions, even if only to assert that the application fails gracefully on unsupported versions.
3. **Risks**: Clearly document the changes in SSL protocol defaults and provide guidance for users on how to adjust their configurations if necessary.

## Traceability
Not specified
```