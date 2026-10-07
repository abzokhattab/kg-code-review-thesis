# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-04-25 03:29
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 8.25/25 | 33.0% | 4.25/9 | 47.2% |
| KG | 8.56/25 | 34.2% | 4.69/9 | 52.1% |
| RAG | 8.56/25 | 34.2% | 4.94/9 | 54.9% |
| HYBRID | 9.12/25 | 36.5% | 5.25/9 | 58.3% |

### KG vs Baseline

- Total improvement: +1.2% (1.04x)
- KG-relevant improvement: +4.9% (1.10x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | 31.5% (126/400) | 36.0% (144/400) | 35.2% (141/400) | 38.8% (155/400) |
| openai:gpt-4o | 32.8% (131/400) | 32.8% (131/400) | 32.8% (131/400) | 34.5% (138/400) |
| gemini:gemini-2.5-flash | 41.6% (165/397) | 42.8% (163/381) | 43.0% (172/400) | 45.7% (175/383) |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 1600 | 1377 | 86.1% | 0.691 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 1561 | 1211 | 77.6% | 0.533 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 1561 | 1320 | 84.6% | 0.677 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 19% | 38% | +19% |
| F4 | Does the review warn about potential breaking changes or imp… | 75% | 75% | 0% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 88% | 100% | +12% |
| T2 | Does the review mention testing edge cases, error paths, or … | 44% | 50% | +6% |
| T3 | Does the review reference specific test files or suggest whi… | 44% | 75% | +31% |
| M1 | Does the review assess whether the change fits the existing … | 12% | 12% | 0% |
| M3 | Does the review check if public APIs or interfaces are prope… | 25% | 12% | -13% |
| C2 | Does the review check if similar problems are solved consist… | 19% | 6% | -13% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 7/9 (77.8%) |
| hybrid | 11/25 (44.0%) | 7/9 (77.8%) |
| kg | 11/25 (44.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 2/9 (22.2%) |
| hybrid | 10/25 (40.0%) | 4/9 (44.4%) |
| kg | 6/25 (24.0%) | 3/9 (33.3%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 6/9 (66.7%) |
| hybrid | 11/25 (44.0%) | 7/9 (77.8%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #7

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 1/9 (11.1%) |
| hybrid | 8/25 (32.0%) | 2/9 (22.2%) |
| kg | 9/25 (36.0%) | 3/9 (33.3%) |
| rag | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 4/9 (44.4%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |
| rag | 10/25 (40.0%) | 7/9 (77.8%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 5/9 (55.6%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |
| rag | 6/25 (24.0%) | 3/9 (33.3%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 6/9 (66.7%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 4/9 (44.4%) |
| hybrid | 10/25 (40.0%) | 7/9 (77.8%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 6/9 (66.7%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 7/9 (77.8%) |
| hybrid | 8/25 (32.0%) | 7/9 (77.8%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 7/9 (77.8%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 5/9 (55.6%) |
| hybrid | 11/25 (44.0%) | 7/9 (77.8%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 4/9 (44.4%) |
| hybrid | 6/25 (24.0%) | 4/9 (44.4%) |
| kg | 8/25 (32.0%) | 6/9 (66.7%) |
| rag | 6/25 (24.0%) | 4/9 (44.4%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 3/9 (33.3%) |
| hybrid | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |
| rag | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 2/9 (22.2%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 3/9 (33.3%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |
| rag | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #25

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 5/9 (55.6%) |
| hybrid | 7/25 (28.0%) | 3/9 (33.3%) |
| kg | 7/25 (28.0%) | 4/9 (44.4%) |
| rag | 9/25 (36.0%) | 3/9 (33.3%) |

### PR #26

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| hybrid | 11/25 (44.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 3/9 (33.3%) |
| rag | 10/25 (40.0%) | 4/9 (44.4%) |

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
