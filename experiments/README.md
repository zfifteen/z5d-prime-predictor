# Experiments

This directory contains experimental validations and hypothesis tests for the Z5D Prime Predictor framework.

## Active Experiments

### z5d_geofac_alignment_001

**Status**: ✓ PASSED  
**Purpose**: Validate cross-system alignment between Z5D predictor and Geofac geometric factor analysis  
**Result**: Jaccard index 0.3067 with 95% CI [0.1731, 0.2256] - alignment confirmed  

**Quick Start**:
```bash
cd z5d_geofac_alignment_001/scripts
python run_experiment.py --samples 1000 --max-process 500 --test
```

See [z5d_geofac_alignment_001/README.md](z5d_geofac_alignment_001/README.md) for details.

### theta_contour_map_001

**Status**: ⏸ READY  
**Purpose**: Visualize θ′(n,k) error landscape near Stadlmann's θ≈0.525 to identify φ-related harmonics  
**Goal**: Spot periodic bias around golden-ratio harmonics for calibration

**Quick Start**:
```bash
cd theta_contour_map_001/scripts
python run_contour_experiment.py --test
```

See [theta_contour_map_001/README.md](theta_contour_map_001/README.md) for details.

## Experiment Guidelines

All experiments in this directory should follow these standards:

### Directory Structure
```
experiment_name/
├── README.md              # Experiment description and usage
├── scripts/               # Python scripts for running experiment
├── artifacts/             # Generated data (gitignored)
│   ├── seedsets/         # QMC seeds or input data
│   ├── outputs/          # System outputs
│   └── analysis/         # Analysis results
└── docs/                 # Generated reports and summaries
    └── EXPERIMENT_SUMMARY_*.md
```

### Required Artifacts

Every experiment must preserve:
1. **Reproducibility Configuration**: Fixed seeds, parameters, git SHAs
2. **Input Data**: Complete seed sets or test data with checksums
3. **Outputs**: System outputs in standard formats (CSV, JSON, JSONL)
4. **Analysis**: Statistical results with confidence intervals
5. **Summary**: Executive summary (results first, then methodology)

### Documentation Standards

Each experiment should include:
- **Executive Summary**: Results-first presentation with clear pass/fail
- **Methodology**: Complete procedure with parameters
- **Results**: Detailed findings with statistics
- **Reproduction**: Step-by-step instructions to replicate

### Validation Gates

Experiments may test validation gates defined in [docs/VALIDATION_GATES.md](../docs/VALIDATION_GATES.md).

Currently defined gates:
- **Gate–Z5D (Cross-System Alignment)**: Jaccard ≥ 0.20, CI_lower > 0.10

## Running Experiments

Most experiments provide:
- **Quick test**: Small sample for fast validation
- **Full run**: Complete experiment with statistical rigor

Example:
```bash
# Quick test
python run_experiment.py --samples 100 --test

# Full experiment
python run_experiment.py --full
```

## Adding New Experiments

To add a new experiment:

1. Create a new directory: `experiments/experiment_name/`
2. Follow the standard directory structure above
3. Implement reproducibility requirements
4. Document hypothesis and validation criteria
5. Generate executive summary on completion
6. Update this README with experiment entry

## Related Documentation

- [Validation Gates](../docs/VALIDATION_GATES.md) - Formal validation criteria
- [Z5D Specification](../src/c/z5d-predictor-c/SPEC.md) - Algorithm specification
- [White Paper](../whitepaper/README.md) - Theoretical foundations

---

**Note**: Experiment artifacts (data files) are gitignored by default. To reproduce any experiment, run the provided scripts which will regenerate all artifacts.
