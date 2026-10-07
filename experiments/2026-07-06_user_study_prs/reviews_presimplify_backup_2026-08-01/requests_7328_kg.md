# Review Note — Evidence-Anchored

**Scope:** This PR modifies the redirect handling in the `requests` library to prevent self-referencing in the response history.

## Problem
1. The change may break existing functionality where clients expect the original request to be part of the history.
2. The modification could violate existing API contracts, particularly if clients rely on the current behavior of `resp.history`.
3. There is a risk of integration issues with components that depend on the `resolve_redirects` function, such as those in `src/requests/api.py`.
4. The test coverage does not include scenarios where redirects are nested or involve complex chains, which could lead to untested edge cases.

## Evidence
- `src/requests/sessions.py:179-183` — Modification of how `resp.history` is assigned.
- `tests/test_requests.py:217-225` — Addition of a new test for redirect history.
- `src/requests/__init__.py` and `src/requests/api.py` depend on `resolve_redirects`.
- Existing tests in `tests/test_requests.py` cover basic redirect scenarios but lack complex chain tests.

## Impact
- **Technical impact:** Potential breaking change for clients relying on the current `resp.history` behavior.
- **Regression risk:** High for clients expecting the original request in the history.
- **Untested scenarios:** Complex redirect chains and nested redirects are not covered.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Consider maintaining backward compatibility by optionally including the original request in the history.
2. **Tests:** Add tests for nested and complex redirect chains to `tests/test_requests.py`.
3. **Risks:** Document the change clearly in the API documentation to inform users of the new behavior.
