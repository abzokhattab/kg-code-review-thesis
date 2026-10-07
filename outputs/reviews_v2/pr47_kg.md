```
# Review Note — Evidence-Anchored

**Scope:** This PR ensures that the offline cause of Jenkins agents is retained when applying configuration as code or restarting Jenkins.

## Problem
1. The method `setTemporaryOfflineCause` in `Node.java` was previously package-private, limiting its accessibility.
2. The integration of the offline cause retention logic in `Nodes.java` may not be adequately covered by existing tests.

## Evidence
- `core/src/main/java/hudson/model/Node.java:282`: The method `setTemporaryOfflineCause` was changed from package-private to public, which could expose it to unintended external use.
- `core/src/main/java/jenkins/model/Nodes.java:124`: The offline cause is now explicitly set when nodes are updated, but this logic is new and may not be fully tested.
- `test/src/test/java/jenkins/model/NodesTest.java:359`: A new test `setNodesRetainsOfflineCause` was added, but it may not cover all edge cases or integration scenarios.

## Impact
- Making `setTemporaryOfflineCause` public increases the risk of misuse by external code, potentially leading to inconsistent states if not used correctly.
- If the new logic in `Nodes.java` is not thoroughly tested, there could be scenarios where the offline cause is not retained as expected, leading to operational issues in Jenkins environments relying on this feature.

## Recommendation (Fix / Tests / Risks)
1. **Restrict Access**: Consider using a more restrictive access level for `setTemporaryOfflineCause` and provide controlled access through a well-defined interface or service.
2. **Expand Test Coverage**: Add more comprehensive tests to cover edge cases and integration scenarios, ensuring that the offline cause is consistently retained across various configurations and states.
3. **Review Documentation**: Ensure that any changes to method access levels are documented, and guidelines are provided for their correct usage to prevent misuse.

## Traceability
- Code Owners: Jenkins core team
- Related Teams: Jenkins configuration as code plugin maintainers
```