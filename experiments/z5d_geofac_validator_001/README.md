# Z5D as Geofac Validator Experiment

## Overview

This experiment validates the hypothesis that **Z5D's factor-ranking can serve as an effective validator for Geofac's resonance scores**, providing orthogonal signals that reduce false positives without requiring classical factoring algorithms (Pollard rho, ECM, etc.).

## Hypothesis

When Z5D's geometric/closed-form ranking is applied to Geofac's top-K resonance candidates:

1. **Agreement**: Z5D consistently ranks true factors higher than false candidates
2. **Confidence**: Combined signals (resonance + Z5D rank) provide stronger validation
3. **Utility**: Creates fast, independent check for false positive reduction
4. **Calibration**: Produces actionable calibration curves and ROC/AUC metrics

## Key Innovation

- **Orthogonal Signals**: Geofac uses phase resonance; Z5D uses geometric/φ-harmonic ranking
- **Minimal Integration**: Thin adapter wraps Z5D without modifying core algorithms
- **Immediate Utility**: Generates calibration curves for production tuning
- **Research Compliant**: No classical factoring algorithms (maintains research constraints)

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install gmpy2 numpy scipy matplotlib

# Verify z_shared module works
cd tools
python z_shared.py
```

### Run Test Experiment (Fast)

```bash
cd tools
python run_experiment.py --test
```

This runs a quick validation with:
- 5 test semiprimes (10^14 to 10^18)
- 500 candidates per N
- Top-10 ranking comparison
- ~2-5 minutes runtime

### Run Full Experiment

```bash
cd tools
python run_experiment.py --full
```

This runs the complete experiment with:
- 20 test semiprimes
- 2,000 candidates per N
- Top-20 ranking comparison
- ~15-30 minutes runtime

### View Results

Results are written to:
- **FINDINGS.md**: `docs/FINDINGS.md` (executive summary)
- **Data**: `artifacts/outputs/` (CSV with standard schema)
- **Metrics**: `artifacts/outputs/*_metrics.json`
- **Calibration**: `artifacts/analysis/*_calibration.json` and `.png`
- **ROC**: `artifacts/analysis/*_roc.json` and `.png`

## Experiment Structure

```
z5d_geofac_validator_001/
├── tools/                      # Python modules
│   ├── z_shared.py            # Shared precision/seed/transform utilities
│   ├── z5d_adapter.py         # Z5D validator adapter
│   ├── geofac_scorer.py       # Geofac resonance scorer
│   ├── crosscheck.py          # Cross-validation script
│   ├── generate_calibration.py # Calibration curve generator
│   └── run_experiment.py      # Main orchestrator
├── artifacts/                  # Generated data (gitignored)
│   ├── outputs/               # Standard CSV/JSONL results
│   └── analysis/              # Calibration and ROC data
├── docs/                      # Documentation
│   └── FINDINGS.md            # Experimental findings report
└── README.md                  # This file
```

## Architecture

### 1. Shared Infrastructure (`z_shared.py`)

Single source of truth for:
- **Precision**: DPS_MIN, DPS_TARGET, DPS_MAX with magnitude-based auto-scaling
- **Seed Control**: Centralized SEED, RNG_KIND with reproducibility assertions
- **Transforms**: Shared φ/Z-transforms and Dirichlet phase helpers
- **I/O Schema**: Standard CSV/JSONL format with metadata

### 2. Geofac Scorer (`geofac_scorer.py`)

Generates and scores candidate factor pairs:
- **Generation**: φ-biased geometric sampling near √N
- **Scoring**: Dirichlet phase resonance + geometric balance + φ-harmonics
- **Output**: Ranked list of candidates with resonance scores

### 3. Z5D Adapter (`z5d_adapter.py`)

Validates candidates using Z5D ranking:
- **Interface**: `validate_candidates(N, pairs, seed, dps) -> List[ValidationResult]`
- **Scoring**: Geometric proximity + φ-harmonics + product error
- **Output**: Re-ranked list with Z5D scores and ranks

### 4. Cross-Validation (`crosscheck.py`)

Combines both systems:
- Runs Geofac to get top-K candidates
- Passes same candidates to Z5D validator
- Computes agreement metrics (Jaccard, Spearman, hit rates)
- Writes standard CSV with unified schema

### 5. Calibration Analysis (`generate_calibration.py`)

Produces calibration and ROC curves:
- **Calibration**: Binned resonance score vs. actual Z5D agreement rate
- **ROC**: Agreement rate vs. threshold (with AUC)
- **Output**: JSON data + PNG plots

## Standard I/O Schema

All outputs follow unified schema (version 1.0.0):

### CSV Columns

```
run_id, N, seed, dps, p, q,
resonance_rank, resonance_score,
z5d_rank, z5d_score,
error, is_factor, agree
```

### Metadata Header (CSV comments)

```
# run_id: <unique_identifier>
# N: <target_semiprime>
# seed: <random_seed>
# dps: <decimal_precision>
# timestamp: <ISO8601_UTC>
# schema_version: 1.0.0
```

### JSONL Format

First line: `{"_metadata": {...}}`  
Remaining lines: One record per line

## Validation Criteria

### Success Metrics

1. **Jaccard Index ≥ 0.20**: Overlap in top-K sets
2. **Agreement Rate ≥ 0.50**: Fraction of candidates both systems agree on
3. **Spearman Correlation > 0.3**: Rank correlation between systems
4. **AUC > 0.6**: Discriminative ability via ROC analysis

### Scale Requirements

- **Minimum**: 10^14 (smaller scales rejected)
- **Maximum**: 10^18 (current test range)
- **Precision**: Auto-scaled by magnitude (128-256 DPS)

## Reproducibility

### Determinism Guarantees

- **Fixed Seed**: All randomness controlled by single seed parameter
- **Precision Control**: Magnitude-based precision with runtime assertions
- **Standard Transforms**: Shared φ/Z/Dirichlet functions in z_shared
- **Schema Version**: All outputs tagged with schema version

### Artifacts

All artifacts include:
- Run ID
- Timestamp (UTC)
- Seed and RNG kind
- Precision (DPS)
- Git SHA (when available)
- Schema version

### Verification

Re-run with same seed and parameters should produce identical results:

```bash
python run_experiment.py --test --seed 42
# Compare checksums
sha256sum artifacts/outputs/*.csv
```

## Individual Tool Usage

### Z5D Adapter

```bash
# Validate specific candidates
python z5d_adapter.py 1000000000000000 \
  --pairs "999999000001,1000001;999999000011,999999000013" \
  --seed 42 --top-k 5 --verbose
```

### Geofac Scorer

```bash
# Generate and score candidates
python geofac_scorer.py 1000000000000000 \
  --candidates 1000 --window 0.1 \
  --seed 42 --top-k 10 --verbose
```

### Crosscheck

```bash
# Cross-validate on multiple semiprimes
python crosscheck.py 1000000000000000 10000000000000000 \
  --candidates 1000 --top-k 10 \
  --seed 42 --output-dir ../artifacts/outputs
```

### Calibration Generator

```bash
# Generate calibration curves from results
python generate_calibration.py ../artifacts/outputs/results.csv \
  --output-dir ../artifacts/analysis \
  --bins 10 --plot
```

## Known Limitations

1. **Test Semiprimes**: Uses generated semiprimes, not historical RSA challenges
2. **Scale Range**: Limited to 10^14-10^18 (smaller scales rejected per gates)
3. **Simplified Models**: Both Geofac and Z5D use research implementations
4. **No Classical Algorithms**: Intentionally excludes Pollard rho, ECM, etc.
5. **Single QMC Type**: Uses deterministic RNG, not QMC sequences

## Future Extensions

- [ ] Test on actual RSA challenge numbers
- [ ] Extend scale range (10^20+)
- [ ] Sensitivity analysis on top-K thresholds
- [ ] Multiple seed robustness tests
- [ ] Integration with full Z5D predictor C implementation
- [ ] Batch processing for large-scale validation
- [ ] Real-time validation API

## Cross-Repo Audit Implementation

This experiment implements cross-repo audit requirements:

### ✓ Precision Handling
- Single source: `z_shared.DPS_MIN/TARGET/MAX`
- Runtime assertions: `assert_dps(N)`
- No silent downcasts: All operations use gmpy2 mpfr
- Logged precision: Headers in all outputs

### ✓ Seed & RNG Control
- Centralized: `z_shared.set_seed(seed, rng_kind)`
- Emitted: seed/rng_kind in every artifact
- Reproducible: `assert_seed()` guards all RNG ops

### ✓ Shared Constants & Transforms
- Module: `z_shared.py` with φ, Z-transform, Dirichlet helpers
- Canonical: Single version with tests
- No duplicates: Both systems import from z_shared

### ✓ I/O Schema
- Standard columns: run_id, N, seed, dps, k, ranks, scores, agree, ts
- Unified format: CSV with metadata comments, JSONL with _metadata
- Agreement flag: `agree` column for quick confusion matrix

## Unified Benchmarking

### Dataset Gates ✓
- **Scale**: 10^14 to 10^18 enforced
- **Source**: RSA-style semiprimes (generated for testing)
- **Validation**: Magnitude checks in all entry points

### Metrics ✓
- **Top-K hit rate**: k=1, 5, 10, 20 supported
- **Median rank**: Computed for true factors
- **AUC**: Trapezoid integration over ROC curve
- **Calibration**: Reliability curve (binned score vs. success rate)

### Strata ✓
- **By digits**: 14-18 digit semiprimes
- **By DPS**: Auto-scaled precision (128-256)
- **By seed**: Single seed per run (multi-seed in future)

### Failure Knowledge ✓
- **Auto-dump**: Worst misses logged in metrics
- **Full header**: All runs include complete metadata
- **Rank gaps**: Computed and reported

## References

- **Z5D Specification**: `/src/python/z5d_predictor/predictor.py`
- **Validation Gates**: `/docs/VALIDATION_GATES.md`
- **Geofac Alignment**: `/experiments/z5d_geofac_alignment_001/`
- **White Paper**: `/whitepaper/`

## Experiment Metadata

- **Created**: 2025-12-14
- **Author**: Automated experiment framework
- **Version**: 1.0.0
- **Status**: Ready for execution

---

For questions or issues, see the main repository README or create an issue on GitHub.
