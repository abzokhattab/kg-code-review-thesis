```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a project setting to enable legacy fog blending behavior, allowing users to revert to pre-4.6 fog visuals.

## Problem
1. Lack of test coverage for the new setting to ensure it behaves as expected across different scenarios.
2. Potential for increased maintenance complexity due to the introduction of a legacy behavior toggle.

## Evidence
- `doc/classes/ProjectSettings.xml:2922`: New project setting `rendering/environment/fog/use_legacy_blending` added without accompanying tests.
- `servers/rendering/renderer_rd/environment/sky.cpp:1226`: Integration of the legacy blending setting into the rendering pipeline.
- `servers/rendering/renderer_rd/shaders/environment/sky.glsl:288`: Conditional logic added for legacy blending without test validation.

## Impact
- Without tests, there is a risk that the legacy blending behavior may not work as intended, leading to visual discrepancies in projects relying on this feature.
- The introduction of a toggle for legacy behavior can complicate future development and debugging efforts, as it adds another path that must be maintained and considered in future changes.

## Recommendation (Fix / Tests / Risks)
1. Implement unit and integration tests to verify the correct functionality of the `use_legacy_blending` setting.
2. Document the expected behavior and any known limitations of the legacy blending mode to aid future maintenance.
3. Consider the long-term implications of maintaining legacy behavior and evaluate if this approach aligns with the project's goals.

## Traceability
Not specified
```