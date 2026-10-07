```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `KeyValueIterator` interface to `KeyValueIteratorInternal`.

## Problem
1. The renaming of `KeyValueIterator` to `KeyValueIteratorInternal` may break existing dependencies and integrations that rely on the original interface name.
2. There is no evidence of corresponding updates in the calling classes or tests to reflect this change, which could lead to runtime errors.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/state/internals/AbstractMergedSortedCacheStoreIterator.java: close` calls `KeyValueIterator.close`.
- `streams/src/main/java/org/apache/kafka/streams/state/internals/CompositeKeyValueIterator.java: hasNext` calls `KeyValueIterator.close`.
- `streams/src/main/java/org/apache/kafka/streams/state/internals/CompositeReadOnlySessionStore.java: findSessions` calls `KeyValueIterator.close`.
- `streams/src/main/java/org/apache/kafka/streams/state/internals/CompositeReadOnlyWindowStore.java: fetch` calls `KeyValueIterator.close`.

## Impact
The technical impact of this change is significant as it may lead to compilation errors across multiple classes that implement or use the `KeyValueIterator` interface. This can cause runtime failures in any Kafka Streams applications relying on these components, potentially leading to data processing disruptions.

## Recommendation (Fix / Tests / Risks)
1. Ensure all classes and interfaces that use or implement `KeyValueIterator` are updated to reflect the new name `KeyValueIteratorInternal`.
2. Update any test cases that involve `KeyValueIterator` to ensure they are using the renamed interface.
3. Consider maintaining backward compatibility by providing an alias or deprecation path for the original `KeyValueIterator` name to minimize disruption.

## Traceability
Not specified
```