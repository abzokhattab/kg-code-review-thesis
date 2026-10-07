# Human study v4 — results (21 raters analysed, 2 partial excluded)

Rater ids are pseudonyms. The mapping to the self-reported names is in `RATER_PSEUDONYM_MAP.txt`, which must not be committed or quoted in the thesis.

## Primary — F3*
- mean KG-preference **0.698** (95% boot CI 0.619-0.774), n=21 raters
- Wilcoxon vs 0.5: p=0.0008, effective non-tie n=19, rank-biserial r=0.87

## Secondary — overall usefulness (estimation only)
- mean KG-preference **0.476** (95% boot CI 0.389-0.563)

## Exploratory — remaining criteria (Holm-corrected)
| criterion | mean | non-tie n | p (raw) | p (Holm) |
|---|---|---|---|---|
| F2* | 0.444 | 20 | 0.0445 | 0.1335 |
| T3 | 0.429 | 14 | 0.0293 | 0.1171 |
| Q5 | 0.460 | 14 | 0.1543 | 0.3086 |
| R1 | 0.405 | 18 | 0.0101 | 0.0505 |
| C6 | 0.464 | 17 | 0.3777 | 0.3777 |

## Descriptives
| PR | mean overall | mean F3* | mean difficulty | highlight used | n |
|---|---|---|---|---|---|
| 101 | 0.60 | 0.83 | 3.0 | 3/21 | 21 |
| 102 | 0.19 | 0.36 | 2.7 | 4/21 | 21 |
| 103 | 0.26 | 0.86 | 2.8 | 3/21 | 21 |
| 104 | 0.50 | 0.69 | 2.8 | 3/21 | 21 |
| 105 | 0.81 | 0.79 | 2.8 | 4/21 | 21 |
| 106 | 0.50 | 0.67 | 2.7 | 2/21 | 21 |

- median task time: 101.6s
- total GitHub-link clicks: 5
- difficulty distribution (1–5): 1=5, 2=47, 3=51, 4=18, 5=5
- F3* choices normalised to mode: kg=75, baseline=25, both=23, neither=3

### Both / neither by criterion
| criterion | both | neither |
|---|---|---|
| F3* | 23 | 3 |
| F2* | 49 | 5 |
| T3 | 74 | 0 |
| Q5 | 66 | 6 |
| R1 | 16 | 76 |
| C6 | 34 | 3 |

## A/B side balance
| PR | KG on A | KG on B |
|---|---|---|
| 101 | 9 | 12 |
| 102 | 13 | 8 |
| 103 | 10 | 11 |
| 104 | 10 | 11 |
| 105 | 10 | 11 |
| 106 | 11 | 10 |

