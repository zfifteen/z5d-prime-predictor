# Benchmark Plan (Apple Silicon only)

Purpose: measure speed, accuracy, and search efficiency of the three C tools on a fixed Apple Silicon machine to catch regressions and guide tuning.

## Tools & objectives
- **z5d-predictor-c** (nth-prime predictor): quantify prediction accuracy vs ground truth (where known) and per-call latency across precisions.
- **z5d-mersenne** (centered nearby-prime search): measure how quickly it finds a prime near huge k and how wide the search window must grow.
- **prime-generator** (forward walker): measure time/candidates to reach the next prime from large numeric starts; gauge benefit of Z5D jump hints.

## Scenarios (scale bands)
- Sanity: k ≈ 1e6; start ≈ 1e12
- Mid: k ≈ 1e9; start ≈ 1e30
- Large: k ≈ 1e1233 (or start ≈ 10^1234); high-precision paths

## Metrics to record
- z5d-predictor-c: |p̂−p|, relative error, wall‑time/call, precision used.
- z5d-mersenne: candidates tried, MR rounds, max window reached, wall‑time to first prime, success rate.
- prime-generator: candidates tried, MR rounds, wall‑time to first prime, primes/sec once running; compare “with jump” vs “no jump”.

## Consistency rules
- Hardware: Apple M1/M2; pin `OMP_NUM_THREADS`; leave turbo/default but note it.
- Precision: fix MPFR/GMP precision per run and log it.
- MR rounds: keep constant within a compare; vary only in dedicated sweeps.
- Single source of params: `src/c/includes/z_framework_params.h`.

## Outputs
- CSV/TSV rows with: tool, scenario, precision, params, candidates, MR rounds, window, wall_ms, primes_found, error metrics (for predictor).
- Store reports under `benchmarks/<program>/` (`z5d-predictor-c/`, `z5d-mersenne/`, `prime-generator/`) to keep runs separated per tool, not at the top level.
- Every CSV/TSV must have a same-basename Markdown explainer in the same folder (e.g., `run1.csv` + `run1.md`). The Markdown must start with the conclusion as the headline, followed by a detailed natural-language walkthrough of methods, params, and key numbers so a reader can understand the results without opening the raw table.

## Regression targets (initial)
- Predictor: < X ms per call for k=1e9 @ 256-bit; stable error envelope.
- Mersenne: >99% finds within window W for target k band; wall‑time threshold T.
- Prime-generator: ≥ Y candidates/sec at start=1e30; wall‑time to first prime under T.

Tune X, Y, W, T after the first measurement pass and lock them into this file.
