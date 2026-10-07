# KG-win attribution — `hybrid` vs `baseline` (n=40 PRs)

Source: `results/checklist_evaluation_llm_multi__v2.json` (3-judge majority). A *win* = treatment scored the criterion 1 and baseline 0 on the same PR.

## 1. Where do the wins land? (the placebo-band test)

| Criterion band | wins | losses | **net** | wins/PR |
|---|---:|---:|---:|---:|
| KG-relevant (9 criteria) | 40 | 19 | **+21** | 1.00 |
| Non-KG-relevant (16 criteria) | 38 | 30 | **+8** | 0.95 |

> If the KG lift were generic (longer/nicer reviews), wins would spread evenly. Concentration on the KG-relevant band is the signature of *context-caused* wins; the 16 non-KG criteria are a built-in negative control.

## 2. Per-criterion breakdown

| crit | KG-rel | wins | losses | net |
|---|:---:|---:|---:|---:|
| C1 | — | 0 | 0 | +0 |
| C2 | ✅ | 4 | 1 | +3 |
| F1 | — | 3 | 3 | +0 |
| F2 | — | 3 | 6 | -3 |
| F3 | ✅ | 5 | 2 | +3 |
| F4 | ✅ | 5 | 1 | +4 |
| M1 | ✅ | 11 | 3 | +8 |
| M2 | — | 0 | 0 | +0 |
| M3 | ✅ | 2 | 2 | +0 |
| P1 | — | 4 | 2 | +2 |
| P2 | — | 1 | 0 | +1 |
| Q1 | — | 0 | 0 | +0 |
| Q2 | ✅ | 0 | 0 | +0 |
| Q3 | — | 9 | 10 | -1 |
| Q4 | — | 0 | 0 | +0 |
| Q5 | — | 7 | 1 | +6 |
| R1 | — | 1 | 3 | -2 |
| R2 | — | 6 | 0 | +6 |
| R3 | — | 0 | 3 | -3 |
| S1 | — | 1 | 1 | +0 |
| S2 | — | 1 | 0 | +1 |
| S3 | — | 2 | 1 | +1 |
| T1 | ✅ | 1 | 1 | +0 |
| T2 | ✅ | 5 | 3 | +2 |
| T3 | ✅ | 7 | 6 | +1 |

## 3. Judge reasons for KG wins on KG-relevant criteria

Read each reason against the KG evidence pack (`data/luca_prs_v2/pr<ID>_evidence.json`: `callers`/`dependent_files`/`nearest_tests`). A grounded win cites a structural fact the baseline could not see.

### C2  (4 wins)
- **PR12** — Mentions inconsistent error messaging with existing patterns
- **PR18** — Review suggests consistency: 'Ensure that the use of Commons Lang 3 is consistent across all test files.'
- **PR31** — The review suggests reviewing similar centering logic in other models to ensure consistency.
- **PR32** — Review suggests ensuring consistency in naming conventions across the codebase.

### F3  (5 wins)
- **PR3** — Review discusses the integration of notification logic within the Reduce component.
- **PR15** — Review checks integration by mentioning potential UI regression due to the change from Button to IconButton.
- **PR33** — The review discusses the change in data structure and its potential impact on object identity and persistence.
- **PR40** — Review discusses the impact of changes on other parts of the system.
- **PR47** — The review discusses how the change in `Nodes.java` directly manipulates the offline cause, indicating integration concerns.

### F4  (5 wins)
- **PR12** — Review warns that using `Math::rand()` can lead to non-deterministic behavior in multi-threaded environments.
- **PR34** — Review warns about potential race conditions that could impact the sidebar's visibility.
- **PR38** — The review warns that incorrect URL processing could lead to broken redirects.
- **PR41** — Review warns that the Interface Segregation Violation could lead to maintenance issues.
- **PR46** — The review warns about potential inconsistent undo states and user confusion, indicating a potential impact on dependent code.

### M1  (11 wins)
- **PR2** — Review assesses the change's fit with existing architecture by discussing backward compatibility.
- **PR8** — Review assesses how the change integrates with existing components and flags inconsistencies.
- **PR10** — Review assesses the change's fit with existing architecture regarding joblib's API.
- **PR15** — Review assesses the change's fit with existing components by discussing potential UI regression.
- **PR22** — Review assesses the impact of the change on module dependencies and package structure.
- **PR32** — Review assesses the change's fit with existing naming conventions and suggests reviewing other parts of the codebase.
- **PR33** — The review assesses the change's fit with existing components, particularly regarding memory management.
- **PR40** — Review assesses the change's impact on existing components.
- **PR41** — Review assesses the change in relation to existing design principles like the Interface Segregation Principle.
- **PR47** — The review assesses that the change could lead to inconsistent states, indicating a fit with existing architecture concerns.
- **PR48** — Review assesses the impact of changes on existing plugins and integrations.

### M3  (2 wins)
- **PR6** — Review suggests updating documentation: 'Update documentation to clearly explain the purpose and impact of the new configuration.'
- **PR10** — Review recommends documenting the minimum joblib version requirement in release notes and README.

### T1  (1 wins)
- **PR14** — The review discusses the need for comprehensive tests for the new 'size' property.

### T2  (5 wins)
- **PR8** — Review mentions the need to test edge cases, especially for existing dashboards.
- **PR33** — The review mentions insufficient testing of Run lifecycle changes, indicating a need to test edge cases.
- **PR36** — Review mentions ensuring that errors are properly logged or handled to prevent silent failures.
- **PR42** — Review suggests: 'Expand test coverage to include edge cases and performance tests for the sorting functions.'
- **PR43** — Review mentions the need to test different DataFrame shapes and types of sparse columns.

### T3  (7 wins)
- **PR3** — Review notes that no changes in test files related to the Reduce component were found.
- **PR14** — The review references specific code locations where tests should be added or updated.
- **PR15** — Review references specific test files that need updates to cover new data-testid attributes.
- **PR19** — Review suggests: 'Add or update tests in DirectoryBrowserSupportTest.java and other relevant test files.'
- **PR24** — Review references specific files and suggests adding tests for '_raise_for_params'.
- **PR33** — The review references specific test files and indicates that tests related to memory management are insufficient.
- **PR48** — Review specifies that no new test cases are added in `AbstractLazyLoadRunMapTest.java`.
