#!/usr/bin/env bash
# Smoke test plan for prime_generator at ~1e18 scale (Apple Silicon)
#
# Goal:
# - Prove end-to-end path works at high magnitude with realistic defaults.
# - Quick, single-prime run; no long scans.
#
# Scenario:
# - Start value: choose a composite around 1e18 (e.g., 1000000000000000000).
# - Expected next prime in that neighborhood: 1000000000000000003 (for 1e18).
# - Precision: leave default MPFR (~256 bits) unless a flag sets it; note what was used.
# - MR rounds: use program defaults (don’t lower at this scale).
#
# Command (to be filled when running):
# - From src/c/prime-generator: ./bin/prime_generator <start> --max=1
#   (If no --max flag exists, rely on first-hit exit.)
#
# Checks:
# - Exit code == 0.
# - Output prime > start; ideally equals known next prime (e.g., 1e18+3).
# - Wall time target: < ~250 ms on M1 Max for a single find at this scale.
#
# Artifacts (to write when executed):
# - benchmarks/prime-generator/smoke-1e18.csv with columns:
#     start, prime_found, elapsed_ms, prec_bits, mr_rounds
# - benchmarks/prime-generator/smoke-1e18.md:
#     Headline = conclusion (e.g., “Found 1e18+3 prime in 180 ms”),
#     followed by method, command, params, and observations.
#
# Notes:
# - Keep this smoke run minimal; it’s a health check, not a sweep.
# - Run on Apple Silicon with Homebrew GMP/MPFR; no Linux/Windows paths needed.
