# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-09-06 16:42
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| KG | 10.26/25 | 41.0% | 5.71/9 | 63.5% |

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | — | 40.5% (314/775) | — | — |
| openai:gpt-4o | — | 37.9% (294/775) | — | — |
| gemini:gemini-2.5-flash | — | 41.5% (322/775) | — | — |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 775 | 661 | 85.3% | 0.692 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 775 | 623 | 80.4% | 0.595 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 775 | 677 | 87.4% | 0.736 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 0% | 77% | +77% |
| F4 | Does the review warn about potential breaking changes or imp… | 0% | 94% | +94% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 0% | 100% | +100% |
| T2 | Does the review mention testing edge cases, error paths, or … | 0% | 68% | +68% |
| T3 | Does the review reference specific test files or suggest whi… | 0% | 71% | +71% |
| M1 | Does the review assess whether the change fits the existing … | 0% | 32% | +32% |
| M3 | Does the review check if public APIs or interfaces are prope… | 0% | 19% | +19% |
| C2 | Does the review check if similar problems are solved consist… | 0% | 10% | +10% |
| Q2 | Are review comments anchored to specific code locations (fil… | 0% | 100% | +100% |

---
## Per-PR results

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 5/25 (20.0%) | 3/9 (33.3%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 8/9 (88.9%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 6/9 (66.7%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #22

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 4/9 (44.4%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #27

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 13/25 (52.0%) | 7/9 (77.8%) |

### PR #28

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #29

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #31

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #32

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #33

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #34

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #36

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 13/25 (52.0%) | 6/9 (66.7%) |

### PR #37

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #38

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #39

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #40

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #41

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #42

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #43

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #44

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #47

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #48

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 4/9 (44.4%) |

---
## Criteria definitions

### Functionality

- **F1**: Does the review verify that the change addresses the stated problem or requirement?
- **F2**: Does the review identify edge cases or boundary conditions that need handling?
- **F3**: Does the review check how the change integrates with existing components, APIs, or modules? (KG-relevant)
- **F4**: Does the review warn about potential breaking changes or impact on dependent code? (KG-relevant)
### Tests

- **T1**: Does the review ask about or discuss the need for unit/integration tests? (KG-relevant)
- **T2**: Does the review mention testing edge cases, error paths, or failure scenarios? (KG-relevant)
- **T3**: Does the review reference specific test files or suggest which tests should be added/updated? (KG-relevant)
### Readability

- **R1**: Does the review comment on code clarity, naming conventions, or function organization?
- **R2**: Does the review identify unnecessary complexity or suggest simplification?
- **R3**: Does the review check if code comments explain the 'why' behind decisions?
### Maintainability

- **M1**: Does the review assess whether the change fits the existing architecture or design patterns? (KG-relevant)
- **M2**: Does the review flag if the PR scope is too large or should be split?
- **M3**: Does the review check if public APIs or interfaces are properly documented? (KG-relevant)
### Consistency

- **C1**: Does the review check adherence to project style guides or coding conventions?
- **C2**: Does the review check if similar problems are solved consistently with existing patterns? (KG-relevant)
### Performance

- **P1**: Does the review identify potential performance issues or inefficiencies?
- **P2**: Does the review ask about benchmarks or performance testing for critical paths?
### Security

- **S1**: Does the review check for proper input validation or sanitization?
- **S2**: Does the review flag hardcoded secrets, credentials, or sensitive data?
- **S3**: Does the review assess error handling and failure recovery?
### Quality

- **Q1**: Does the review provide an overall summary or assessment of the changes?
- **Q2**: Are review comments anchored to specific code locations (file paths, line numbers)? (KG-relevant)
- **Q3**: Does the review distinguish between blocking issues and minor suggestions?
- **Q4**: Does the review ask clarifying questions rather than making assumptions?
- **Q5**: Does the review explain the reasoning behind suggestions (the 'why')?
