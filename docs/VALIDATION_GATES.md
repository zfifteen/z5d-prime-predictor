# Validation Gates

This document defines the validation gates that must be passed for various aspects of the Z5D Prime Predictor framework.

## Overview

Validation gates are formal criteria that experimental results must satisfy before findings can be considered validated. Each gate specifies:
- Measurable criteria
- Required evidence/artifacts
- Reproducibility requirements
- Failure conditions

## Gate–Z5D (Cross-System Alignment)

### Purpose
Validate that z5d-predictor and geofac (geometric factor search) detect the same structural features in prime distribution when operating on identical quasi-Monte Carlo (QMC) seed sets.

### Criteria

Using a fixed QMC seed set and shared binning near √N, the z5d-predictor top-K peaks and geofac top-K peaks must show:

1. **Jaccard Overlap ≥ 0.20**
   - Measure: |A ∩ B| / |A ∪ B| where A = z5d bins, B = geofac bins
   - Threshold: J ≥ 0.20
   
2. **95% Confidence Interval Lower Bound > 0.10**
   - Bootstrap resampling (minimum 1000 samples)
   - CI_lower > 0.10
   - Guards against spurious correlations

**Both criteria must be satisfied.**

### Scale Constraints
- Minimum scale: 10^14
- Maximum scale: 10^18
- Reject smaller scales (insufficient statistical power)

### Dataset Requirements
- Named RSA challenge semiprimes (e.g., RSA-100, RSA-110)
- OR synthetic semiprimes with documented generation method
- Dataset must be specified in validation report

### Reproducibility Requirements

#### Required Artifacts
All experiments must preserve:

1. **Seed Set**: `artifacts/seedsets/{seed_set_id}.csv`
   - QMC type (Sobol/Halton)
   - Random seed value
   - Number of samples
   - Dimensions
   - Complete sample sequence with row indices

2. **Z5D Peaks**: `artifacts/z5d/peaks_{seed_set_id}.jsonl`
   - Row ID mapping to seed set
   - k indices
   - Predicted primes
   - Scores
   - Bin assignments
   - Top-K selection (K documented)

3. **Geofac Peaks**: `artifacts/geofac/peaks_{seed_set_id}.jsonl`
   - Row ID mapping (same as Z5D)
   - Semiprime candidates (N)
   - Phase parameters
   - Amplitudes
   - Window sizes
   - Bin assignments
   - Top-K selection (same K as Z5D)

4. **Alignment Report**: `artifacts/alignment/{seed_set_id}/overlap_report.json`
   - Jaccard index
   - Bootstrap CI (method and sample count)
   - Top-K hit rate
   - Spearman correlation
   - Gate decision
   - All metadata

5. **Configuration**
   - Precision: scale (bits) and rounding mode
   - Binning: method, number of bins, range
   - Git SHA of both systems
   - Timestamp (UTC)

#### Seed Integrity
- QMC seeds must be checksummed (SHA-256)
- Any modification invalidates reproducibility
- Seed drift detection: all operations must log row_id

#### Precision Requirements
- BigDecimal scale: minimum 256 bits for Z5D
- Rounding mode: HALF_EVEN (or documented alternative)
- Geofac: exact integer arithmetic (GMP) for factors
- No mixed-precision artifacts (document any conversions)

### Binning Specification

Bins must be:
1. **Defined once**: Single binning specification used by both systems
2. **Committed**: Bin edges or generation method in version control
3. **Documented**: Min/max values, number of bins, spacing (linear/log)
4. **Shared coordinate**: Near √N or another justified coordinate

Example specification:
```json
{
  "binning": {
    "method": "equal_width_log",
    "num_bins": 1000,
    "coordinate": "log10(value)",
    "range": [14, 18]
  }
}
```

### K-Value Requirements
- Use identical K for both systems
- Document K in all artifacts
- Sensitivity analysis recommended: test K/2 and 2K
- Report if results are sensitive to K choice

### Failure Modes

The gate **FAILS** if any of the following occur:

1. **Insufficient Overlap**
   - Jaccard < 0.20
   
2. **Wide Confidence Interval**
   - CI_lower ≤ 0.10 (even if point estimate > 0.20)
   
3. **Reproducibility Failure**
   - Missing artifacts
   - Seed mismatch
   - Configuration drift
   - Bin specification mismatch
   
4. **Scale Violation**
   - Any test outside [10^14, 10^18]
   
5. **Precision Inconsistency**
   - Undocumented precision
   - Mixed scales affecting results
   - Near-tie reshuffling

### Mitigation Strategies

To avoid common failures:

1. **Seed Drift**: Always log row_id in all transformations
2. **Bin Mismatch**: Generate bins once, reuse in both tools
3. **Precision Bias**: Pin scale and rounding mode at start
4. **K-Mismatch**: Verify K in both output files before alignment
5. **Statistical Noise**: Use sufficient bootstrap samples (≥ 1000)

### Validation Status

This gate can be in one of three states:

- **PASS ✓**: All criteria met, artifacts preserved, reproducible
- **FAIL ✗**: One or more criteria not met
- **PENDING ⏸**: Experiment in progress or awaiting review

Current experiments:
- `z5d_geofac_alignment_001`: See `experiments/z5d_geofac_alignment_001/`

### Documentation Requirements

Each experiment passing or failing this gate must include:

1. **Executive Summary**
   - Results-first presentation
   - Clear pass/fail declaration
   - Key metrics in table format
   - Interpretation of findings

2. **Methodology Section**
   - Complete procedure
   - All parameters and configurations
   - Reproducibility instructions
   - Validation of requirements

3. **Results Section**
   - Binning statistics
   - Overlap measurements
   - Correlation analysis
   - Bootstrap diagnostics

4. **Artifacts Section**
   - File manifest
   - Checksums
   - Git SHAs
   - Access instructions

### Citation

When referencing this gate in papers or documentation:

```
Z5D Validation Gate (Cross-System Alignment): Jaccard overlap ≥ 0.20 
(95% CI > 0.10) between z5d-predictor and geofac top-K peaks on 
identical QMC seed sets at scales 10^14–10^18 on RSA semiprimes.
Required artifacts: seeds, peaks, alignment report, configurations.
```

### Updates and Versioning

- **Version**: 1.0
- **Created**: 2025-11-23
- **Last Updated**: 2025-11-23
- **Status**: Active

Changes to this gate require:
1. Version increment
2. Changelog entry
3. Re-validation of affected experiments
4. Notification to stakeholders

### Related Documents

- Experiment: `experiments/z5d_geofac_alignment_001/README.md`
- Z5D Specification: `src/c/z5d-predictor-c/SPEC.md`
- Verification: `src/c/z5d-predictor-c/VERIFICATION.md`
- White Paper: `whitepaper/README.md`

---

**Note**: This is the first validation gate for the Z5D framework. Additional gates for other validation dimensions (accuracy, performance, convergence) may be added in future versions.
