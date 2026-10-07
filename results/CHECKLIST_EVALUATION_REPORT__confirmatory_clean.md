# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-08-31 17:23
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 10.00/25 | 40.0% | 5.17/9 | 57.4% |
| KG | 10.42/25 | 41.7% | 5.58/9 | 62.1% |

### KG vs Baseline

- Total improvement: +1.7% (1.04x)
- KG-relevant improvement: +4.7% (1.08x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | 39.0% (117/300) | 41.3% (124/300) | — | — |
| openai:gpt-4o | 38.7% (116/300) | 38.7% (116/300) | — | — |
| gemini:gemini-2.5-flash | 42.7% (128/300) | 45.3% (136/300) | — | — |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 600 | 517 | 86.2% | 0.71 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 600 | 465 | 77.5% | 0.539 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 600 | 510 | 85.0% | 0.692 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 50% | 75% | +25% |
| F4 | Does the review warn about potential breaking changes or imp… | 83% | 100% | +17% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 100% | 92% | -8% |
| T2 | Does the review mention testing edge cases, error paths, or … | 83% | 83% | 0% |
| T3 | Does the review reference specific test files or suggest whi… | 67% | 67% | 0% |
| M1 | Does the review assess whether the change fits the existing … | 25% | 25% | 0% |
| M3 | Does the review check if public APIs or interfaces are prope… | 0% | 8% | +8% |
| C2 | Does the review check if similar problems are solved consist… | 8% | 8% | 0% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| kg | 11/25 (44.0%) | 7/9 (77.8%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 6/9 (66.7%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #4

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #5

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 11/25 (44.0%) | 5/9 (55.6%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #7

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 4/9 (44.4%) |
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 5/9 (55.6%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 6/9 (66.7%) |
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #11

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 6/9 (66.7%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 5/9 (55.6%) |
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
