#!/usr/bin/env bash
# Smoke test plan for z5d-mersenne (nearby-prime scanner) on Apple Silicon
#
# Goal:
# - Prove the centered search runs and finds a nearby prime quickly for a large k.
#
# Scenario:
# - Choose k around 1e18 (within comfortable MPFR range). Example: k = 1_000_000_000_000_000_007.
# - Precision: default MPFR (e.g., 256 bits) unless overridden; record actual.
# - Search window: leave defaults; this is a quick path-to-first-prime check.
#
# Command (fill in when running):
# - From src/c/z5d-mersenne: ./bin/z5d_mersenne <k> --auto-tune (or default options)
#
# Checks:
# - Exit code == 0.
# - Prime found is > 2, within the search window (verify monotone distance if reported).
# - Wall time target: < ~500 ms for a single find at this k on M1 Max.
#
# Artifacts (to write when executed):
# - benchmarks/z5d-mersenne/smoke-1e18.csv with columns:
#     k, prime_found, distance_from_center, candidates_tested, mr_rounds, elapsed_ms, prec_bits
# - benchmarks/z5d-mersenne/smoke-1e18.md:
#     Headline = conclusion (e.g., “Found prime +19 from center in 240 ms”),
#     followed by method, command, params, and observations.
#
# Notes:
# - This is a health check; no exhaustive scan. Keep default filters (wheel/MR) on.
# - Apple Silicon only; assumes Homebrew MPFR/GMP.
