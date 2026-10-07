# Slack reply draft (2026-07-21, v5 — natural voice)

Same verified numbers as v4:
- PR18 quote: results/RAG_WIN_ATTRIBUTION.md (C2, literal judge citation)
- Win split: KG_WIN_ATTRIBUTION.md §1 (+24 on 9 dep criteria vs +1 on
  other 16); RAG spread even (+17/+18)
- Visibility: INJECTION_EXP2_RESULTS.md (local bands 83-100% all arms,
  structural baseline 0/28)
- Precision: same file (kg 15/28 vs hybrid 12/28)

---

Good question, I've been thinking about exactly this. I'd say there are
two more factors that show up in the data:

Similarity is the second signal, that's basically what RAG contributes.
For example in one of the PRs the author added null checks in his own
style, and the RAG review told him to standardize them the way the rest
of the codebase does it, because it had retrieved similar code. The KG
could never make that comment since it only knows the dependency
structure. You can also see it in where the wins land: the KG gains are
almost entirely on the 9 dependency criteria, while RAG's are spread
over all 25.

And then there are two conditions for any of this context to matter.
First the problem has to be hidden from the diff: in experiment 2, bugs
that were visible in the diff got caught by every setup including the
baseline (83-100%), while cross-file bugs got caught by the baseline
exactly never (0/28). Second the context has to stay focused. KG alone
catches 15/28 of the cross-file bugs but KG+RAG together only 12/28,
the retrieved files basically drown out the one caller that matters.

So dependency + similarity as the two signals, and they only pay off
when the diff hides the problem and the context isn't diluted.
