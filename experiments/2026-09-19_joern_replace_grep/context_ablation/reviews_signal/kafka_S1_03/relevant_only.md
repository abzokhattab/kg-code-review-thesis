```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `StreamsException` class to `StreamsExceptionInternal`.

## Problem
1. The renaming of `StreamsException` to `StreamsExceptionInternal` may break existing dependencies and integrations that rely on the original class name.
2. The change lacks corresponding updates in the dependent files and tests that utilize `StreamsException`.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/errors/StreamsException.java`: The class `StreamsException` is renamed to `StreamsExceptionInternal`.
- Dependent files such as `streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java` and others still reference `StreamsException` without any updates.
- Call-graph edges indicate multiple exceptions (e.g., `BrokerNotFoundException`, `InternalTopicsAlreadySetupException`) depend on `StreamsException` constructor.

## Impact
- This change can lead to compilation errors in any module or file that imports or extends `StreamsException`.
- Runtime exceptions may occur if the class is dynamically loaded or reflected upon by its original name.
- The lack of test updates may result in undetected issues during runtime, especially in error handling paths.

## Recommendation (Fix / Tests / Risks)
1. Update all dependent files to reference `StreamsExceptionInternal` instead of `StreamsException`.
2. Ensure all tests that involve `StreamsException` are updated to reflect the new class name and run them to verify no regressions occur.
3. Consider the necessity of this renaming and provide a clear migration path or aliasing if backward compatibility is a concern.

## Traceability
Not specified
```