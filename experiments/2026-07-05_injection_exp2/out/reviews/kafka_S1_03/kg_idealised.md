```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `StreamsException` class to `StreamsExceptionInternal`.

## Problem
1. The renaming of `StreamsException` to `StreamsExceptionInternal` could break backward compatibility for any external code that relies on this exception class.
2. The change affects multiple dependent files and classes that currently use `StreamsException`, potentially leading to runtime errors if not all references are updated.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/errors/StreamsException.java`: Line 31, class name changed from `StreamsException` to `StreamsExceptionInternal`.
- Dependent files such as:
  - `streams/src/main/java/org/apache/kafka/streams/KafkaStreams.java` (calls `StreamsException`)
  - `streams/src/main/java/org/apache/kafka/streams/errors/BrokerNotFoundException.java` (calls `StreamsException`)
  - `streams/src/main/java/org/apache/kafka/streams/errors/TaskAssignmentException.java` (calls `StreamsException`)

## Impact
- **Backward Compatibility Risk:** External systems or plugins that catch or throw `StreamsException` will face compilation errors unless they are updated to use the new class name.
- **Integration Risk:** Any internal logic that relies on the specific type `StreamsException` may fail if not updated, leading to potential runtime exceptions or incorrect error handling.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility:** Consider maintaining the original `StreamsException` class and deprecating it, while introducing `StreamsExceptionInternal` for internal use. This provides a smoother transition path.
2. **Update References:** Ensure all internal references to `StreamsException` are updated to `StreamsExceptionInternal` to prevent runtime errors.
3. **Testing:** Add comprehensive tests to verify that all exceptions are correctly caught and handled with the new class name. Ensure that existing tests are updated to reflect the new class name.
4. **Documentation:** Update any relevant documentation to inform users of the change and how to adapt their code.

## Traceability
- Code Owners: Streams Team
```