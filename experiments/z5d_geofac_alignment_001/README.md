# Z5D-Geofac Alignment Validation Experiment

## Overview

This experiment validates the hypothesis that Z5D resonance peaks and Geofac geometric peaks align when using the same quasi-Monte Carlo (QMC) seed set. The goal is to determine if overlap exceeds 20% (Jaccard index ≥ 0.20 with 95% CI > 0.10), which would justify formalizing a "Z5D Gate" in validation documentation.

## Hypothesis

When Z5D Prime Predictor and Geofac (geometric factor search) are fed the same QMC seed set:
- Both systems should identify similar resonance/peak locations
- Overlap (measured by Jaccard index) should exceed 20%
- Correlation should be statistically significant (bootstrap CI > 0.10)

If validated, this demonstrates deterministic alignment between geometric and analytic approaches to prime analysis.

## Experiment Structure

```
z5d_geofac_alignment_001/
├── scripts/              # Python scripts for experiment pipeline
│   ├── generate_qmc_seeds.py      # Generate Sobol/Halton sequences
│   ├── run_z5d_peaks.py           # Extract Z5D predictor peaks
│   ├── run_geofac_peaks.py        # Extract Geofac resonance peaks
│   ├── compute_alignment.py       # Calculate overlap statistics
│   ├── generate_summary.py        # Create executive summary
│   └── run_experiment.py          # Master orchestration script
├── artifacts/            # All experimental data
│   ├── seedsets/        # QMC seed CSVs
│   ├── z5d/             # Z5D peak outputs (JSONL)
│   ├── geofac/          # Geofac peak outputs (JSONL)
│   └── alignment/       # Overlap reports (JSON)
└── docs/                # Generated documentation
    └── EXPERIMENT_SUMMARY_*.md
```

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install numpy scipy sympy

# Build z5d-predictor-c (if not already built)
cd ../../../src/c/z5d-predictor-c
make clean && make
cd -
```

### Run Test Experiment (Fast)

```bash
cd scripts
python run_experiment.py --samples 1000 --max-process 100 --test
```

This runs a quick validation with:
- 1,000 QMC samples
- Process first 100 for each system
- 100 bootstrap samples
- Generates all artifacts and summary

### Run Full Experiment

```bash
cd scripts
python run_experiment.py --full
```

This runs the complete experiment with:
- 200,000 QMC samples
- Full processing
- 1,000 bootstrap samples
- Complete statistical analysis

**Note**: Full experiment may take 30-60 minutes depending on hardware.

## Experimental Parameters

### Hard Constraints (Gates)

- **Scale Range**: 10^14 to 10^18 (reject smaller scales)
- **Dataset**: RSA challenge semiprimes (synthetic for testing)
- **Reproducibility**: Fixed seed=42, deterministic precision
- **Binning**: 1000 equal-width log-space bins
- **Top-K**: 2000 highest-amplitude peaks

### QMC Configuration

- **Type**: Sobol sequence (scrambled)
- **Dimensions**: 5 (matching Z5D framework)
- **Seed**: 42 (fixed for reproducibility)
- **Samples**: 200,000 (configurable)

### Validation Criteria

**Z5D Gate Passes If:**
- Jaccard index ≥ 0.20
- 95% CI lower bound > 0.10
- Both criteria must be satisfied

## Output Artifacts

### Seeds
`artifacts/seedsets/phi_qmc_001.csv`
- Row ID indexed QMC samples
- Metadata header with generation parameters
- 5 dimensions per row

### Z5D Peaks
`artifacts/z5d/peaks_phi_qmc_001.jsonl`
- One result per line (JSONL format)
- Fields: row_id, k, predicted_prime, score, bin_id
- Metadata in first line
- Top 2000 peaks by score

### Geofac Peaks
`artifacts/geofac/peaks_phi_qmc_001.jsonl`
- One result per line (JSONL format)
- Fields: row_id, N, k_or_phase, amplitude, p0_window, bin_id
- Metadata in first line
- Top 2000 peaks by amplitude

### Alignment Report
`artifacts/alignment/phi_qmc_001/overlap_report.json`
- Complete statistical analysis
- Jaccard index with bootstrap CI
- Top-K hit rate
- Spearman correlation
- Gate decision
- Full reproducibility metadata

### Executive Summary
`docs/EXPERIMENT_SUMMARY_phi_qmc_001.md`
- Results-first presentation
- Detailed methodology
- Statistical interpretation
- Reproduction instructions

## Individual Script Usage

### 1. Generate QMC Seeds

```bash
python generate_qmc_seeds.py \
  --type sobol \
  --samples 200000 \
  --dimensions 5 \
  --seed 42 \
  --output ../artifacts/seedsets/phi_qmc_001.csv \
  --set-id phi_qmc_001
