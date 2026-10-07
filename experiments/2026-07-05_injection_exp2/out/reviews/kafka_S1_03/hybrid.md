```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `StreamsException` class to `StreamsExceptionInternal`.

## Problem
1. The renaming of `StreamsException` to `StreamsExceptionInternal` may break existing code that relies on the public API, as this class is widely used across the codebase.
2. The change does not seem to be accompanied by updates in the dependent files or tests that ensure the new naming does not introduce errors.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/errors/StreamsException.java`: Line 31 - Class name changed from `StreamsException` to `StreamsExceptionInternal`.
- `streams/src/main/java/org/apache/kafka/streams/errors/BrokerNotFoundException.java`: Line 15 - Constructor calls `StreamsException` which may now be broken.
- `streams/src/main/java/org/apache/kafka/streams/errors/InternalTopicsAlreadySetupException.java`: Line 12 - Constructor calls `StreamsException`.
- Additional references in other exception classes such as `InvalidStateStoreException`, `LockException`, etc., all relying on `StreamsException`.

## Impact
The renaming of a widely used exception class can lead to compilation errors across the codebase if all references are not updated. This could disrupt the build process and lead to runtime exceptions if not properly handled. Furthermore, if this class is part of the public API, it could affect external clients relying on the existing class name.

## Recommendation (Fix / Tests / Risks)
1. Ensure all references to `StreamsException` in the codebase are updated to `StreamsExceptionInternal` to prevent compilation errors.
2. Review and update any documentation that references `StreamsException` to reflect the new naming.
3. Consider the impact on public API users and provide a migration path or maintain backward compatibility if necessary.
4. Add or update unit tests to ensure that the renaming does not introduce new errors or affect existing functionality.

## Traceability
Not specified
```