# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-06-01 01:08
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 13.57/25 | 54.3% | 6.83/9 | 75.9% |
| KG | 14.05/25 | 56.2% | 7.03/9 | 78.1% |
| RAG | 14.25/25 | 57.0% | 7.15/9 | 79.5% |
| HYBRID | 13.85/25 | 55.4% | 7.03/9 | 78.1% |

### KG vs Baseline

- Total improvement: +1.9% (1.03x)
- KG-relevant improvement: +2.2% (1.03x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | 51.8% (518/1000) | 52.9% (529/1000) | 54.2% (542/1000) | 54.0% (540/1000) |
| openai:gpt-4o | 53.7% (537/1000) | 55.0% (550/1000) | 56.0% (560/1000) | 54.4% (544/1000) |
| gemini:gemini-2.5-flash | 52.5% (525/1000) | 55.7% (556/999) | 55.1% (551/1000) | 52.4% (524/1000) |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 4000 | 3460 | 86.5% | 0.728 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 3999 | 3234 | 80.9% | 0.615 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 3999 | 3494 | 87.4% | 0.746 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 88% | 90% | +2% |
| F4 | Does the review warn about potential breaking changes or imp… | 92% | 92% | 0% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 88% | 95% | +7% |
| T2 | Does the review mention testing edge cases, error paths, or … | 85% | 90% | +5% |
| T3 | Does the review reference specific test files or suggest whi… | 82% | 90% | +8% |
| M1 | Does the review assess whether the change fits the existing … | 78% | 82% | +4% |
| M3 | Does the review check if public APIs or interfaces are prope… | 10% | 8% | -2% |
| C2 | Does the review check if similar problems are solved consist… | 60% | 55% | -5% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 9/9 (100.0%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 15/25 (60.0%) | 7/9 (77.8%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 12/25 (48.0%) | 6/9 (66.7%) |
| rag | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 16/25 (64.0%) | 9/9 (100.0%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 5/9 (55.6%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 16/25 (64.0%) | 7/9 (77.8%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #13

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 7/9 (77.8%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 11/25 (44.0%) | 5/9 (55.6%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 8/9 (88.9%) |
| hybrid | 13/25 (52.0%) | 8/9 (88.9%) |
| kg | 13/25 (52.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 7/9 (77.8%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 16/25 (64.0%) | 7/9 (77.8%) |
| rag | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 6/9 (66.7%) |
| hybrid | 16/25 (64.0%) | 7/9 (77.8%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 16/25 (64.0%) | 8/9 (88.9%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 7/9 (77.8%) |
| hybrid | 13/25 (52.0%) | 8/9 (88.9%) |
| kg | 13/25 (52.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #20

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 8/9 (88.9%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 13/25 (52.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 6/9 (66.7%) |

### PR #22

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| hybrid | 12/25 (48.0%) | 6/9 (66.7%) |
| kg | 12/25 (48.0%) | 6/9 (66.7%) |
| rag | 13/25 (52.0%) | 6/9 (66.7%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 8/9 (88.9%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 17/25 (68.0%) | 9/9 (100.0%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #27

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 6/9 (66.7%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 16/25 (64.0%) | 9/9 (100.0%) |

### PR #28

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 8/9 (88.9%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |
| rag | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #29

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 13/25 (52.0%) | 6/9 (66.7%) |
| kg | 11/25 (44.0%) | 5/9 (55.6%) |
| rag | 11/25 (44.0%) | 4/9 (44.4%) |

### PR #30

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 10/25 (40.0%) | 4/9 (44.4%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 8/25 (32.0%) | 4/9 (44.4%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #31

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| hybrid | 14/25 (56.0%) | 6/9 (66.7%) |
| kg | 12/25 (48.0%) | 5/9 (55.6%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #32

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 11/25 (44.0%) | 5/9 (55.6%) |
| kg | 13/25 (52.0%) | 6/9 (66.7%) |
| rag | 11/25 (44.0%) | 3/9 (33.3%) |

### PR #33

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #34

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 5/9 (55.6%) |
| hybrid | 11/25 (44.0%) | 3/9 (33.3%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #35

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 17/25 (68.0%) | 8/9 (88.9%) |
| hybrid | 11/25 (44.0%) | 4/9 (44.4%) |
| kg | 16/25 (64.0%) | 7/9 (77.8%) |
| rag | 15/25 (60.0%) | 5/9 (55.6%) |

### PR #36

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 7/9 (77.8%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #37

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 15/25 (60.0%) | 7/9 (77.8%) |

### PR #38

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #39

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 12/25 (48.0%) | 5/9 (55.6%) |
| kg | 12/25 (48.0%) | 6/9 (66.7%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #40

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #41

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 13/25 (52.0%) | 6/9 (66.7%) |
| rag | 13/25 (52.0%) | 5/9 (55.6%) |

### PR #42

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 13/25 (52.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #43

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 6/9 (66.7%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #44

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 5/9 (55.6%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #45

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 16/25 (64.0%) | 7/9 (77.8%) |
| kg | 17/25 (68.0%) | 7/9 (77.8%) |
| rag | 15/25 (60.0%) | 7/9 (77.8%) |

### PR #46

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 6/9 (66.7%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 15/25 (60.0%) | 7/9 (77.8%) |
| rag | 17/25 (68.0%) | 7/9 (77.8%) |

### PR #47

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 13/25 (52.0%) | 8/9 (88.9%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #48

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 4/9 (44.4%) |
| hybrid | 11/25 (44.0%) | 4/9 (44.4%) |
| kg | 12/25 (48.0%) | 5/9 (55.6%) |
| rag | 11/25 (44.0%) | 4/9 (44.4%) |

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
