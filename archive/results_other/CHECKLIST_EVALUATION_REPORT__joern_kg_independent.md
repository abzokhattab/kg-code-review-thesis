# PR Review Evaluation Report (Multi-Judge LLM Panel)

**Generated:** 2026-10-04 20:15
**Judges:** anthropic:claude-sonnet-4-5, deepseek:deepseek-v4-pro, xai:grok-4.6
**Aggregation:** majority vote (ties → 0)
**Criteria:** 25 (9 KG-relevant)

---
## Average Scores by Mode (majority vote)

| Mode | Total | % | KG-Relevant | KG % |
|------|-------|---|-------------|------|
| KG | 8.26/25 | 33.0% | 5.14/9 | 57.2% |

---
## Per-judge Yes rates by mode

| Judge | BASELINE | KG | RAG | HYBRID |
|-------|---|---|---|---|
| anthropic:claude-sonnet-4-5 | — | 42.4% (371/875) | — | — |
| deepseek:deepseek-v4-pro | — | 32.3% (283/875) | — | — |
| xai:grok-4.6 | — | 31.4% (275/875) | — | — |

## Inter-judge agreement (across all (PR × mode × criterion) cells)

| Pair | Cells | Agreed | % | Cohen's κ |
|------|-------|--------|---|-----------|
| anthropic:claude-sonnet-4-5 vs deepseek:deepseek-v4-pro | 875 | 769 | 87.9% | 0.744 |
| anthropic:claude-sonnet-4-5 vs xai:grok-4.6 | 875 | 771 | 88.1% | 0.748 |
| deepseek:deepseek-v4-pro vs xai:grok-4.6 | 875 | 841 | 96.1% | 0.911 |

---
## KG-relevant criteria: baseline vs KG (majority vote)

| Criterion | Description | Baseline | KG | Δ |
|-----------|-------------|----------|----|----|
| F3 | Does the review check how the change integrates with existin… | 0% | 77% | +77% |
| F4 | Does the review warn about potential breaking changes or imp… | 0% | 71% | +71% |
| T1 | Does the review ask about or discuss the need for unit/integ… | 0% | 94% | +94% |
| T2 | Does the review mention testing edge cases, error paths, or … | 0% | 66% | +66% |
| T3 | Does the review reference specific test files or suggest whi… | 0% | 74% | +74% |
| M1 | Does the review assess whether the change fits the existing … | 0% | 14% | +14% |
| M3 | Does the review check if public APIs or interfaces are prope… | 0% | 11% | +11% |
| C2 | Does the review check if similar problems are solved consist… | 0% | 6% | +6% |
| Q2 | Are review comments anchored to specific code locations (fil… | 0% | 100% | +100% |

---
## Per-PR results

### PR #1

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #2

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #3

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 5/25 (20.0%) | 3/9 (33.3%) |

### PR #6

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 12/25 (48.0%) | 7/9 (77.8%) |

### PR #8

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #10

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #12

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 6/25 (24.0%) | 3/9 (33.3%) |

### PR #13

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #14

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #15

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 3/25 (12.0%) | 1/9 (11.1%) |

### PR #18

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 5/9 (55.6%) |

### PR #19

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #20

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 6/25 (24.0%) | 4/9 (44.4%) |

### PR #21

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 4/9 (44.4%) |

### PR #22

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #23

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #24

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #28

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #29

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #30

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #31

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 7/9 (77.8%) |

### PR #32

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #33

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 10/25 (40.0%) | 6/9 (66.7%) |

### PR #34

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #38

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 6/9 (66.7%) |

### PR #39

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 5/9 (55.6%) |

### PR #40

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 7/9 (77.8%) |

### PR #41

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 4/9 (44.4%) |

### PR #42

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #43

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 5/9 (55.6%) |

### PR #44

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 9/25 (36.0%) | 7/9 (77.8%) |

### PR #45

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 11/25 (44.0%) | 7/9 (77.8%) |

### PR #46

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 6/25 (24.0%) | 4/9 (44.4%) |

### PR #47

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 8/25 (32.0%) | 5/9 (55.6%) |

### PR #48

| Mode | Score (maj) | KG-Relevant |
|------|-------------|-------------|
| kg | 7/25 (28.0%) | 4/9 (44.4%) |

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
