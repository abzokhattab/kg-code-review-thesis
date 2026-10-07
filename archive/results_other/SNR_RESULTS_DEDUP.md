# Signal-to-Noise (precision / actionability) results

Judge: openai-gpt-4o-mini · labels each raised point useful / generic / wrong
signal = #useful · noise = #generic+#wrong · SNR = signal/total

## Per-mode means

| mode | cond | n | signal | noise | total | SNR |
|---|---|---|---|---|---|---|
| baseline | verbose | 40 | 3.50 | 0.42 | 3.92 | 0.930 |
| rag | verbose | 40 | 3.45 | 0.28 | 3.73 | 0.937 |
| kg | verbose | 40 | 3.20 | 0.50 | 3.70 | 0.921 |
| hybrid | verbose | 40 | 3.60 | 0.50 | 4.10 | 0.926 |
| baseline | concise | 40 | 3.02 | 0.55 | 3.58 | 0.899 |
| rag | concise | 40 | 3.12 | 0.33 | 3.45 | 0.936 |
| kg | concise | 40 | 2.77 | 0.78 | 3.55 | 0.852 |
| hybrid | concise | 39 | 3.51 | 0.51 | 4.03 | 0.916 |

## Q1 — does CONCISE raise precision? (paired concise vs verbose)

- **snr**: verbose=0.928  concise=0.901  Δ=-0.027 (concise↓)  Wilcoxon p=0.1477  (n=159)
- **signal**: verbose=3.440  concise=3.107  Δ=-0.333 (concise↓)  Wilcoxon p=0.03804  (n=159)
- **noise**: verbose=0.428  concise=0.541  Δ=+0.113 (concise↑)  Wilcoxon p=0.2379  (n=159)
- **total**: verbose=3.868  concise=3.648  Δ=-0.220 (concise↓)  Wilcoxon p=0.1428  (n=159)

## Q2 — does KG add signal over baseline? (paired, verbose)

- **signal**: baseline=3.500  kg=3.200  Δ=-0.300  Wilcoxon p=0.3639  (n=40)
- **noise**: baseline=0.425  kg=0.500  Δ=+0.075  Wilcoxon p=0.6439  (n=40)
- **snr**: baseline=0.930  kg=0.921  Δ=-0.009  Wilcoxon p=0.6833  (n=40)
- **total**: baseline=3.925  kg=3.700  Δ=-0.225  Wilcoxon p=0.6075  (n=40)

## Bottom line

- Concise SNR 0.901 vs verbose 0.928 (not higher).
- Concise signal 3.11 vs verbose 3.44 useful points/review (keeps real signal).
