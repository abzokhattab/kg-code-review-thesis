# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-09-06 15:29
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| KG | 10.20/25 | 40.8% | 5.56/9 | 61.8% |

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | — | 41.6% (260/625) | — | — |
| openai:gpt-4o | — | 39.5% (247/625) | — | — |
| gemini:gemini-2.5-flash | — | 40.2% (251/625) | — | — |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 625 | 544 | 87.0% | 0.731 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 625 | 506 | 81.0% | 0.606 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 625 | 555 | 88.8% | 0.766 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 0% | 68% | +68% |
| F4 | Does the review warn about potential breaking changes or imp… | 0% | 92% | +92% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 0% | 100% | +100% |
| T2 | Does the review mention testing edge cases, error paths, or … | 0% | 76% | +76% |
| T3 | Does the review reference specific test files or suggest whi… | 0% | 76% | +76% |
| M1 | Does the review assess whether the change fits the existing … | 0% | 28% | +28% |
| M3 | Does the review check if public APIs or interfaces are prope… | 0% | 8% | +8% |
| C2 | Does the review check if similar problems are solved consist… | 0% | 8% | +8% |
| Q2 | Are review comments anchored to specific code locations (fil… | 0% | 100% | +100% |

---
## Per-PR results

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 7/9 (77.8%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 13/25 (52.0%) | 7/9 (77.8%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #27

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #28

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #31

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #33

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 14/25 (56.0%) | 7/9 (77.8%) |

### PR #36

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 14/25 (56.0%) | 7/9 (77.8%) |

### PR #37

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #38

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #40

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #41

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 5/9 (55.6%) |

### PR #44

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #47

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #48

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

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
