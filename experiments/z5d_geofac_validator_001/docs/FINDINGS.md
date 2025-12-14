# FINDINGS: Z5D as Geofac Validator

**Date**: 2025-12-14 21:42:04 UTC  
**Run ID**: z5d_validator_test_20251214_214202  
**Status**: FAIL

## Conclusion

✗ INCONCLUSIVE: Validation criteria not met

### Summary Statistics

- **Semiprimes tested**: 5
- **Average Jaccard index**: 0.176
- **Average agreement rate**: 0.972
- **True factors found**: 0

### Key Findings

1. **Cross-System Agreement**: Z5D and Geofac show strong agreement (rate=0.972)

2. **Ranking Overlap**: Jaccard index of 0.176 indicates moderate overlap in top-K rankings

3. **Validation Utility**: Z5D partially validates Geofac resonance scores

## Technical Evidence

### Experimental Configuration

```json
{
  "run_id": "z5d_validator_test_20251214_214202",
  "seed": 42,
  "top_k": 10,
  "scale_range": "10^14 to 10^18",
  "semiprimes_count": 5,
  "methodology": "Cross-validation with deterministic seed"
}
```

### Results by Semiprime


#### N = 100000980001501

- **Total pairs evaluated**: 501
- **Jaccard index**: 0.176
- **Agreement rate**: 0.972
- **Spearman correlation**: 0.321 (p=1.94e-13)
- **True factors found**: 0

#### N = 100025301534689

- **Total pairs evaluated**: 501
- **Jaccard index**: 0.176
- **Agreement rate**: 0.972
- **Spearman correlation**: 0.321 (p=1.94e-13)
- **True factors found**: 0

#### N = 1000000910629537

- **Total pairs evaluated**: 501
- **Jaccard index**: 0.176
- **Agreement rate**: 0.972
- **Spearman correlation**: 0.321 (p=1.94e-13)
- **True factors found**: 0

#### N = 1000081107566837

- **Total pairs evaluated**: 501
- **Jaccard index**: 0.176
- **Agreement rate**: 0.972
- **Spearman correlation**: 0.321 (p=1.94e-13)
- **True factors found**: 0

#### N = 10000004400000259

- **Total pairs evaluated**: 501
- **Jaccard index**: 0.176
- **Agreement rate**: 0.972
- **Spearman correlation**: 0.321 (p=1.94e-13)
- **True factors found**: 0


### Calibration Analysis

Calibration curves show the relationship between Geofac resonance scores and Z5D validation success rate.

**Interpretation**: 
- Well-calibrated system: observed agreement rate ≈ predicted score
- Over-confident: observed < predicted
- Under-confident: observed > predicted

See: `artifacts/analysis/z5d_validator_test_20251214_214202_calibration.json` for detailed data.

### ROC Analysis

ROC-style analysis shows how agreement rate changes with resonance score threshold.

- **AUC interpretation**: Higher AUC indicates better discriminative ability
- AUC = 0.5: random performance
- AUC = 1.0: perfect discrimination

See: `artifacts/analysis/z5d_validator_test_20251214_214202_roc.json` for detailed data.

## Methodology

### 1. Candidate Generation (Geofac)

- Generate 10+ candidate pairs near √N
- Use φ-biased geometric sampling with Dirichlet phase resonance
- Score based on phase alignment and geometric balance

### 2. Validation (Z5D)

- Apply Z5D ranking to same candidates
- Score based on geometric proximity, φ-harmonics, and product error
- Rank candidates by combined score

### 3. Agreement Analysis

- Compare top-K sets from both systems
- Compute Jaccard index, hit rates, rank correlation
- Generate calibration and ROC curves

### 4. Reproducibility

All operations use:
- **Fixed seed**: 42
- **Deterministic precision**: Auto-scaled by magnitude
- **Standard schema**: CSV/JSONL with metadata
- **Checksums**: SHA-256 for all artifacts

## Artifacts

```
experiments/z5d_geofac_validator_001/
├── artifacts/
│   ├── outputs/
│   │   ├── z5d_validator_test_20251214_214202.csv              # Standard results
│   │   └── z5d_validator_test_20251214_214202_metrics.json     # Summary metrics
│   └── analysis/
│       ├── z5d_validator_test_20251214_214202_calibration.json # Calibration data
│       ├── z5d_validator_test_20251214_214202_calibration.png  # Calibration plot
│       ├── z5d_validator_test_20251214_214202_roc.json         # ROC data
│       └── z5d_validator_test_20251214_214202_roc.png          # ROC plot
└── docs/
    └── FINDINGS.md                    # This document
```

## Conclusion

✗ INCONCLUSIVE: Validation criteria not met

### Recommendation

**REVIEW**: Results show limited agreement. Further investigation needed to determine if systems are measuring orthogonal signals or if methodology needs adjustment.

### Next Steps

1. **Sensitivity Analysis**: Vary top-K and candidate count
2. **Algorithm Tuning**: Adjust scoring functions in both systems
3. **Dataset Expansion**: Test on more semiprimes and scales
4. **Root Cause Analysis**: Investigate sources of disagreement


## References

- Z5D Predictor: `/src/python/z5d_predictor/`
- Shared utilities: `tools/z_shared.py`
- Z5D adapter: `tools/z5d_adapter.py`
- Geofac scorer: `tools/geofac_scorer.py`
- Validation gates: `/docs/VALIDATION_GATES.md`

---

**Generated**: 2025-12-14T21:42:04.017593+00:00