```

### 2. Run Z5D Predictor

```bash
python run_z5d_peaks.py \
  --seeds ../artifacts/seedsets/phi_qmc_001.csv \
  --output ../artifacts/z5d/peaks_phi_qmc_001.jsonl \
  --scale-min 14 \
  --scale-max 18 \
  --top-k 2000
```

### 3. Run Geofac Analysis

```bash
python run_geofac_peaks.py \
  --seeds ../artifacts/seedsets/phi_qmc_001.csv \
  --output ../artifacts/geofac/peaks_phi_qmc_001.jsonl \
  --scale-min 14 \
  --scale-max 18 \
  --top-k 2000
```

### 4. Compute Alignment

```bash
python compute_alignment.py \
  --z5d ../artifacts/z5d/peaks_phi_qmc_001.jsonl \
  --geofac ../artifacts/geofac/peaks_phi_qmc_001.jsonl \
  --output ../artifacts/alignment/phi_qmc_001/overlap_report.json \
  --bootstrap-samples 1000
```

### 5. Generate Summary

```bash
python generate_summary.py \
  --report ../artifacts/alignment/phi_qmc_001/overlap_report.json \
  --output ../docs/EXPERIMENT_SUMMARY_phi_qmc_001.md
```

## Methodology

### Z5D Peak Extraction
- Uses existing z5d-predictor-c binary
- Maps QMC samples to k-indices logarithmically
- Extracts predicted primes for each k
- Scores using log₁₀(k)
- Bins predictions in log space
- Selects top-K by score

### Geofac Resonance Analysis
- Generates semiprime candidates from QMC
- Computes Dirichlet-style phase resonance near √N
- Uses golden ratio (φ) for geometric phase
- Includes e-based harmonic components
- Detects factor signals (high amplitude at actual factors)
- Bins resonances identically to Z5D
- Selects top-K by amplitude

### Overlap Measurement
- **Jaccard Index**: |A ∩ B| / |A ∪ B| on bin sets
- **Top-K Hit Rate**: |A ∩ B| / |A| (asymmetric)
- **Spearman Correlation**: Rank correlation on matching bins
- **Bootstrap CI**: 1000 resamples for confidence intervals

## Known Limitations

1. **Synthetic Semiprimes**: Uses generated semiprimes rather than historical RSA challenges
2. **Z5D Wrapper**: Calls z5d_cli as subprocess; could be optimized with library integration
3. **Geofac Implementation**: Simplified geometric model; full implementation would be more complex
4. **Scale Range**: Limited to 10^14-10^18; larger scales may behave differently
5. **Single QMC Type**: Only tests Sobol sequences; Halton sequences could give different results

## Future Extensions

- [ ] Test with actual RSA challenge numbers
- [ ] Vary QMC types (Halton, Latin Hypercube)
- [ ] Sensitivity analysis on K (500, 1000, 2000, 4000)
- [ ] Multiple seed values to test robustness
- [ ] Extended scale ranges (10^10-10^20)
- [ ] Direct factor detection validation
- [ ] Cross-validation with other prime analysis tools

## References

- Sobol Sequences: I.M. Sobol (1967), "Distribution of points in a cube"
- Bootstrap CI: B. Efron (1979), "Bootstrap methods"
- Jaccard Index: P. Jaccard (1901), "Étude comparative"
- Z5D Framework: See `/whitepaper/02-abstract/abstract.md`
- Geofac Concept: Geometric factor analysis via Dirichlet resonance

## Experiment Metadata

- **Created**: 2025-11-23
- **Author**: Automated experiment framework
- **Version**: 1.0
- **Status**: Ready for execution
- **Estimated Runtime**: 5 minutes (test), 30-60 minutes (full)

---

For questions or issues, see the main repository README or open an issue on GitHub.