## Rationale audit (for post-hoc coding)
| rater | PR | rationale |
|---|---|---|
| P01 | 102 | neither PR names what was the reason for the change, but B felt more concise on what's happening |
| P01 | 103 | even though A is better on files referenced, B just felt more like what I would want to read to get the info I need |
| P01 | 106 | neither shows what the usage string looked like before vs. after the fix |
| P03 | 101 | The main deciding factor is that Review A identifies additional affected integration points (sessions.py and api.py) and discusses how the change could affect request handling, whereas Review B's documentation concern is relatively minor for this PR. |
| P03 | 102 | The key reason is that B stays closer to the actual change. It correctly focuses on:  create_url_adapter TRUSTED_HOSTS default None invalid host patterns documentation potential 400 responses  Review A makes some questionable claims about logging.py and sessions.py being affected simply because they use request data/context. That's not necessarily a meaningful impact of this particular change. |
| P03 | 103 | The deciding factor is that A identifies more relevant behavioral edge cases for the actual bug fix, particularly the interaction of empty/None values with nl=False. |
| P03 | 104 | Review B contains a significant questionable recommendation: it suggests keeping the original behavior by optionally including the original request in history, which conflicts with the purpose of this PR—to eliminate the self-reference. |
| P03 | 106 | Review B stays closer to the actual PR: the change is in make_metavar(), so the important question is whether other parameter types that produce bracketed metavars could be affected and whether changing CLI output could affect consumers. |
| P04 | 101 | Review B better identifies the integration points and focuses on concrete risks from changing iterable detection, including other __getattr__-based wrappers. Review A adds a maintainability observation, but its documentation concern is less important for this narrowly scoped internal behavior change. |
| P04 | 102 | Review B is more grounded in the actual PR: it identifies the default None case and invalid host patterns, references the relevant implementation, tests, and documentation, and explains how misconfiguration can produce 400 responses. Review A makes a stronger claim about backward compatibility and names logging.py/sessions.py, but those impacts are less directly supported by the PR. |
| P04 | 103 | Review B identifies more concrete edge cases in the changed echo logic—especially None, empty strings, and nl=False—and connects them to specific tests. Review A does a better job naming potentially affected callers, but some of those references are less directly tied to the actual change. B also spots the match syntax compatibility concern, making it more useful overall. |
| P04 | 104 | Both reviews identify the changed resolve_redirects logic, the new test, and the gap around longer redirect chains. Review B gives a slightly clearer explanation of the API-compatibility risk, but its specific claims about __init__.py and api.py are not especially useful to this change. Review A is similarly actionable overall. |
| P04 | 105 | Review B gives more concrete, actionable coverage of the refactor: it identifies the synchronous-use risk, specific dependent files, and precise missing edge-case tests. Review A has useful concerns about async compatibility and nested/error cases, but B is more specific about where regressions could occur and ties those risks more directly to the changed context-management behavior. |
| P04 | 106 | Review B identifies the most important practical risk: changing CLI usage output could affect scripts or integrations that parse that output. It also correctly focuses on whether other bracketed metavar types are covered. Review A names more files and tests, but several of those references are less clearly relevant to this specific make_metavar change. |
| P08 | 101 | The deciding difference is that A stays closer to the actual PR change (prepare_body and its test), while B gains little from naming sessions.py and api.py and potentially overstates their direct relationship to prepare_body. |
| P08 | 102 | Review A stays closer to the actual PR: it names create_url_adapter, tests/test_request.py, and docs/config.rst, and identifies concrete gaps around the default None configuration and invalid host patterns. Review B adds claims about logging.py, sessions.py, and tests/test_instance_config.py that aren't clearly supported by the supplied PR details. The supplied PR explicitly documents that None means all hosts are valid. |
| P08 | 103 | Review B catches the concrete behavioral edge cases around None and nl=False, and it explicitly discusses the new match syntax. Review A names more callers, but its main concern about unsupported types is weaker because the implementation still converts other objects with str(message); the PR description explicitly says the cases are handled exhaustively. |
| P08 | 104 | Both reviews identify the same core risks: changing resp.history could affect existing integrations, and longer redirect chains need more testing. Review A names additional files, but the study explicitly says that naming more files isn't automatically better; those claimed dependencies aren't clearly established by the PR material. Review B is therefore about equally useful. |
| P08 | 105 | Review B identifies a broader compatibility risk: the refactor changes context management and could affect synchronous as well as asynchronous usage, including dependent components. Review A is more precise about tests and documentation, but it focuses mainly on async/backward-compatibility concerns and doesn't identify those potentially affected consumers. |
| P08 | 106 | The deciding difference is that B identifies a concrete compatibility consequence of changing user-visible usage output, whereas A mostly adds speculative concerns and references files that aren't clearly affected. |
| P09 | 102 | A is more grounded in the actual diff: it identifies Flask.create_url_adapter, tests/test_request.py, and docs/config.rst, and it connects the configuration to possible 400 responses. B names more files, but that isn't automatically better—the mentions of logging.py and sessions.py are speculative and don't establish a concrete problem. B also claims an empty TRUSTED_HOSTS should allow all hosts, while the provided documentation only explicitly says None allows all hosts. |
| P10 | 101 | Review B identified additional files (sessions.py, api.py) that call prepare_body, which is important for understanding the full integration risk of this change |
| P10 | 102 | Review A identified additional affected files (logging.py, sessions.py) that rely on the request context, which is directly relevant because host validation could affect any component reading request.host |
| P10 | 103 | Review B identified the Python version compatibility issue with the match statement, which is a concrete and potentially breaking concern that Review A completely overlooked. It also flagged the untested nl=False scenario with None, which is directly related to the PR's changes. These specific, actionable points make Review B more valuable for ensuring a safe merge. |
| P10 | 105 | Review B identified potential regressions in synchronous code and named additional files that could be affected, which are important for assessing the full impact of the change. Review A focused mainly on async views and the test file, but missed the broader implications |
| P11 | 101 | Review B provide more details and names the affected code better and covers the important issues |
| P11 | 102 | both reviews identified the core issues, review B provided more details with suggested solutions. Review B also, catches the documentation gap. |
| P11 | 103 | Review A catches a critical Python version compatibility issue. The match statement was introduced in Python 3.10. While Review B does a good job looking at downstream usages of echo, its fundamental premise that changing a type hint from Any to object breaks runtime behavior is incorrect in Python. Review A's catch regarding syntax compatibility and edge cases (None, nl=False) makes it significantly more valuable to the author. |
| P11 | 104 | Review A correctly identifies the core issue with the PR. Review B is mostly fill up general text without pinning down the technical reason why. |
| P11 | 105 | Review B catches the most dangerous potential consequence of this PR: that refactoring a function to support async usage could inadvertently break all existing synchronous views relying on it. |
| P11 | 106 | Review A provides more files and edge cases and it shows the misunderstanding of the framework claiming that metavar changes will break parsing logic. |
| P14 | 101 | Review B is more useful because it points to more specific places that could be affected. Both find similar problems, but B gives clearer suggestions. |
| P14 | 102 | Review B is more useful because it identifies concrete failure cases around misconfigured hosts and invalid patterns. Review A is stronger on specific affected files and test locations, however some of its compatibility concerns are less convincing given the `None` default. |
| P14 | 103 | Review A is more useful. It focuses better on the main compatibility risk and missing tests. Review B raises a less important concern about older Python versions. |
| P14 | 104 | Review A is more useful because it points to more affected code and gives a more specific fix. Both reviews find similar risks and missing tests. |
| P14 | 105 | Review B is more useful because it points to more affected code and more specific cases that could fail. Both reviews find similar testing problems. |
| P14 | 106 | Review B is more useful because it identifies specific affected files, tests, and concrete edge cases. Review A raises similar concerns but is more general. |
| P16 | 103 | Review A identifies a critical defect that would break the entire library on older Python versions |
| P17 | 101 | These reviews are very similar in quality and coverage. The only real difference is that Review A briefly mentions code clarity/maintainability, while Review B names more dependent files (sessions.py, api.py). Neither advantage is decisive—the core analysis (risk of breaking existing callers, limited test coverage) is nearly identical in both. The PR is small and focused, and both reviews do an adequate job identifying the key concerns without being especially more specific than the other. |
| P17 | 102 | Both reviews identify the core risks correctly, but Review A is more concretely grounded. The key advantages of A are: (1) it names specific dependent files (logging.py, sessions.py) that could be affected, (2) it points to a specific existing test file (test_instance_config.py) where additional tests should go, and (3) it more clearly articulates the breaking change ("applications that relied on unrestricted host access"). Review B is competent but stays more general—saying "add tests for None" without naming where, and missing the specific dependent files. The difference is moderate but consistent. |
| P22 | 106 | mentioned missing test coverage and types |

## Ingestion audit
- feedback_accepted: 4
- payloads_seen: 138
- rating_rows_seen: 134
- rows_accepted: 134

## Partial sessions (excluded from inference)
- P15: 1/6 tasks
- P18: 4/6 tasks

## Free-text feedback
- **P03**: Great experiment!
- **P04**: Thank you to the author for putting together the PR Review Study! The comparisons were clear, practical, and useful for evaluating review quality.
- **P17**: - Interface was clear and easy to use.
- "Highlight what differs" was helpful.
- **P20**: Best wishes, 
el shahy shahin
