```
# Review Note — Evidence-Anchored

**Scope:** This PR ensures that the offline cause of Jenkins agents is retained when applying configuration as code (CASC) or restarting Jenkins.

## Problem
1. The method `setTemporaryOfflineCause` in `Node.java` is made public without clear justification.
2. Lack of comprehensive test coverage for edge cases related to offline causes.

## Evidence
- `core/src/main/java/hudson/model/Node.java:282`: The method `setTemporaryOfflineCause` is changed from package-private to public.
- `test/src/test/java/jenkins/model/NodesTest.java:359`: A new test `setNodesRetainsOfflineCause` is added, but it only covers a basic scenario.

## Impact
- Making `setTemporaryOfflineCause` public increases the risk of misuse by external classes, potentially leading to unintended modifications of node states.
- Insufficient test coverage might miss edge cases where offline causes are not retained correctly, leading to potential regressions in production environments.

## Recommendation (Fix / Tests / Risks)
1. **Restrict Access**: Consider keeping `setTemporaryOfflineCause` package-private or use annotations to restrict its access to internal use only.
2. **Expand Test Coverage**: Add more tests to cover edge cases, such as multiple nodes with different offline causes and scenarios where nodes are rapidly toggled between online and offline states.
3. **Review Documentation**: Ensure that any changes to method visibility are well-documented to prevent misuse by developers unfamiliar with the internal workings.

## Traceability
Not specified
```