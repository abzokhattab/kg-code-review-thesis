# Hallucination audit — PARITY Joern reviews (n=35)

**Difference from the buggy-run audit:** under parity the LLM has the PR body
in its prompt. PR bodies often contain `Reviewers:` lines (Apache Kafka)
or `cc @user` mentions. An owner/author/handle is therefore only a fabrication
if the name does **not** appear in the body.

## Summary

- Reviews audited: **35**
- Reviews with ≥1 unverified file citation: **10** (29%)
- Owner claim *grounded in body*: **7** | *fabricated*: **3** | *abstained ("Not specified")*: **13**
- Reviews with `@handle`: **verified-from-body 6**, **fabricated 0**
- Reviews naming a team: **1** (manually inspect for fabrication)

## Per-PR detail

| PR | unverified files | verified owner-claim | **fabricated owner-claim** | abstain |
|---:|:---|:---|:---|:---|
| 10 |  |  | **Code Owners: sklearn/utils, sklearn/pipeline** |  |
| 12 |  |  | **** | Code Owners: Not specified |
| 13 |  |  | **** | Code Owners: Not specified |
| 14 | packages/grafana-ui/src/components/Drawer/Drawer.story.ts, packages/grafana-ui/src/components/Drawer/Drawer.ts, public/app/features/dashboard/components/HelpWizard/HelpWizard.ts |  | **** |  |
| 15 | packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/CalendarHeader.ts, packages/grafana-ui/src/components/DateTimePickers/TimeRangePicker/TimeRangeContent.ts, public/locales/de-DE/grafana.js, public/locales/es-ES/grafana.js |  | **** | Code Owners: Not specified |
| 18 |  |  | **** |  |
| 19 | DirectoryBrowserSupportTest.java, test/src/test/java/hudson/model/DirectoryBrowserSupportTest.java |  | **** | Code Owners: Not specified |
| 1 |  |  | **** |  |
| 20 |  |  | **** |  |
| 21 |  |  | **** |  |
| 22 |  |  | **** | Code Owners: Not specified |
| 23 |  |  | **** |  |
| 24 |  | Code Owners: @OmarManzoor, @glemaitre | **** |  |
| 28 |  |  | **** | Code Owners: Not specified |
| 29 |  | Code Owners: Ken Huang <s7133700@gmail.com>, Chia-Ping Tsai <chia7712@gmail.com> | **** |  |
| 2 |  |  | **** | Code Owners: Not specified |
| 30 |  |  | **** |  |
| 31 |  |  | **Code owners: sklearn/linear_model team** |  |
| 32 | sklearn/metrics/tests/test_ranking.py |  | **** | Code Owners: Not specified |
| 33 |  |  | **** |  |
| 34 | public/app/features/dashboard-scene/scene/DashboardSceneRenderer.ts |  | **** |  |
| 38 |  |  | **** | Code Owners: Not specified |
| 39 |  | Code Owners: Sean Quah <squah@confluent.io> | **** |  |
| 3 | public/app/features/expressions/components/Reduce.ts |  | **** |  |
| 40 |  | Code Owners: Sean Quah <squah@confluent.io> | **** |  |
| 41 |  | Code Owners: Apoorv Mittal <apoorvmittal10@gmail.com>, Andrew Schofield <aschofield@confluent.io> | **** |  |
| 42 | sklearn/tree/_criterion.py, utils/_sorting.py |  | **Code Owners: sklearn/tree/ and sklearn/utils/ teams** |  |
| 43 |  |  | **** | Code Owners: Not specified |
| 44 | sklearn/ensemble/_hist_gradient_boosting/_predictor.py, sklearn/utils/_bitset.py |  | **** | Code Owners: Not specified |
| 45 |  |  | **** |  |
| 46 |  |  | **** |  |
| 47 |  | Code Owners: Jenkins core team | **** |  |
| 48 | AbstractLazyLoadRunMapTest.java, BuildReferenceMapAdapterTest.java | Code Owners: @jglick, @timja, @bennettzhu1 | **** |  |
| 6 |  |  | **** | Code Owners: Not specified |
| 8 | public/app/features/dashboard-scene/settings/variables/components/AdHocVariableForm.test.ts, public/app/features/dashboard-scene/settings/variables/components/CustomVariableForm.test.ts |  | **** | Code Owners: Not specified |

## Reading

**File-citation hallucination rate** is the headline number — it does not depend
on body access (the LLM cannot infer *paths* from the body if they aren't there).
Compare to the buggy-run rate (10/35, 29%) to see whether body access reduces
path-fabrication.

**Fabricated owners** are the most damning failure: even with the body in
context, the LLM invents authorial metadata. PR31's `Danilo Silva` was the
buggy-run example; check the parity column for whether it persists.
