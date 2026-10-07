# KG-win attribution — `kg` vs `baseline` (n=40 PRs)

Source: `results/checklist_evaluation_llm_multi__v2.json` (3-judge majority). A *win* = treatment scored the criterion 1 and baseline 0 on the same PR.

## 1. Where do the wins land? (the placebo-band test)

| Criterion band | wins | losses | **net** | wins/PR |
|---|---:|---:|---:|---:|
| KG-relevant (9 criteria) | 42 | 18 | **+24** | 1.05 |
| Non-KG-relevant (16 criteria) | 34 | 33 | **+1** | 0.85 |

> If the KG lift were generic (longer/nicer reviews), wins would spread evenly. Concentration on the KG-relevant band is the signature of *context-caused* wins; the 16 non-KG criteria are a built-in negative control.

## 2. Per-criterion breakdown

| crit | KG-rel | wins | losses | net |
|---|:---:|---:|---:|---:|
| C1 | — | 0 | 0 | +0 |
| C2 | ✅ | 4 | 1 | +3 |
| F1 | — | 3 | 3 | +0 |
| F2 | — | 4 | 5 | -1 |
| F3 | ✅ | 11 | 2 | +9 |
| F4 | ✅ | 6 | 2 | +4 |
| M1 | ✅ | 7 | 2 | +5 |
| M2 | — | 0 | 0 | +0 |
| M3 | ✅ | 2 | 1 | +1 |
| P1 | — | 6 | 2 | +4 |
| P2 | — | 2 | 0 | +2 |
| Q1 | — | 0 | 0 | +0 |
| Q2 | ✅ | 0 | 0 | +0 |
| Q3 | — | 7 | 5 | +2 |
| Q4 | — | 0 | 0 | +0 |
| Q5 | — | 6 | 5 | +1 |
| R1 | — | 1 | 2 | -1 |
| R2 | — | 3 | 0 | +3 |
| R3 | — | 0 | 3 | -3 |
| S1 | — | 0 | 4 | -4 |
| S2 | — | 0 | 0 | +0 |
| S3 | — | 2 | 4 | -2 |
| T1 | ✅ | 1 | 1 | +0 |
| T2 | ✅ | 4 | 6 | -2 |
| T3 | ✅ | 7 | 3 | +4 |

## 3. Judge reasons for KG wins on KG-relevant criteria

Read each reason against the KG evidence pack (`data/luca_prs_v2/pr<ID>_evidence.json`: `callers`/`dependent_files`/`nearest_tests`). A grounded win cites a structural fact the baseline could not see.

### C2  (4 wins)
- **PR9** — The review suggests ensuring consistent behavior across different environments.
- **PR22** — Review suggests maintaining consistent package structure.
- **PR31** — The review suggests ensuring consistency and correctness in centering logic across the codebase.
- **PR45** — The review suggests consistency: 'Consider using a more dynamic approach to calculate the position adjustment.'

### F3  (11 wins)
- **PR9** — Review mentions: 'The IP address validation logic is added but lacks integration with existing configuration checks.'
- **PR12** — The review discusses potential integration issues with existing systems that rely on deterministic behavior.
- **PR13** — Review discusses the potential for incorrect behavior due to changes in logic, indicating integration concerns.
- **PR15** — Review discusses how changes in layout and button styles might affect existing UI.
- **PR31** — The review suggests reviewing other parts of the codebase for similar centering logic, indicating integration checks.
- **PR33** — Review discusses potential integration risks with other components relying on `OldDataMonitor`.
- **PR37** — Review discusses potential impacts on existing integrations due to changes in validation logic.
- **PR38** — The review recommends verifying that all components relying on `locationUtil` are tested.
- **PR39** — Review mentions potential integration issues: 'Changes in `GroupCoordinatorBaseRequestTest` might affect other tests'.
- **PR40** — Review discusses potential integration issues with components relying on metadata image updates.
- **PR47** — The review discusses the integration of offline cause retention logic in `Nodes.java`.

### F4  (6 wins)
- **PR12** — The review warns that using 'Math::rand()' could lead to non-deterministic behavior, impacting dependent code.
- **PR34** — Review warns about potential impact: 'The current implementation may lead to unexpected behavior if the sidebar state is altered by other components or user actions during edit mode.'
- **PR38** — The review warns that changes in URL handling might affect other components, leading to potential navigation issues.
- **PR39** — Review warns about backward compatibility: 'could lead to unexpected behavior in older versions'.
- **PR41** — The review warns that misconfigured DLQ topics could disrupt message processing, indicating potential impact on dependent code.
- **PR46** — The review warns about potential performance issues due to the integration of the undo/redo feature.

### M1  (7 wins)
- **PR9** — Review assesses integration with existing components, stating: 'the IP address validation logic is not fully integrated with existing configuration settings.'
- **PR21** — Review assesses the change's fit with existing architecture: 'the removal of Java version checks could lead to compatibility issues.'
- **PR22** — Review assesses the impact of changes on the existing architecture.
- **PR31** — The review assesses the change's fit with existing components by suggesting a review of similar logic.
- **PR40** — Review assesses integration with existing architecture: 'evaluate dependencies on metadata image updates across the codebase.'
- **PR41** — The review assesses the change's fit with existing architecture by discussing integration with `ShareGroupDLQStateManager`.
- **PR47** — The review assesses the change's impact on existing components and mentions potential misuse.

### M3  (2 wins)
- **PR6** — Review mentions incomplete documentation updates for the new configuration parameter.
- **PR10** — Review suggests updating documentation: 'Update documentation to reflect the new minimum joblib version.'

### T1  (1 wins)
- **PR14** — Review asks for comprehensive tests for the 'size' property.

### T2  (4 wins)
- **PR8** — The review specifically mentions testing edge cases and backward compatibility.
- **PR36** — Review suggests expanding test cases to cover additional edge cases, such as null values or unexpected data types.
- **PR42** — Review suggests: 'Add more tests to cover edge cases'.
- **PR43** — The review implies the need to test various scenarios where `check_array` might be used.

### T3  (7 wins)
- **PR1** — Review references the specific setting `xr/openxr/startup_alert` for which tests should be added.
- **PR14** — Review references specific test files that need updates to cover the new 'size' property.
- **PR15** — Review references specific test files that need updates to reflect new selectors.
- **PR19** — Review references specific test files: 'No direct tests in test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java or core/src/test/java/org/jenkins/ui/icon/IconSetTest.java.'
- **PR33** — Review references specific test files and suggests adding tests for the new behavior of `OldDataMonitor`.
- **PR36** — Review references specific test files: 'pkg/storage/unified/testing/storage_backend.go' and suggests updates.
- **PR37** — Review references specific test files: 'pkg/storage/unified/resource/storage_backend_test.go:1078-136'.
