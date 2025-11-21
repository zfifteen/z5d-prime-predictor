Current focus (Apple Silicon only)
================================

1) Benchmarks
- Define concrete thresholds (X/Y/W/T) in `benchmarks/BENCHMARKS.md` after first measurement pass.
- Add lightweight runners per module that dump CSV+Markdown into `benchmarks/<program>/` (matching basename, conclusion-first).
- Run sanity/mid/large scenarios and populate initial reports.

2) Warnings/cleanliness
- Resolve current compiler warnings in `z5d-predictor-c`, `z5d-mersenne`, and `prime-generator` (unused vars, sign compare).
- Ensure all Makefiles stay Apple-only and include the shared header path.

3) Tests / smoke runs
- Add quick smoke tests for each binary (small k/start) to guard regressions.
- Consider a small deterministic fixture set for `z5d-predictor-c` to track prediction error drift.

4) Docs
- Keep `src/c/README.md` and top-level README in sync when adding features or changing build/layout.
- For every new benchmark CSV/TSV, write the paired Markdown explainer (conclusion-first).

5) Housekeeping
- Decide whether to keep or drop stray artifacts like `prime_generator_output.txt`.
- Periodically prune per-module `bin/` and `build/` outputs before commits.
