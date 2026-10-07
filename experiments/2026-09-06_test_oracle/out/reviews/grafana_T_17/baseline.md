```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming in the `frameComparisons` module.

## Problem
1. The function `compareArrayValuesInternal` is marked with a `@beta` tag, which suggests it might be intended for external use, yet the naming suggests internal use.
2. The renaming might affect other parts of the codebase if this function is used externally, but the PR does not include any updates to documentation or usage examples.

## Evidence
- `packages/grafana-data/src/dataframe/frameComparisons.ts:79`: The function `compareArrayValues` is renamed to `compareArrayValuesInternal`, but it retains the `@beta` tag.

## Impact
- The renaming could lead to confusion about the function's intended use, especially if it is part of a public API. This could result in breaking changes if external code relies on this function.
- Lack of documentation updates might lead to inconsistencies in how the function is used or understood by other developers.

## Recommendation (Fix / Tests / Risks)
1. Clarify the intended use of the function by either removing the `@beta` tag if it is truly internal or reconsidering the naming if it is meant for external use.
2. Conduct a search for any external references to this function to assess the impact of the renaming and update documentation accordingly.
3. Add tests or update existing ones to ensure that the renaming does not introduce any regressions.

## Traceability
Not specified
```