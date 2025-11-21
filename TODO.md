Current focus (Apple Silicon only)
================================

1) Benchmarks
- Set concrete thresholds (X/Y/W/T) in `benchmarks/BENCHMARKS.md` after first measurement pass.
- Add lightweight runners per module that dump CSV+Markdown into `benchmarks/<program>/` (basename-matched, conclusion-first narrative).
- Run sanity/mid/large scenarios and publish initial reports.

2) Tests / smoke runs
- Add quick smoke tests for each binary (small k/start) to guard regressions.
- Consider a small deterministic fixture set for `z5d-predictor-c` to track prediction error drift.

3) Docs
- Keep top-level README aligned with `src/c/C-IMPLEMENTATION.md` (single C overview lives there—avoid duplicates).
- For every new benchmark CSV/TSV, write the paired Markdown explainer (conclusion-first).

4) Housekeeping
- Decide whether to keep or drop stray artifacts like `prime_generator_output.txt`.
- Periodically prune per-module `bin/` and `build/` outputs before commits; keep builds warning-free.
