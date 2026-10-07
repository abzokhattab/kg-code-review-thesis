```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `TaskId` class to `TaskIdInternal`.

## Problem
1. Inconsistent Logging: The logger still references the old class name `TaskId`.
2. Potential API Breakage: Renaming a public class might affect external dependencies if this is part of a public API.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/processor/TaskId.java:29`: The logger is initialized with `TaskId.class` instead of the new `TaskIdInternal.class`.

## Impact
- **Inconsistent Logging**: This could lead to confusion in log files, making it harder to trace issues related to this class.
- **API Breakage**: If `TaskId` is part of a public API, external systems depending on this class will break unless they are updated to use `TaskIdInternal`.

## Recommendation (Fix / Tests / Risks)
1. Update the logger initialization to use `TaskIdInternal.class` to ensure log consistency.
2. Verify whether `TaskId` is part of a public API. If so, consider maintaining backward compatibility or providing migration documentation for users.
3. Add tests to ensure that any external systems or modules that depend on this class are identified and tested for compatibility.

## Traceability
Not specified
```