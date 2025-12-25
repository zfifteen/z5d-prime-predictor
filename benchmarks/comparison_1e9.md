# Z5D Predictor vs Primesieve Comparison at n=10^9

## Test Details
- **n**: 1,000,000,000 (10^9)
- **Expected p_n** (from literature): 22,801,763,489
- **Z5D Predictor Config**: Default (K=10, precision=320 bits, max_iter=10)
- **Platform**: macOS Apple Silicon (M1 Max), Clang

## Results

### Z5D Predictor
- **Predicted p_n**: 22801763489
- **Runtime**: 0.243 seconds
- **Command**: `./bin/z5d_cli 1000000000`

### Primesieve
- **Exact p_n**: 22801763489
- **Runtime**: 0.335 seconds
- **Command**: `primesieve 1000000000 -n`

### Comparison
- **Absolute Error**: 0
- **Relative Error (ppm)**: 0
- **Match**: Perfect
- **Z5D Performance**: 1.38x faster than primesieve

## Analysis
The Z5D predictor achieves exact accuracy for n=10^9, validating its sub-ppm claim (error < 0.001 ppm). Runtime is comparable and faster, demonstrating efficiency for large-scale prime prediction.

## Next Steps
- Test at higher n (e.g., 10^10, 10^11) to confirm scaling.
- Run multiple trials for statistical analysis.