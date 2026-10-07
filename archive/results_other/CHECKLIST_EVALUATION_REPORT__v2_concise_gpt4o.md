# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-06-19 19:29
**Judges:** openai:gpt-4o
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 8.50/25 | 34.0% | 4.33/9 | 48.1% |
| KG | 8.82/25 | 35.3% | 5.05/9 | 56.1% |
| RAG | 8.50/25 | 34.0% | 4.53/9 | 50.3% |
| HYBRID | 8.72/25 | 34.9% | 4.70/9 | 52.2% |

### KG vs Baseline

- Total improvement: +1.3% (1.04x)
- KG-relevant improvement: +8.0% (1.17x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o | 34.0% (340/1000) | 35.3% (353/1000) | 34.0% (340/1000) | 34.9% (349/1000) |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 32% | 55% | +23% |
| F4 | Does the review warn about potential breaking changes or imp… | 88% | 92% | +4% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 90% | 98% | +8% |
| T2 | Does the review mention testing edge cases, error paths, or … | 60% | 60% | 0% |
| T3 | Does the review reference specific test files or suggest whi… | 52% | 75% | +23% |
| M1 | Does the review assess whether the change fits the existing … | 0% | 10% | +10% |
| M3 | Does the review check if public APIs or interfaces are prope… | 2% | 10% | +8% |
| C2 | Does the review check if similar problems are solved consist… | 8% | 5% | -3% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| hybrid | 7/25 (28.0%) | 2/9 (22.2%) |
| kg | 8/25 (32.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 3/9 (33.3%) |

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 6/9 (66.7%) |
| hybrid | 10/25 (40.0%) | 6/9 (66.7%) |
| kg | 12/25 (48.0%) | 7/9 (77.8%) |
| rag | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 3/9 (33.3%) |
| hybrid | 8/25 (32.0%) | 4/9 (44.4%) |
| kg | 9/25 (36.0%) | 4/9 (44.4%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 4/9 (44.4%) |
| hybrid | 10/25 (40.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 6/9 (66.7%) |
| hybrid | 9/25 (36.0%) | 6/9 (66.7%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 6/25 (24.0%) | 2/9 (22.2%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 5/9 (55.6%) |
| hybrid | 7/25 (28.0%) | 4/9 (44.4%) |
| kg | 5/25 (20.0%) | 3/9 (33.3%) |
| rag | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 4/9 (44.4%) |
| hybrid | 6/25 (24.0%) | 3/9 (33.3%) |
| kg | 7/25 (28.0%) | 4/9 (44.4%) |
| rag | 10/25 (40.0%) | 4/9 (44.4%) |

### PR #13

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 4/9 (44.4%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |
| rag | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 4/9 (44.4%) |
| hybrid | 7/25 (28.0%) | 4/9 (44.4%) |
| kg | 10/25 (40.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 3/9 (33.3%) |
| hybrid | 9/25 (36.0%) | 6/9 (66.7%) |
| kg | 7/25 (28.0%) | 3/9 (33.3%) |
| rag | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 4/9 (44.4%) |
| hybrid | 10/25 (40.0%) | 6/9 (66.7%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 3/9 (33.3%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 7/25 (28.0%) | 4/9 (44.4%) |
| rag | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #20

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |
| rag | 6/25 (24.0%) | 4/9 (44.4%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 4/9 (44.4%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #22

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 4/9 (44.4%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 7/9 (77.8%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 4/9 (44.4%) |
| hybrid | 8/25 (32.0%) | 4/9 (44.4%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 6/9 (66.7%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 10/25 (40.0%) | 6/9 (66.7%) |
| rag | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #27

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 2/9 (22.2%) |
| hybrid | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 10/25 (40.0%) | 6/9 (66.7%) |
| rag | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #28

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 4/9 (44.4%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #29

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 5/9 (55.6%) |
| hybrid | 8/25 (32.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #30

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #31

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #32

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 6/9 (66.7%) |
| hybrid | 10/25 (40.0%) | 6/9 (66.7%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |
| rag | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #33

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 8/25 (32.0%) | 5/9 (55.6%) |
| rag | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #34

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |
| rag | 6/25 (24.0%) | 2/9 (22.2%) |

### PR #35

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 9/25 (36.0%) | 4/9 (44.4%) |
| rag | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #36

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 6/9 (66.7%) |
| hybrid | 9/25 (36.0%) | 2/9 (22.2%) |
| kg | 13/25 (52.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 2/9 (22.2%) |

### PR #37

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| hybrid | 9/25 (36.0%) | 3/9 (33.3%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #38

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 5/9 (55.6%) |
| hybrid | 10/25 (40.0%) | 6/9 (66.7%) |
| kg | 9/25 (36.0%) | 4/9 (44.4%) |
| rag | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #39

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 5/9 (55.6%) |
| hybrid | 10/25 (40.0%) | 6/9 (66.7%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |
| rag | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #40

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 5/9 (55.6%) |
| hybrid | 11/25 (44.0%) | 7/9 (77.8%) |
| kg | 9/25 (36.0%) | 5/9 (55.6%) |
| rag | 11/25 (44.0%) | 7/9 (77.8%) |

### PR #41

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 2/9 (22.2%) |
| hybrid | 9/25 (36.0%) | 4/9 (44.4%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 6/25 (24.0%) | 2/9 (22.2%) |

### PR #42

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 6/9 (66.7%) |
| hybrid | 7/25 (28.0%) | 5/9 (55.6%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |
| rag | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #43

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 7/25 (28.0%) | 4/9 (44.4%) |
| hybrid | 10/25 (40.0%) | 6/9 (66.7%) |
| kg | 7/25 (28.0%) | 5/9 (55.6%) |
| rag | 7/25 (28.0%) | 4/9 (44.4%) |

### PR #44

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 4/9 (44.4%) |
| hybrid | 11/25 (44.0%) | 8/9 (88.9%) |
| kg | 10/25 (40.0%) | 7/9 (77.8%) |
| rag | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #45

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 5/9 (55.6%) |
| hybrid | 9/25 (36.0%) | 5/9 (55.6%) |
| kg | 12/25 (48.0%) | 7/9 (77.8%) |
| rag | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #46

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 3/9 (33.3%) |
| hybrid | 8/25 (32.0%) | 3/9 (33.3%) |
| kg | 7/25 (28.0%) | 2/9 (22.2%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #47

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 8/25 (32.0%) | 2/9 (22.2%) |
| hybrid | 8/25 (32.0%) | 2/9 (22.2%) |
| kg | 9/25 (36.0%) | 6/9 (66.7%) |
| rag | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #48

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 6/25 (24.0%) | 3/9 (33.3%) |
| hybrid | 6/25 (24.0%) | 3/9 (33.3%) |
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
