# Z5D d/e-Term Calibration Run (2025-12-14)

Reproducible record of the calibration run performed with the new tooling.

## Command
```bash
python3 scripts/calibrate_de_terms.py --refine --compare --filter-below-min
```

## Dataset
- `data/KNOWN_PRIMES.md`
- Rows with `n < 10_000` automatically dropped (`--filter-below-min`, default `--min-n 10000`).

## Settings
- c bounds: [-0.01, 0.01], steps: 25  
- kappa_star bounds: [0.0, 0.2], steps: 25  
- Refinement: enabled (default span factor 0.2, 15×15 grid)  
- Comparison: enabled (baseline constants and ±δ perturbations)
- Loss: maximum relative error (ppm) over remaining rows; RMS ppm reported as diagnostic.

## Results (best by max-relative-error)
- `c = -0.00016667`
- `kappa_star = 0.06500000`
- `max_rel_ppm = 417.785827`
- `rms_ppm = 194.647729`

## Outputs
- Per‑n errors: `scripts/output/calibration_errors.csv`  
- Comparison table: `scripts/output/calibration_comparison.csv`

## Baseline vs best (from comparison CSV)
- Baseline (c=-0.00247, κ*=0.04449): max_rel_ppm ≈ 1678.54, rms_ppm ≈ 903.90  
- Best (above): max_rel_ppm ≈ 417.79, rms_ppm ≈ 194.65

## Notes
- Objective is sensitive to very small n; those rows were excluded via the min-n filter to focus on “meaningfully large” indices.
- The script evaluates the closed-form estimate only (no refinement to the next prime). If you want to target end-to-end predictor outputs, add refinement to the loss in a future run.
- Deprecation warning from gmpy2 `local_context` is benign for this run.

## Re-run checklist
1) Ensure `PYTHONPATH=src/python` or run from repo root.  
2) Optional: adjust min-n or loss bounds, e.g. `--min-n 1e5` or change grid density.  
3) Inspect `scripts/output/*.csv` after the run for per-n and comparison details.  
