```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `KeyValue` class to `KeyValueInternal`.

## Problem
1. Potential backward compatibility issue due to class name change.
2. Lack of documentation or migration guide for users affected by this change.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/KeyValue.java:28`: The class name has been changed from `KeyValue` to `KeyValueInternal`.

## Impact
- The renaming of a public class can break existing codebases that depend on the `KeyValue` class, leading to compilation errors for users who upgrade to this version without adjusting their imports and references.
- Users of the library may not be aware of the change, causing confusion and potential disruptions in production environments.

## Recommendation (Fix / Tests / Risks)
1. Provide a deprecated `KeyValue` class that extends `KeyValueInternal` to maintain backward compatibility.
2. Update the documentation to include a migration guide for users, explaining the change and how to adapt their code.
3. Consider adding a test to ensure that the deprecated `KeyValue` class behaves as expected if implemented.

## Traceability
Not specified
```