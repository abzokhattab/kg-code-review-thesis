```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the `wrapped` method in the `WrappedStateStore` class to include a new parameter `RequiredContext`.

## Problem
1. The `wrapped` method signature has changed, but the method body does not utilize the new `RequiredContext` parameter.
2. The change in method signature affects multiple callers in `AbstractReadOnlyDecorator`, which have not been updated to pass the new parameter.

## Evidence
- `streams/src/main/java/org/apache/kafka/streams/state/internals/WrappedStateStore.java:144`: The `wrapped` method now requires a `RequiredContext` parameter, but it is not used within the method.
- Callers in `streams/src/main/java/org/apache/kafka/streams/processor/internals/AbstractReadOnlyDecorator.java` (e.g., `get`, `range`, `reverseRange`, etc.) are not updated to accommodate the new parameter.

## Impact
- This change introduces a compilation error in all methods in `AbstractReadOnlyDecorator` that call `wrapped`, as they do not provide the required `RequiredContext` argument.
- The lack of usage of `RequiredContext` in the method suggests either an incomplete implementation or an unnecessary parameter, leading to potential confusion and maintenance issues.

## Recommendation (Fix / Tests / Risks)
1. Update all callers in `AbstractReadOnlyDecorator` to pass the appropriate `RequiredContext` to the `wrapped` method.
2. If `RequiredContext` is not needed, remove it from the method signature to avoid unnecessary complexity.
3. Add unit tests to ensure that the `wrapped` method behaves correctly with the new parameter, if it is indeed required.

## Traceability
Not specified
```