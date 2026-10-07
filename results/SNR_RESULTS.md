# Signal-to-Noise (precision / actionability) results

Judge: openai-gpt-4o-mini · labels each raised point useful / generic / wrong
signal = #useful · noise = #generic+#wrong · SNR = signal/total

## Per-mode means

| mode | cond | n | signal | noise | total | SNR |
|---|---|---|---|---|---|---|
| baseline | verbose | 40 | 5.47 | 0.72 | 6.20 | 0.881 |
| rag | verbose | 40 | 5.62 | 0.88 | 6.50 | 0.877 |
| kg | verbose | 40 | 5.35 | 0.62 | 5.97 | 0.896 |
| hybrid | verbose | 40 | 5.53 | 0.90 | 6.42 | 0.877 |
| baseline | concise | 40 | 4.97 | 0.80 | 5.78 | 0.860 |
| rag | concise | 40 | 5.05 | 0.88 | 5.92 | 0.867 |
| kg | concise | 40 | 4.78 | 1.05 | 5.83 | 0.835 |
| hybrid | concise | 40 | 5.20 | 1.07 | 6.28 | 0.834 |

## Q1 — does CONCISE raise precision? (paired concise vs verbose)

- **snr**: verbose=0.883  concise=0.849  Δ=-0.034 (concise↓)  Wilcoxon p=0.07127  (n=160)
- **signal**: verbose=5.494  concise=5.000  Δ=-0.494 (concise↓)  Wilcoxon p=0.0002579  (n=160)
- **noise**: verbose=0.781  concise=0.950  Δ=+0.169 (concise↑)  Wilcoxon p=0.16  (n=160)
- **total**: verbose=6.275  concise=5.950  Δ=-0.325 (concise↓)  Wilcoxon p=0.01566  (n=160)

## Q2 — does KG add signal over baseline? (paired, verbose)

- **signal**: baseline=5.475  kg=5.350  Δ=-0.125  Wilcoxon p=0.7449  (n=40)
- **noise**: baseline=0.725  kg=0.625  Δ=-0.100  Wilcoxon p=0.6911  (n=40)
- **snr**: baseline=0.881  kg=0.896  Δ=+0.015  Wilcoxon p=0.9272  (n=40)
- **total**: baseline=6.200  kg=5.975  Δ=-0.225  Wilcoxon p=0.2205  (n=40)

## Bottom line

- Concise SNR 0.849 vs verbose 0.883 (not higher).
- Concise signal 5.00 vs verbose 5.49 useful points/review (keeps real signal).
