# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-04-25 02:20
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 14.20/25 | 56.8% | 7.80/9 | 86.7% |
| KG | 13.80/25 | 55.2% | 7.80/9 | 86.7% |
| RAG | 14.20/25 | 56.8% | 7.20/9 | 80.0% |
| HYBRID | 14.40/25 | 57.6% | 8.00/9 | 88.9% |

### KG vs Baseline

- Total improvement: -1.6% (0.97x)
- KG-relevant improvement: +0.0% (1.00x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | 46.4% (58/125) | 54.4% (68/125) | 55.2% (69/125) | 58.4% (73/125) |
| openai:gpt-4o | 59.2% (74/125) | 56.8% (71/125) | 58.4% (73/125) | 61.6% (77/125) |
| gemini:gemini-2.5-flash | 55.3% (68/123) | 52.1% (61/117) | 58.1% (61/105) | 53.0% (53/100) |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 500 | 421 | 84.2% | 0.68 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 445 | 340 | 76.4% | 0.525 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 445 | 388 | 87.2% | 0.74 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 100% | 100% | 0% |
| F4 | Does the review warn about potential breaking changes or imp… | 80% | 100% | +20% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 100% | 100% | 0% |
| T2 | Does the review mention testing edge cases, error paths, or … | 80% | 80% | 0% |
| T3 | Does the review reference specific test files or suggest whi… | 100% | 100% | 0% |
| M1 | Does the review assess whether the change fits the existing … | 100% | 100% | 0% |
| M3 | Does the review check if public APIs or interfaces are prope… | 40% | 20% | -20% |
| C2 | Does the review check if similar problems are solved consist… | 80% | 80% | 0% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 16/25 (64.0%) | 8/9 (88.9%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 5/9 (55.6%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 9/9 (100.0%) |
| hybrid | 15/25 (60.0%) | 9/9 (100.0%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 7/9 (77.8%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 9/9 (100.0%) |
| hybrid | 13/25 (52.0%) | 9/9 (100.0%) |
| kg | 13/25 (52.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 9/9 (100.0%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 17/25 (68.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 7/9 (77.8%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 7/9 (77.8%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 6/9 (66.7%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 12/25 (48.0%) | 7/9 (77.8%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

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
