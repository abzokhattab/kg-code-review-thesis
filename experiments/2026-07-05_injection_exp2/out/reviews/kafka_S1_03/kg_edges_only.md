```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `StreamsException` class to `StreamsExceptionInternal`.

## Problem
1. The renaming of `StreamsException` to `StreamsExceptionInternal` may break existing code that relies on the original class name.
2. The change affects multiple classes that depend on `StreamsException`, potentially leading to widespread integration issues.
3. There is no evidence of updated documentation or migration notes for this breaking change.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/errors/StreamsException.java`: Line 30, class name changed from `StreamsException` to `StreamsExceptionInternal`.
- Multiple dependencies on `StreamsException` constructor:
  - `streams/src/main/java/org/apache/kafka/streams/errors/BrokerNotFoundException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/InternalTopicsAlreadySetupException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/InvalidStateStoreException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/LockException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/MisconfiguredInternalTopicException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/MissingInternalTopicsException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/MissingSourceTopicException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/ProcessorStateException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/TaskAssignmentException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/TaskCorruptedException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/TaskIdFormatException.java`: Line 10
  - `streams/src/main/java/org/apache/kafka/streams/errors/TaskMigratedException.java`: Line 10

## Impact
- Technical impact includes potential compilation errors across multiple classes that instantiate `StreamsException`.
- Risk of runtime failures if the change is not propagated correctly across all dependent modules.
- Lack of documentation or migration guidance could lead to confusion and increased maintenance burden for developers.

## Recommendation (Fix / Tests / Risks)
1. Revert the renaming of `StreamsException` to maintain backward compatibility, or provide a clear migration path with extensive documentation.
2. Update all dependent classes and ensure comprehensive testing to validate that the change does not introduce integration issues.
3. Consider deprecating the old class name with a transition period if the renaming is necessary, providing developers time to adapt.

## Traceability
- Code ownership: Not specified
```