```
# Review Note — Evidence-Anchored

**Scope:** This PR ensures that the offline cause of Jenkins agents is retained when applying configuration as code (CASC) or restarting Jenkins.

## Problem
1. The method `setTemporaryOfflineCause` was made public without adequate access control.
2. The change in `Nodes.java` directly sets the offline cause without checking for null values or existing causes.

## Evidence
- `core/src/main/java/hudson/model/Node.java:282`: The method `setTemporaryOfflineCause` was changed from package-private to public.
- `core/src/main/java/jenkins/model/Nodes.java:124`: The offline cause is set directly from the old node to the new node without null checks.

## Impact
- Making `setTemporaryOfflineCause` public could lead to unintended external modifications, potentially causing inconsistent states or security issues.
- Directly setting the offline cause without null checks might lead to NullPointerExceptions or overwrite existing causes unintentionally.

## Recommendation (Fix / Tests / Risks)
1. Restrict the visibility of `setTemporaryOfflineCause` to package-private or use annotations to control access.
2. Add null checks and logic to handle existing offline causes in `Nodes.java` to prevent overwriting or exceptions.
3. Consider adding more comprehensive tests to cover edge cases, such as nodes with existing offline causes.

## Traceability
Not specified
```