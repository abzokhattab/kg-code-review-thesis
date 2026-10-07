```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `StreamsException` class to `StreamsExceptionInternal`.

## Problem
1. The renaming of `StreamsException` to `StreamsExceptionInternal` may break existing code that relies on the original class name.
2. The change does not include updates to all references and usages of `StreamsException` across the codebase, potentially leading to runtime errors.
3. There is no evidence of updated documentation or migration notes for users of the library.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/errors/StreamsException.java:30`: The class name is changed from `StreamsException` to `StreamsExceptionInternal`.
- Multiple files (e.g., `BrokerNotFoundException.java`, `LockException.java`) in the call graph still reference `StreamsException` constructor without any updates.

## Impact
- Technical Impact: This change can cause compilation errors in any code that imports or extends `StreamsException`. It may also lead to runtime exceptions if the class is dynamically loaded or reflected upon.
- Risk of breaking backward compatibility for users who have implemented custom exception handling based on `StreamsException`.

## Recommendation (Fix / Tests / Risks)
1. Ensure all references to `StreamsException` across the codebase are updated to `StreamsExceptionInternal` to prevent compilation errors.
2. Provide a migration guide or update documentation to inform users of the change and how to adapt their code.
3. Consider maintaining backward compatibility by deprecating `StreamsException` instead of renaming it outright, or by providing an alias.

## Traceability
- Not specified
```