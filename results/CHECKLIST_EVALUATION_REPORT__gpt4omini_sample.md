# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-04-24 17:12
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 10.80/25 | 43.2% | 6.00/9 | 66.7% |
| KG | 9.80/25 | 39.2% | 5.00/9 | 55.6% |
| RAG | 9.80/25 | 39.2% | 5.80/9 | 64.5% |
| HYBRID | 10.00/25 | 40.0% | 5.20/9 | 57.8% |

### KG vs Baseline

- Total improvement: -4.0% (0.91x)
- KG-relevant improvement: -11.1% (0.83x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | 45.6% (57/125) | 38.4% (48/125) | 45.6% (57/125) | 41.6% (52/125) |
| openai:gpt-4o | 39.2% (49/125) | 36.8% (46/125) | 36.8% (46/125) | 36.8% (46/125) |
| gemini:gemini-2.5-flash | 46.4% (51/110) | 39.2% (49/125) | 39.2% (40/102) | 46.0% (57/124) |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 500 | 417 | 83.4% | 0.655 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 461 | 372 | 80.7% | 0.605 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 461 | 393 | 85.2% | 0.693 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 40% | 20% | -20% |
| F4 | Does the review warn about potential breaking changes or imp… | 100% | 80% | -20% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 100% | 100% | 0% |
| T2 | Does the review mention testing edge cases, error paths, or … | 80% | 60% | -20% |
| T3 | Does the review reference specific test files or suggest whi… | 80% | 100% | +20% |
| M1 | Does the review assess whether the change fits the existing … | 20% | 0% | -20% |
| M3 | Does the review check if public APIs or interfaces are prope… | 40% | 0% | -40% |
| C2 | Does the review check if similar problems are solved consist… | 40% | 40% | 0% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| hybrid | 11/25 (44.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 4/9 (44.4%) |
| rag | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 6/9 (66.7%) |
| hybrid | 11/25 (44.0%) | 5/9 (55.6%) |
| kg | 11/25 (44.0%) | 5/9 (55.6%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 6/9 (66.7%) |
| hybrid | 7/25 (28.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 7/9 (77.8%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 13/25 (52.0%) | 6/9 (66.7%) |
| kg | 13/25 (52.0%) | 6/9 (66.7%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |
| rag | 7/25 (28.0%) | 4/9 (44.4%) |

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
