```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the Node and Nodes classes to ensure that the offline cause of agents is retained when applying configuration as code.

## Problem
1. The `setTemporaryOfflineCause` method in `Node.java` has been made public, which may expose it to unintended external use despite the `@Restricted(NoExternalUse.class)` annotation.
2. The test coverage for the new functionality in `NodesTest.java` may not be comprehensive enough to cover all edge cases, such as different types of `OfflineCause`.

## Evidence
- `core/src/main/java/hudson/model/Node.java:279-282`: The `setTemporaryOfflineCause` method is changed from package-private to public.
- `test/src/test/java/jenkins/model/NodesTest.java:359-372`: A new test `setNodesRetainsOfflineCause` is added, but it only tests a specific `OfflineCause.UserCause`.

## Impact
- Making `setTemporaryOfflineCause` public could lead to misuse by external code, potentially causing nodes to be set offline unintentionally.
- Insufficient test coverage might lead to undetected bugs if other types of `OfflineCause` are used or if the method is called in different contexts.

## Recommendation (Fix / Tests / Risks)
1. Consider keeping `setTemporaryOfflineCause` package-private or protected to limit its exposure, and ensure the `@Restricted(NoExternalUse.class)` annotation is respected.
2. Expand test coverage in `NodesTest.java` to include different types of `OfflineCause` and scenarios to ensure robustness.
3. Review the necessity of making `setTemporaryOfflineCause` public and assess if there are alternative approaches to achieve the desired functionality without increasing the method's visibility.

## Traceability
- Code Owners: Not specified
```