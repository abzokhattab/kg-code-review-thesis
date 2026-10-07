# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-04-25 02:46
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | — | — | — | — |
| openai:gpt-4o | — | — | — | — |
| gemini:gemini-2.5-flash | — | — | — | — |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 125 | 111 | 88.8% | 0.739 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 125 | 103 | 82.4% | 0.591 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 125 | 107 | 85.6% | 0.654 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 0% | 0% | 0% |
| F4 | Does the review warn about potential breaking changes or imp… | 0% | 0% | 0% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 0% | 0% | 0% |
| T2 | Does the review mention testing edge cases, error paths, or … | 0% | 0% | 0% |
| T3 | Does the review reference specific test files or suggest whi… | 0% | 0% | 0% |
| M1 | Does the review assess whether the change fits the existing … | 0% | 0% | 0% |
| M3 | Does the review check if public APIs or interfaces are prope… | 0% | 0% | 0% |
| C2 | Does the review check if similar problems are solved consist… | 0% | 0% | 0% |
| Q2 | Are review comments anchored to specific code locations (fil… | 0% | 0% | 0% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kgempty | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #5

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kgempty | 7/25 (28.0%) | 2/9 (22.2%) |

### PR #11

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kgempty | 3/25 (12.0%) | 1/9 (11.1%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kgempty | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #13

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kgempty | 8/25 (32.0%) | 5/9 (55.6%) |

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
