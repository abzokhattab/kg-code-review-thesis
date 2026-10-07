# Judge validation vs deterministic mention-oracle (structural bands)

Oracle = review text literally names >= 1 true dependent file. The oracle is a conservative lexical check; disagreements are audit flags, not automatic judge errors (a judge may rightly reject a mention that names the file without identifying the breakage).

| Judge | Agreement | Detected-without-mention (FP-flag) | Mention-without-detected (FN-flag) |
|---|---:|---:|---:|
| openai:gpt-4o-mini | 121/168 (72%) | 0 | 47 |
| openai:gpt-4o | 135/168 (80%) | 0 | 33 |
| gemini:gemini-2.5-flash | 156/168 (93%) | 5 | 7 |

## FP flags (judge said detected; no dependent named)
- **gemini:gemini-2.5-flash**: kafka_S4_01/hybrid, kafka_S2_01/kg, kafka_S2_01/hybrid, kafka_S2_01/kg_joern_inherit, kafka_S1_02/hybrid
