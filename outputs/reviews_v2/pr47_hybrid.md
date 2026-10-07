```
# Review Note — Evidence-Anchored

**Scope:** This PR ensures that when applying configuration as code, the offline cause of Jenkins agents is retained.

## Problem
1. The method `setTemporaryOfflineCause` in `Node.java` was made public without adequate access control.
2. The change in `Nodes.java` directly manipulates the offline cause without considering potential side effects or encapsulation principles.

## Evidence
- `core/src/main/java/hudson/model/Node.java:279-282`: The method `setTemporaryOfflineCause` was changed from package-private to public.
- `core/src/main/java/jenkins/model/Nodes.java:121-124`: Directly sets the offline cause of a node without additional validation or encapsulation.

## Impact
- Making `setTemporaryOfflineCause` public could lead to unintended usage by external classes, potentially causing inconsistent states or security issues.
- Direct manipulation of node states in `Nodes.java` could bypass necessary checks or event triggers, leading to unexpected behavior in the Jenkins ecosystem.

## Recommendation (Fix / Tests / Risks)
1. Revert the visibility change of `setTemporaryOfflineCause` to package-private and provide a controlled interface for necessary external access.
2. Introduce a method in `Node` that safely updates the offline cause, ensuring all necessary checks and events are handled.
3. Add additional unit tests to cover edge cases where offline causes are manipulated, ensuring robustness against future changes.

## Traceability
Not specified
```