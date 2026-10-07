# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-05-14 20:58
**Judges:** gemini:gemini-2.5-flash, anthropic:claude-sonnet-4-20250514
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 11.00/25 | 44.0% | 5.75/9 | 63.9% |
| KG | 8.75/25 | 35.0% | 4.67/9 | 51.9% |

### KG vs Baseline

- Total improvement: -9.0% (0.80x)
- KG-relevant improvement: -12.0% (0.81x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| gemini:gemini-2.5-flash | 50.3% (151/300) | 40.7% (122/300) | — | — |
| anthropic:claude-sonnet-4-20250514 | 48.4% (133/275) | 41.7% (125/300) | — | — |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| gemini:gemini-2.5-flash vs anthropic:claude-sonnet-4-20250514 | 575 | 504 | 87.7% | 0.751 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 75% | 75% | 0% |
| F4 | Does the review warn about potential breaking changes or imp… | 75% | 67% | -8% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 83% | 83% | 0% |
| T2 | Does the review mention testing edge cases, error paths, or … | 83% | 58% | -25% |
| T3 | Does the review reference specific test files or suggest whi… | 83% | 75% | -8% |
| M1 | Does the review assess whether the change fits the existing … | 33% | 8% | -25% |
| M3 | Does the review check if public APIs or interfaces are prope… | 8% | 0% | -8% |
| C2 | Does the review check if similar problems are solved consist… | 33% | 0% | -33% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| kg | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 11/25 (44.0%) | 5/9 (55.6%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 2/25 (8.0%) | 1/9 (11.1%) |

### PR #4

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #5

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 5/9 (55.6%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 6/9 (66.7%) |
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #7

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 8/9 (88.9%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 8/9 (88.9%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #11

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 4/9 (44.4%) |
| kg | 5/25 (20.0%) | 1/9 (11.1%) |

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
