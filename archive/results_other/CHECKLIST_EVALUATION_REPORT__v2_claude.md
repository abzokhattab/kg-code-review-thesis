# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-06-01 01:44
**Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| BASELINE | 14.12/25 | 56.5% | 7.22/9 | 80.3% |
| KG | 14.43/25 | 57.7% | 7.38/9 | 82.0% |
| RAG | 14.20/25 | 56.8% | 7.22/9 | 80.3% |
| HYBRID | 14.12/25 | 56.5% | 7.33/9 | 81.4% |

### KG vs Baseline

- Total improvement: +1.2% (1.02x)
- KG-relevant improvement: +1.7% (1.02x)

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| openai:gpt-4o-mini | 54.7% (506/925) | 55.8% (502/900) | 56.2% (506/900) | 55.4% (512/925) |
| openai:gpt-4o | 56.8% (525/925) | 57.7% (519/900) | 57.6% (518/900) | 56.9% (526/925) |
| gemini:gemini-2.5-flash | 54.3% (542/999) | 56.0% (560/1000) | 54.6% (546/1000) | 54.9% (549/1000) |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| openai:gpt-4o-mini vs openai:gpt-4o | 3650 | 3150 | 86.3% | 0.722 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 3649 | 2909 | 79.7% | 0.59 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 3649 | 3133 | 85.9% | 0.713 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 92% | 100% | +8% |
| F4 | Does the review warn about potential breaking changes or imp… | 95% | 98% | +3% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 98% | 95% | -3% |
| T2 | Does the review mention testing edge cases, error paths, or … | 88% | 85% | -3% |
| T3 | Does the review reference specific test files or suggest whi… | 85% | 95% | +10% |
| M1 | Does the review assess whether the change fits the existing … | 80% | 90% | +10% |
| M3 | Does the review check if public APIs or interfaces are prope… | 25% | 12% | -13% |
| C2 | Does the review check if similar problems are solved consist… | 60% | 62% | +2% |
| Q2 | Are review comments anchored to specific code locations (fil… | 100% | 100% | 0% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 9/9 (100.0%) |

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 13/25 (52.0%) | 7/9 (77.8%) |
| rag | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 8/9 (88.9%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 6/9 (66.7%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 13/25 (52.0%) | 6/9 (66.7%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 15/25 (60.0%) | 7/9 (77.8%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #9

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 9/9 (100.0%) |
| hybrid | 14/25 (56.0%) | 9/9 (100.0%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 7/9 (77.8%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 12/25 (48.0%) | 6/9 (66.7%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #13

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 17/25 (68.0%) | 9/9 (100.0%) |
| hybrid | 14/25 (56.0%) | 6/9 (66.7%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 9/9 (100.0%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 9/9 (100.0%) |
| rag | 14/25 (56.0%) | 9/9 (100.0%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 15/25 (60.0%) | 7/9 (77.8%) |
| kg | 15/25 (60.0%) | 7/9 (77.8%) |
| rag | 13/25 (52.0%) | 7/9 (77.8%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 8/9 (88.9%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 18/25 (72.0%) | 9/9 (100.0%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 8/9 (88.9%) |
| hybrid | 11/25 (44.0%) | 7/9 (77.8%) |
| kg | 12/25 (48.0%) | 7/9 (77.8%) |
| rag | 11/25 (44.0%) | 6/9 (66.7%) |

### PR #20

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 8/9 (88.9%) |
| hybrid | 11/25 (44.0%) | 7/9 (77.8%) |
| kg | 13/25 (52.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 8/9 (88.9%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 7/9 (77.8%) |

### PR #22

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 6/9 (66.7%) |
| hybrid | 12/25 (48.0%) | 6/9 (66.7%) |
| kg | 10/25 (40.0%) | 6/9 (66.7%) |
| rag | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 19/25 (76.0%) | 9/9 (100.0%) |
| hybrid | 18/25 (72.0%) | 8/9 (88.9%) |
| kg | 18/25 (72.0%) | 8/9 (88.9%) |
| rag | 16/25 (64.0%) | 7/9 (77.8%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 8/9 (88.9%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #27

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 13/25 (52.0%) | 6/9 (66.7%) |

### PR #28

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 12/25 (48.0%) | 7/9 (77.8%) |
| kg | 12/25 (48.0%) | 6/9 (66.7%) |
| rag | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #29

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #30

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 9/25 (36.0%) | 4/9 (44.4%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 11/25 (44.0%) | 6/9 (66.7%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #31

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 8/9 (88.9%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #32

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 12/25 (48.0%) | 5/9 (55.6%) |
| rag | 14/25 (56.0%) | 7/9 (77.8%) |

### PR #33

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 7/9 (77.8%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #34

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 5/9 (55.6%) |
| hybrid | 13/25 (52.0%) | 5/9 (55.6%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 13/25 (52.0%) | 5/9 (55.6%) |

### PR #35

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 5/9 (55.6%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 18/25 (72.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 7/9 (77.8%) |

### PR #36

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 18/25 (72.0%) | 8/9 (88.9%) |
| hybrid | 17/25 (68.0%) | 8/9 (88.9%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 16/25 (64.0%) | 8/9 (88.9%) |

### PR #37

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 14/25 (56.0%) | 7/9 (77.8%) |
| rag | 12/25 (48.0%) | 6/9 (66.7%) |

### PR #38

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 8/9 (88.9%) |
| hybrid | 15/25 (60.0%) | 7/9 (77.8%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 7/9 (77.8%) |

### PR #39

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 12/25 (48.0%) | 6/9 (66.7%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 15/25 (60.0%) | 7/9 (77.8%) |
| rag | 16/25 (64.0%) | 8/9 (88.9%) |

### PR #40

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 9/9 (100.0%) |
| hybrid | 16/25 (64.0%) | 9/9 (100.0%) |
| kg | 15/25 (60.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #41

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 5/9 (55.6%) |
| hybrid | 14/25 (56.0%) | 7/9 (77.8%) |
| kg | 13/25 (52.0%) | 5/9 (55.6%) |
| rag | 15/25 (60.0%) | 5/9 (55.6%) |

### PR #42

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 12/25 (48.0%) | 7/9 (77.8%) |
| rag | 16/25 (64.0%) | 8/9 (88.9%) |

### PR #43

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 15/25 (60.0%) | 8/9 (88.9%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 14/25 (56.0%) | 8/9 (88.9%) |
| rag | 14/25 (56.0%) | 8/9 (88.9%) |

### PR #44

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 11/25 (44.0%) | 7/9 (77.8%) |
| hybrid | 16/25 (64.0%) | 8/9 (88.9%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 15/25 (60.0%) | 8/9 (88.9%) |

### PR #45

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 13/25 (52.0%) | 7/9 (77.8%) |
| hybrid | 14/25 (56.0%) | 8/9 (88.9%) |
| kg | 16/25 (64.0%) | 8/9 (88.9%) |
| rag | 13/25 (52.0%) | 8/9 (88.9%) |

### PR #46

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 16/25 (64.0%) | 7/9 (77.8%) |
| hybrid | 17/25 (68.0%) | 7/9 (77.8%) |
| kg | 20/25 (80.0%) | 8/9 (88.9%) |
| rag | 18/25 (72.0%) | 8/9 (88.9%) |

### PR #47

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 17/25 (68.0%) | 8/9 (88.9%) |
| hybrid | 13/25 (52.0%) | 7/9 (77.8%) |
| kg | 17/25 (68.0%) | 8/9 (88.9%) |
| rag | 17/25 (68.0%) | 8/9 (88.9%) |

### PR #48

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| baseline | 14/25 (56.0%) | 7/9 (77.8%) |
| hybrid | 16/25 (64.0%) | 7/9 (77.8%) |
| kg | 10/25 (40.0%) | 5/9 (55.6%) |
| rag | 13/25 (52.0%) | 6/9 (66.7%) |

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
