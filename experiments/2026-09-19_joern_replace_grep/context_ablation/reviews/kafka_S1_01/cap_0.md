```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the KeyValue class to KeyValueInternal.

## Problem
1. Potential backward compatibility issues due to class renaming.
2. Lack of documentation or migration guide for users relying on the previous class name.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/KeyValue.java:28`: The class name is changed from `KeyValue` to `KeyValueInternal`.

## Impact
Renaming a public class can break existing codebases that depend on this class. Users of the library might experience compilation errors if they have directly referenced `KeyValue` in their code. This change could also affect any serialized data that relies on the class name, potentially leading to deserialization issues.

## Recommendation (Fix / Tests / Risks)
1. Consider maintaining the original class name and introducing `KeyValueInternal` as a new class if needed, to preserve backward compatibility.
2. If renaming is necessary, provide a migration guide or deprecation strategy to help users transition smoothly.
3. Add tests to ensure that any serialized forms of the class are still compatible after the change.

## Traceability
Not specified
```