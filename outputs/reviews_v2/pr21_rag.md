```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the Kafka codebase to remove JDK 8 compatibility checks and annotations, ensuring compatibility with JDK 11.

## Problem
1. Removal of Java version compatibility checks may lead to unexpected behavior on non-JDK 11 environments.
2. The removal of the `Java` utility class and its version checks could impact other parts of the codebase that rely on these checks.
3. The changes in `SslConfigs` and related test files may not fully account for environments where TLSv1.3 is not supported.

## Evidence
- `clients/src/main/java/org/apache/kafka/common/config/SslConfigs.java:39-53`: Removal of conditional logic based on Java version.
- `clients/src/main/java/org/apache/kafka/common/utils/Java.java:16-47`: Complete removal of Java version parsing and compatibility checks.
- `clients/src/test/java/org/apache/kafka/common/network/SslTransportLayerTest.java:146-145`: Removal of Java version checks in test parameters.

## Impact
- **Technical Impact:** The removal of Java version checks could lead to runtime errors or unexpected behavior in environments that do not fully support JDK 11 features, such as TLSv1.3.
- **Risk:** Systems running on older Java versions may encounter compatibility issues, especially in SSL/TLS configurations.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Reintroduce a mechanism to handle environments that do not support JDK 11 features, possibly through configuration or runtime checks.
2. **Tests:** Ensure comprehensive testing across different Java environments to verify that the application behaves as expected.
3. **Risks:** Document the changes and potential impacts on environments not running JDK 11, advising users to upgrade their Java version.

## Traceability
Not specified
```