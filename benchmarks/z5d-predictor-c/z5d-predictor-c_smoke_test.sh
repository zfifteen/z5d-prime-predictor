#!/usr/bin/env bash
# Smoke test plan for z5d-predictor-c (nth-prime predictor) on Apple Silicon
#
# Goal:
# - Verify predictor binary runs at high magnitude and produces reasonable estimates quickly.
# - Check accuracy at a known k where ground truth is available.
#
# Scenario:
# - Choose k in the mid/large band but still in 64-bit range, e.g., k = 1_000_000_000 (1e9).
# - Ground truth prime p_k is known from published tables; use that value when writing the report.
# - Precision: default MPFR (e.g., 256 bits) unless a flag overrides; record what was used.
#
# Command (fill in when running):
# - From src/c/z5d-predictor-c: ./bin/z5d_cli <k>
#
# Checks:
# - Exit code == 0.
# - Output returns a predicted prime estimate.
# - Compute |p̂ − p| and relative error against known p_k (use a helper if available).
# - Wall time target: < ~50 ms for the single prediction at k=1e9 on M1 Max.
#
# Artifacts (to write when executed):
# - benchmarks/z5d-predictor-c/smoke-1e9.csv with columns:
#     k, p_true, p_hat, abs_error, rel_error, elapsed_ms, prec_bits
# - benchmarks/z5d-predictor-c/smoke-1e9.md:
#     Headline = conclusion (e.g., “Predictor hits 0.3 ppm error at k=1e9 in 12 ms”),
#     followed by method, command, params, and observations.
#
# Notes:
# - Keep this as a fast health check, not a full accuracy sweep.
# - Run on Apple Silicon with Homebrew GMP/MPFR; no cross-platform paths.
