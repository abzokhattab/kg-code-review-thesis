# Hallucination audit — clean Joern reviews (n=35)

**Method:** for each review, extract every `file:line` citation, then verify
the file appears in the Joern evidence pack (changed files, callers, dependents,
or test list). Also flag any **named individual** (Code Owner / Author /
Maintainer fields) — the evidence pack contains *no* author data, so any named
person is a fabrication by construction. Same for teams and `@` handles.

## Summary

- Reviews audited: **35**
- Reviews with ≥1 unverified file citation: **10** (29%)
- Reviews naming a code owner / author / maintainer: **1** (3%) — **all are fabrications** (evidence has no author data)
- Reviews with `@handle` mentions: **0**
- Reviews naming a team: **2**

## Per-PR detail

| PR | unverified files | owners (fabricated) | handles | teams (fabricated) |
|---:|:---|:---|:---|:---|
| 10 | sklearn/tests/test_min_dependencies_readme.py |  |  |  |
| 12 |  |  |  |  |
| 13 |  |  |  |  |
| 14 | packages/grafana-ui/src/components/Drawer/Drawer.ts, public/app/core/components/AppChrome/News/NewsContainer.ts, public/app/features/dashboard/components/HelpWizard/HelpWizard.test.ts, public/app/features/dashboard/components/HelpWizard/HelpWizard.ts |  |  |  |
| 15 | CalendarFooter.ts, CalendarHeader.ts, packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarFooter.ts, packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarHeader.ts, packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimeRangeContent.ts … |  |  |  |
| 18 |  |  |  |  |
| 19 | test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java |  |  |  |
| 1 |  |  |  |  |
| 20 |  |  |  |  |
| 21 |  |  |  | Not specified |
| 22 |  |  |  |  |
| 23 |  |  |  |  |
| 24 |  |  |  |  |
| 28 |  |  |  |  |
| 29 |  |  |  |  |
| 2 |  |  |  |  |
| 30 |  |  |  |  |
| 31 |  | Danilo Silva |  | sklearn.linear_model maintainers |
| 32 |  |  |  |  |
| 33 |  |  |  |  |
| 34 | public/app/features/dashboard-scene/scene/DashboardSceneRenderer.ts |  |  |  |
| 38 |  |  |  |  |
| 39 |  |  |  |  |
| 3 | public/app/features/expressions/components/Reduce.ts, public/app/plugins/datasource/elasticsearch/hooks/useStatelessReducer.test.ts |  |  |  |
| 40 |  |  |  |  |
| 41 |  |  |  |  |
| 42 | sklearn/tree/_criterion.py, sklearn/tree/_partitioner.py, sklearn/utils/_sorting.py, utils/_sorting.py |  |  |  |
| 43 |  |  |  |  |
| 44 | sklearn/ensemble/_hist_gradient_boosting/_predictor.py, sklearn/utils/_bitset.py |  |  |  |
| 45 |  |  |  |  |
| 46 |  |  |  |  |
| 47 |  |  |  |  |
| 48 | AbstractLazyLoadRunMapTest.java, BuildReferenceMapAdapterTest.java, core/src/test/java/jenkins/model/lazy/AbstractLazyLoadRunMapTest.java |  |  |  |
| 6 |  |  |  |  |
| 8 | public/app/features/dashboard-scene/settings/variables/components/QueryVariableForm.test.ts |  |  |  |

## Reading

Unverified file citations include both **real hallucinations** (file does not
exist in the repo) and **soft hallucinations** (the model paraphrased a path,
e.g. shortened or guessed an extension). Both are review-quality defects.

Fabricated owners are unambiguous: the Joern evidence pack carries zero owner
metadata. Any named person in the review text is fully made up by the LLM.
This is the most concerning failure mode for thesis discussion (it's the
"shape of structural claims rewarded over correctness" pattern shown by PR31).
