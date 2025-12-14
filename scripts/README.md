Scripts (run from repo root)
============================

- `calibrate_de_terms.py` — grid-search calibration of d/e-term coefficients (`c`, `kappa_star`) using `data/KNOWN_PRIMES.md` (default). Enforces a minimum n (default 10,000); use `--filter-below-min` to drop smaller rows or lower `--min-n` if you intentionally want them. Writes per‑n errors to `scripts/output/calibration_errors.csv` and an optional comparison table to `scripts/output/calibration_comparison.csv`.
- `compare_z5dp_implementations.sh` — parity check across C / Python / Java on the benchmark grid.
- `benchmark_big_n.sh` — big‑n benchmark for C implementation (`scripts/output/z5d_big_n_timings.csv`).
- `benchmark_big_n_python.sh` — big‑n benchmark for Python (`scripts/output/z5d_big_n_timings_python.csv`).
- `benchmark_big_n_java.sh` — big‑n benchmark for Java (`scripts/output/z5d_big_n_timings_java.csv`).

All generated artifacts land in `scripts/output/`.
