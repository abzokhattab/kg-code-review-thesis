# §13 sign-off record — 2026-07-13

User instruction (2026-07-13): "yes lets go ... make sure its idempotent
and parallel", following the assistant's summary of the pre-registered
recommendations. Decisions below follow
`docs/DESIGN_AND_PREREGISTRATION.md` §13 recommendations; deviations are
flagged and justified.

1. **N and split:** 48 total = 36 structural (S1–S5) + 12 local control
   (L1–L2), 16 per repo (12 structural + 4 control). Per-band quotas per
   repo: S1×3 S2×3 S3×2 S4×2 S5×2, L1×2 L2×2. Shortfalls (insufficient
   AST-discovered supply for a band) are **reported, not back-filled**
   (pre-reg §5).
2. **Repos:** scikit-learn (Python), apache/kafka (Java,
   `streams/` scope), grafana (**TypeScript** `packages/grafana-data`
   scope). *Deviation note:* grafana participates via its TS code, not
   Go — the Joern Go frontend gap is the same one that forced n=35 in
   era 3; the TS frontend was verified working on 2026-07-13. This keeps
   the 3-language guard (Python/Java/TS) without a known-broken frontend.
3. **Oracle scope:** static-structural ground truth for all injections
   (independently resolved import/extends/call dependents). Behavioural
   test-run oracle **omitted** (recommended fallback in §13.3: repos are
   too large for reliable suite runs); every manifest entry records
   `oracle: "static-structural"` and this is reported honestly.
4. **Ablation arms:** both `kg-idealised` and `kg-joern+inherit`
   included, per §7. Six arms total: baseline, kg (Joern deployed), rag,
   hybrid, kg-idealised, kg-joern+inherit.
5. **Human study (RQ3):** downgrade confirmed (2026-07-05 decision
   stands; re-affirmed implicitly 2026-07-13). No further rater-UX work
   until draft + Experiment 2 are done.

## Execution decisions (engineering, not scientific)

- **Idempotency:** every paid unit (review generation, judge verdict)
  writes to its own file under `out/`; stages skip existing non-empty
  outputs, so any stage can be killed and re-run. `--force` regenerates.
- **Parallelism:** generation and judging run in a bounded thread pool
  (default 8 workers) with exponential backoff on 429/rate errors.
- **Control-band judging:** the pre-registered detection criterion
  ("names ≥1 true dependent breakage", §6) applies to structural bands.
  For L1–L2 (no dependents by construction) detection = the review
  identifies the specific injected local defect (wrong
  comparison/inverted null check at the edit site). Both templates are
  fixed here, before any data is generated.
- **Contexts are built from the clean scope** (CPG + RAG index on
  un-mutated code), matching the prototype and the deployed pipeline;
  the mutation exists only in the diff the reviewer sees.
- **Generator:** gpt-4o, **T=0.3** via `prnote.note.generate_review_direct`
  (production prompts). The temperature is hardcoded in that function and
  takes no override; the "T=0.4" recorded here before 2026-08-12 was wrong
  (`paper/2026-08-12/INTEGRITY_AUDIT.md` §I1). The same function truncates
  the diff at 12 000 characters, which is not binding here because an
  injected defect diff is a few lines. **Judges:** gpt-4o-mini, gpt-4o,
  gemini-2.5-flash, majority of 3, ties→0 (identical to Experiment 1).
- Nothing outside `experiments/2026-07-05_injection_exp2/out/` is
  written. Experiment 1 data is never touched.
