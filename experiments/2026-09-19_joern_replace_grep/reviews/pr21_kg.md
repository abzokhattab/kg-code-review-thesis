```
# Review Note — Evidence-Anchored

**Scope:** This PR updates the Kafka codebase to remove JDK 8 compatibility and fully support JDK 11.

## Problem
1. Removal of Java version checks may lead to unexpected behavior on non-JDK 11 environments.
2. The removal of conditional logic based on Java version could affect backward compatibility.
3. Insufficient test coverage for changes in `ByteBufferUnmapper` and `Crc32C` classes.

## Evidence
- **clients/src/main/java/org/apache/kafka/common/config/SslConfigs.java:53**: Removal of `IS_JAVA11_COMPATIBLE` check.
- **clients/src/main/java/org/apache/kafka/common/utils/ByteBufferUnmapper.java:82**: Simplification of method handle logic without version checks.
- **clients/src/main/java/org/apache/kafka/common/utils/Crc32C.java:77**: Direct use of `CRC32C` constructor without fallback.
- **clients/src/test/java/org/apache/kafka/common/utils/JavaTest.java:68**: Removal of Java version parsing tests.

## Impact
- The removal of Java version checks could lead to runtime errors if the code is executed in environments not fully compatible with JDK 11.
- Backward compatibility might be compromised, affecting users who have not yet upgraded to JDK 11.
- Lack of specific tests for the new logic in `ByteBufferUnmapper` and `Crc32C` could result in undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. **Fix**: Consider adding runtime checks or documentation to ensure the code is executed in a JDK 11 environment.
2. **Tests**: Enhance test coverage for `ByteBufferUnmapper` and `Crc32C` to ensure the new logic works as expected.
3. **Risks**: Evaluate the impact on users who may still be on older Java versions and provide guidance for upgrading.

## Traceability
Not specified
```