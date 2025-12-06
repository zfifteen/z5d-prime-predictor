# Theta Contour Map Visualization Experiment

## Overview

This experiment provides a contour-map visualization kit for the θ′(n,k) error landscape near Stadlmann's θ≈0.525. The goal is to spot any periodic bias around golden-ratio (φ) harmonics and identify stable features that could inform calibration or bias correction.

## Hypothesis

When visualizing the θ′(n,k) error surface:
- If there's φ-locked bias, repeating bands or nodal lines should appear in (θ,k) space
- Stable features across scales (10^14 to 10^18) are candidates for calibration
- Drifting features hint at scale-coupled terms that can be modeled

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install numpy matplotlib

# Optional: scipy for additional analysis
pip install scipy
```

### Run Test Experiment (Fast)

```bash
cd scripts
python run_contour_experiment.py --test
```

This runs with:
- 50×50 grid resolution
- All validation gate scales (log₁₀n = 14-18)
- Generates data files and plots

### Run Full Experiment

```bash
cd scripts
python run_contour_experiment.py --full
```

This runs with:
- 100×100 grid resolution
- Complete statistical analysis
- High-quality plots

### Generate Data Only (No Plots)

```bash
cd scripts
python run_contour_experiment.py --data-only
```

Useful for environments without matplotlib display support.

## Experiment Structure

```
theta_contour_map_001/
├── scripts/                      # Python scripts
│   ├── generate_contour_map.py   # Core contour generation
│   └── run_contour_experiment.py # Orchestration script
├── artifacts/                    # Generated data (gitignored)
│   ├── contour_data/            # JSON surface data
│   │   ├── surface_log14.json
│   │   ├── surface_log15.json
│   │   ├── surface_log16.json
│   │   ├── surface_log17.json
│   │   ├── surface_log18.json
│   │   └── multi_scale_summary.json
│   └── plots/                   # PNG contour maps
│       ├── contour_log14.png
│       ├── contour_log15.png
│       ├── contour_log16.png
│       ├── contour_log17.png
│       └── contour_log18.png
├── docs/                        # Generated reports
│   └── EXPERIMENT_SUMMARY.md
└── README.md                    # This file
```

## Parameters

### Grid Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| θ center | 0.525 | Stadlmann's optimal θ value |
| θ delta | ±0.06 | Range around center |
| k min | 0.05 | Minimum geodesic exponent |
| k max | 1.0 | Maximum geodesic exponent |
| Resolution | 100 | Grid points per axis |

### Scale Range

- **Minimum**: log₁₀(n) = 14 (10^14)
- **Maximum**: log₁₀(n) = 18 (10^18)
- Matches Z5D validation gate constraints

### φ-Related Harmonics

Reference lines at φ-related offsets:
- 1/φ² ≈ 0.382
- 1/φ ≈ 0.618
- 1.0

## Individual Script Usage

### Generate Single Contour Map

```bash
python generate_contour_map.py \
  --log10n 16 \
  --output ../artifacts/plots/contour_log16.png

# With custom parameters
python generate_contour_map.py \
  --log10n 16 \
  --theta-center 0.525 \
  --theta-delta 0.08 \
  --k-min 0.1 \
  --k-max 0.8 \
  --resolution 150 \
  --output custom_contour.png
```

### Generate All Scales

```bash
# Generate all plots
python generate_contour_map.py --all-scales --output ../artifacts/plots/contour.png

# Generate all data files
python generate_contour_map.py --all-scales --save-data --output ../artifacts/contour_data/surface.json
```

### Disable φ Reference Lines

```bash
python generate_contour_map.py --log10n 16 --no-phi-lines --output clean_contour.png
```

## Hooking Your Real Error Function

The script uses a mock error model by default. To use your real θ′(n,k) benchmark:

### Step 1: Locate the Mock Function

In `generate_contour_map.py`, find:

```python
def theta_prime_error_mock(theta: np.ndarray, k: np.ndarray, log10n: float) -> np.ndarray:
    """Mock θ′(n,k) error model for visualization."""
    ...
