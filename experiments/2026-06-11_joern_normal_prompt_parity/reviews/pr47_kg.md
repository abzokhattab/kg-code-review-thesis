```
# Review Note — Evidence-Anchored

**Scope:** This PR ensures that the offline cause of Jenkins agents is retained when applying configuration as code (CASC) or restarting Jenkins.

## Problem
1. The method `setTemporaryOfflineCause` in `Node.java` was made public without proper access restrictions.
2. The integration of the offline cause retention logic in `Nodes.java` may not be adequately covered by existing tests.

## Evidence
- `core/src/main/java/hudson/model/Node.java:282`: The method `setTemporaryOfflineCause` was changed from package-private to public, which could expose it to unintended external use.
- `core/src/main/java/jenkins/model/Nodes.java:124`: The offline cause is set for nodes, but there is no evidence of comprehensive test coverage for various edge cases.

## Impact
- Making `setTemporaryOfflineCause` public increases the risk of misuse by external code, potentially leading to inconsistent states or security issues.
- Insufficient test coverage for the new logic in `Nodes.java` could result in undetected bugs, especially in complex scenarios involving multiple nodes or concurrent operations.

## Recommendation (Fix / Tests / Risks)
1. **Restrict Access**: Consider using annotations like `@Restricted(NoExternalUse.class)` to limit the exposure of `setTemporaryOfflineCause` to internal use only.
2. **Expand Test Coverage**: Add more unit tests to cover edge cases, such as concurrent node updates and scenarios with multiple nodes having different offline causes.
3. **Review Integration**: Ensure that the integration with other components that depend on node states is thoroughly tested, especially in scenarios involving CASC and Jenkins restarts.

## Traceability
- Code Owners: Jenkins core team
- Related Teams: Jenkins configuration as code plugin maintainers
```