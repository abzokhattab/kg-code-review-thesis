# Slack message draft (2026-07-13, v2 — short & smooth)

Attachments: `EXPERIMENT_1_SUMMARY.pdf`, `EXPERIMENT_2_INJECTION_SUMMARY.pdf`

---

Hi Chris,

quick update — the thesis now rests on three pieces that build on each other. Short version below, details in the two attached PDFs.

*1. Experiment 1 (PDF 1)* — the 40-PR benchmark. Adding knowledge-graph context to the LLM reviewer significantly improves the dependency/impact criteria of the review rubric; RAG helps on breadth; the hybrid gets both. This is the result you already know, now written up cleanly.

*2. Experiment 2 (PDF 2)* — a controlled bug-injection study I ran as a causal follow-up to Experiment 1. I planted bugs whose consequences sit in a *different file* than the change, and checked which reviewer setup catches them. Without the KG the reviewer catches essentially none of them (0/28; RAG 1/28); with the KG it catches most (up to 26/28 in the best variant). On control bugs that are visible in the diff itself, the KG gives no advantage — so it's really the dependency knowledge doing the work. The design was pre-registered before I wrote any code.

*3. Human study — live:* https://abzokhattab.github.io/pr-review-study/
Both experiments are judged by LLMs, so the last step is showing that humans see the difference too. 6 easy-to-read Python PRs, two anonymous reviews each, ~20-30 min per rater; the power analysis says 15-20 raters. Feel free to click through it yourself.

In one line: Exp 1 shows the effect on real PRs, Exp 2 shows it's causal, the human study shows people actually notice it.

*Ask:* your OK to start recruiting the raters. Happy to walk through Experiment 2 in our next meeting.
