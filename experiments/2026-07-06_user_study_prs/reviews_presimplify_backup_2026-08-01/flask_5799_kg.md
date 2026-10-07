# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `stream_with_context` function to properly handle async views by storing both app and request contexts and adjusting when they are pushed.

## Problem
1. **Functionality Breakage:** The refactor may inadvertently break existing functionality where `stream_with_context` is used synchronously, as the context management logic has changed significantly.
2. **API Contract Violation:** The change in context management could violate existing API contracts, especially if callers expect the context to be managed differently.
3. **Integration Risk:** The refactor could affect components that rely on `stream_with_context`, such as `src/flask/templating.py` and `src/flask/blueprints.py`, which may not handle the new context management correctly.
4. **Missing Edge Case Tests:** There are no tests for scenarios where the generator raises exceptions or when the context is manually popped before iteration.

## Evidence
- `src/flask/helpers.py:63-111`: Refactored `stream_with_context` function.
- `tests/test_helpers.py:306-335`: Added tests for async view usage.
- `src/flask/templating.py`: Uses `stream_with_context` for template streaming.
- `src/flask/blueprints.py`: May use `stream_with_context` in blueprint routes.
- `tests/test_helpers.py`: Contains tests for `stream_with_context`.

## Impact
- **Technical Impact:** Potential breakage of synchronous usage of `stream_with_context`, leading to runtime errors if contexts are not managed as expected.
- **Regression Risk:** High risk of regression in components that depend on the previous context management behavior.
- **Untested Scenarios:** Lack of tests for exception handling within the generator and manual context manipulation.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure backward compatibility by adding logic to handle both synchronous and asynchronous contexts appropriately.
2. **Tests:** Add tests for edge cases, including exception handling within the generator and scenarios where contexts are manually manipulated.
3. **Risks:** Review and update dependent components (`src/flask/templating.py`, `src/flask/blueprints.py`) to ensure compatibility with the new context management.
