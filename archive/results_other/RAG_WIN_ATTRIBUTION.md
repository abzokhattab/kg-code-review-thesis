# KG-win attribution — `rag` vs `baseline` (n=40 PRs)

Source: `results/checklist_evaluation_llm_multi__v2.json` (3-judge majority). A *win* = treatment scored the criterion 1 and baseline 0 on the same PR.

## 1. Where do the wins land? (the placebo-band test)

| Criterion band | wins | losses | **net** | wins/PR |
|---|---:|---:|---:|---:|
| KG-relevant (9 criteria) | 38 | 21 | **+17** | 0.95 |
| Non-KG-relevant (16 criteria) | 39 | 21 | **+18** | 0.97 |

> If the KG lift were generic (longer/nicer reviews), wins would spread evenly. Concentration on the KG-relevant band is the signature of *context-caused* wins; the 16 non-KG criteria are a built-in negative control.

## 2. Per-criterion breakdown

| crit | KG-rel | wins | losses | net |
|---|:---:|---:|---:|---:|
| C1 | — | 1 | 0 | +1 |
| C2 | ✅ | 8 | 0 | +8 |
| F1 | — | 4 | 0 | +4 |
| F2 | — | 2 | 3 | -1 |
| F3 | ✅ | 5 | 4 | +1 |
| F4 | ✅ | 5 | 5 | +0 |
| M1 | ✅ | 11 | 2 | +9 |
| M2 | — | 0 | 0 | +0 |
| M3 | ✅ | 2 | 2 | +0 |
| P1 | — | 4 | 2 | +2 |
| P2 | — | 0 | 0 | +0 |
| Q1 | — | 0 | 0 | +0 |
| Q2 | ✅ | 0 | 0 | +0 |
| Q3 | — | 8 | 8 | +0 |
| Q4 | — | 0 | 0 | +0 |
| Q5 | — | 7 | 3 | +4 |
| R1 | — | 3 | 1 | +2 |
| R2 | — | 4 | 0 | +4 |
| R3 | — | 1 | 2 | -1 |
| S1 | — | 1 | 1 | +0 |
| S2 | — | 0 | 0 | +0 |
| S3 | — | 4 | 1 | +3 |
| T1 | ✅ | 0 | 0 | +0 |
| T2 | ✅ | 4 | 3 | +1 |
| T3 | ✅ | 3 | 5 | -2 |

## 3. Judge reasons for KG wins on KG-relevant criteria

Read each reason against the KG evidence pack (`data/luca_prs_v2/pr<ID>_evidence.json`: `callers`/`dependent_files`/`nearest_tests`). A grounded win cites a structural fact the baseline could not see.

### C2  (8 wins)
- **PR13** — Review suggests consistent application of vector operations.
- **PR15** — Review checks for consistency by discussing the use of data-testid over aria-label.
- **PR18** — Review suggests consistency: 'Standardize null and empty string checks across all modified files'.
- **PR19** — Review mentions: 'the naming convention is inconsistent with existing patterns.'
- **PR20** — Review checks for consistency in handling configuration flags across tests.
- **PR22** — Review suggests standardizing on a single assertion library for consistency.
- **PR27** — Review discusses potential inconsistencies with existing patterns for handling metadata.
- **PR41** — Review suggests consistent handling: 'Consolidate DLQ Topic Validation Logic'.

### F3  (5 wins)
- **PR15** — Review discusses how the changes may affect existing components and user experience.
- **PR33** — The review discusses changes in how `Saveable` objects are stored and retrieved, indicating integration concerns.
- **PR39** — Review discusses integration with existing components by mentioning `GroupCoordinatorBaseRequestTest` and `TxnOffsetCommitRequestTest`.
- **PR40** — Review discusses the integration with other components, specifically the impact of removing `metadataImage`.
- **PR47** — The review discusses the integration of changes in `Nodes.java` and its impact on existing functionality.

### F4  (5 wins)
- **PR12** — The review warns that using `Math::rand()` can lead to predictable values, impacting dependent code.
- **PR38** — The review warns that incorrect handling of URIs could lead to broken redirects, impacting user experience.
- **PR39** — Review warns about potential unexpected behavior due to 'topicId' usage.
- **PR41** — The review warns about potential runtime exceptions due to the lack of null checks, indicating a risk of breaking changes.
- **PR46** — The review warns that redundant or conflicting undo actions could confuse users, indicating potential impact on user experience.

### M1  (11 wins)
- **PR2** — Review assesses the change's impact on existing components and potential integration issues.
- **PR8** — Review assesses the handling of the 'allowCustomValue' feature in relation to existing components.
- **PR15** — Review assesses the impact of changes on the existing design system.
- **PR22** — Review assesses how the change fits with existing dependencies and modules.
- **PR27** — Review assesses the change's impact on existing architecture by discussing the `K8sMetadata` interface.
- **PR33** — The review assesses how the change in `OldDataMonitor` affects existing data handling.
- **PR40** — Review assesses the change's fit with existing architecture by discussing integration with components.
- **PR41** — The review assesses how the new implementation fits within the existing architecture of the DLQ manager.
- **PR44** — Review assesses integration with existing components, stating: 'the change might introduce integration issues with other parts of the codebase.'
- **PR47** — The review assesses the change's fit with existing components and warns about potential issues.
- **PR48** — Review assesses how the change integrates with existing components, particularly the `search` method.

### M3  (2 wins)
- **PR6** — Review mentions inconsistency in documentation: 'Inconsistency in documentation and usage.'
- **PR8** — Mentions the need for documentation updates: 'Update the documentation to include details about the new feature.'

### T2  (4 wins)
- **PR33** — The review mentions insufficient test coverage increases the risk of undetected regressions.
- **PR36** — The review suggests ensuring errors are correctly propagated and handled.
- **PR42** — Review specifically mentions testing edge cases such as empty arrays and arrays with duplicate values.
- **PR48** — Review specifically mentions testing edge cases and robustness for the new resolvers.

### T3  (3 wins)
- **PR24** — Review references specific test files and suggests reviewing the use of the 'enable_slep006' fixture.
- **PR33** — The review references specific test files, indicating tests related to memory management are insufficient.
- **PR37** — Review references specific test files and suggests adding stress tests.
