```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the condition handling for epsilon in the `_optics` module of sklearn.

## Problem
1. The change from `>` to `>=` in the condition may alter the intended behavior of the function.
2. Lack of accompanying test updates or additions to verify the new behavior.

## Evidence
- `sklearn/cluster/_optics.py:381`: The condition change from `eps > self.max_eps` to `eps >= self.max_eps`.

## Impact
- The change in condition could lead to a `ValueError` being raised in scenarios that were previously valid (i.e., when `eps` is exactly equal to `max_eps`). This could break existing functionality or user code that relies on the previous behavior.

## Recommendation (Fix / Tests / Risks)
1. Review the intended logic to confirm whether `eps` should indeed be allowed to equal `max_eps`. If the change is intentional, ensure that this is documented.
2. Add or update unit tests to cover the scenario where `eps` equals `max_eps` to verify that the new behavior is as expected.
3. Consider communicating this change in behavior in the release notes or documentation to alert users of the potential impact.

## Traceability
Not specified
```