```

### Step 2: Replace with Your Implementation

```python
def theta_prime_error_real(theta: np.ndarray, k: np.ndarray, log10n: float) -> np.ndarray:
    """
    Real θ′(n,k) error from Z5D benchmark.
    
    Args:
        theta: 2D array of θ values
        k: 2D array of k values  
        log10n: log₁₀(n) scale
    
    Returns:
        2D array of prediction errors
    """
    n = 10 ** log10n
    
    # Your vectorized Z5D prediction logic here
    # Example structure:
    predicted_primes = vectorized_z5d_predict(n, theta, k)
    actual_primes = get_actual_primes(n)
    
    # Compute relative error
    error = np.abs(predicted_primes - actual_primes) / actual_primes
    
    return error
```

### Step 3: Update the Error Function Call

In `compute_error_surface()`, change:

```python
if error_func is None:
    error_func = theta_prime_error_real  # Changed from theta_prime_error_mock
```

## Interpreting Results

### Contour Map Features

1. **Valleys (dark regions)**: Low error; optimal parameter combinations
2. **Ridges (light regions)**: High error; avoid these parameter regions
3. **Nodal lines**: Boundaries between high/low error; may indicate phase transitions

### φ-Harmonic Analysis

Look for:
- **Repeating bands** aligned with gold reference lines → φ-locked bias present
- **Stable features** across all scales → candidates for universal calibration
- **Drifting features** as scale increases → scale-coupled terms to model

### Scale Dependency

Compare contour maps across log₁₀(n) = 14 to 18:
- **Consistent optima**: θ≈0.525 is universally optimal
- **Shifting optima**: Need scale-dependent θ correction
- **Changing topology**: Error landscape fundamentally changes with scale

## Output Artifacts

### JSON Data Format

Each `surface_log{N}.json` contains:

```json
{
  "_metadata": {
    "log10n": 16,
    "theta_min": 0.465,
    "theta_max": 0.585,
    "k_min": 0.05,
    "k_max": 1.0,
    "stadlmann_theta": 0.525,
    "phi": 1.618...,
    "timestamp_utc": "..."
  },
  "theta": [[...]],
  "k": [[...]],
  "error": [[...]],
  "statistics": {
    "error_min": 0.00123,
    "error_max": 0.45678,
    "optimal_theta": 0.524,
    "optimal_k": 0.32
  }
}
```

### Multi-Scale Summary

`multi_scale_summary.json` contains:

```json
{
  "scales": [14, 15, 16, 17, 18],
  "optimal_theta_drift": [...],
  "optimal_k": [...],
  "min_error": [...],
  "phi_alignment_score": [...]
}
```

## Known Limitations

1. **Mock Error Model**: Default uses simulated error; replace with real benchmark
2. **Static Grid**: Fixed resolution; could be adaptive for efficiency
3. **Single θ Metric**: Only examines θ′ error; other metrics may be relevant
4. **Limited Harmonics**: Only tests first few φ powers; could extend

## Future Extensions

- [ ] Integrate with real Z5D predictor for true error maps
- [ ] Add interactive visualization (Plotly/Bokeh)
- [ ] Implement adaptive grid refinement near optima
- [ ] Add uncertainty quantification via bootstrap
- [ ] Cross-reference with z5d_geofac_alignment experiment
- [ ] Test additional harmonic bases (e, π, algebraic irrationals)

## References

- Stadlmann's θ: See `/whitepaper/` for theoretical foundation
- Golden Ratio: φ = (1 + √5) / 2 ≈ 1.618
- Z5D Framework: See `/src/c/includes/z_framework_params.h`
- Validation Gates: See `/docs/VALIDATION_GATES.md`

## Experiment Metadata

- **Created**: 2025-12-04
- **Author**: Automated experiment framework
- **Version**: 1.0
- **Status**: Ready for execution
- **Estimated Runtime**: 1 minute (test), 5 minutes (full)

---

For questions or issues, see the main repository README or open an issue on GitHub.
