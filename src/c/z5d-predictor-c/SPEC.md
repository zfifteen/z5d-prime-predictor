# Z5D nth-Prime Predictor - Technical Specification

**Platform scope:** macOS on Apple Silicon (M1 Max). This C implementation is intentionally Apple-only; portability to Linux/Windows or non-ARM64 CPUs is not a goal.

## Mathematical Foundation

### Riemann Prime-Counting Function

The Riemann prime-counting function R(x) approximates π(x) (the number of primes ≤ x):

```
R(x) = Σ(k=1 to ∞) μ(k)/k * li(x^(1/k))
```

Where:
- μ(k) is the Möbius function
- li(x) is the logarithmic integral

### Truncated Series

In practice, we truncate the series at K terms (typically K=5):

```
R(x) ≈ Σ(k=1 to K) μ(k)/k * li(x^(1/k))
```

This provides excellent accuracy with manageable computation.

### Möbius Function

```
μ(n) = {
    1   if n is a square-free positive integer with even number of prime factors
   -1   if n is a square-free positive integer with odd number of prime factors
    0   if n has a squared prime factor
}
```

### Logarithmic Integral

The logarithmic integral li(x) is computed using series expansion:

```
li(x) ≈ ln(ln(x)) + γ + Σ(k=1 to N) (ln x)^k / (k * k!)
```

Where γ ≈ 0.5772156649 is the Euler-Mascheroni constant.

### Derivative R'(x)

The derivative of R(x) is:

```
R'(x) = (1/ln x) * Σ(k=1 to K) μ(k)/k * x^(1/k - 1)
```

## Algorithm

### 1. Initialization

Use the 3-term Cipolla/Dusart initializer for x₀:

```
x₀ = n * (L + L₂ - 1 + (L₂ - 2)/L - (L₂² - 6L₂ + 11)/(2L²))
where L = ln n, L₂ = ln ln n
```

This 3-term version provides materially better accuracy at 10^9-10^12 scales compared to the 2-term version, with the additional O(L^-2) term reducing initialization error.

### 2. Newton Iteration

Solve f(x) = R(x) - n = 0 using Newton's method:

```
x_{i+1} = x_i - f(x_i)/f'(x_i)
        = x_i - (R(x_i) - n)/R'(x_i)
```

### 3. Convergence

Iterate until:

```
|x_{i+1} - x_i| < tolerance
```

Typically converges in 1-3 iterations.

## Implementation Details

### Precision

- **Default MPFR precision**: 320 bits (~96 decimal places)
- Comfortable headroom for 10^12+ scales
- Upgraded from 200 bits for better accuracy at large n

### Series Terms

- **Default K**: 10
- K=5: Fast, ~1-10 ppm accuracy at 10^9
- K=10: Better accuracy, 0.04-1.5 ppm at 10^9-10^12
- K=15: Maximum supported (precomputed Möbius table)

### Convergence Tolerance

- **Default**: 1e-50
- Ensures high-precision convergence
- Typically reached in 1-3 iterations

## Performance Characteristics

### Time Complexity

Per iteration:
- Möbius μ(k): O(K√k) ≈ O(K) for small K
- Series sum: O(K)
- li(x) computation: O(N) where N ≈ 100
- Overall: O(K * N) per iteration

### Space Complexity

- MPFR variables: O(precision)
- Overall: O(precision * variables) ≈ O(precision)

### Convergence Rate

Newton's method provides quadratic convergence:
- Error after i iterations: ε_i ≈ ε₀^(2^i)
- Typically 1-3 iterations for convergence

## Accuracy Analysis

### Small Scale (n ≤ 10^6)

- Absolute error: < 1
- Relative error: < 0.1 ppm
- Convergence: 1-2 iterations

### Medium Scale (10^7 ≤ n ≤ 10^9)

- Absolute error: < 10
- Relative error: < 1 ppm
- Convergence: 2-3 iterations

### Large Scale (10^10 ≤ n ≤ 10^12)

- Absolute error: < 100
- Relative error: < 10 ppm
- Convergence: 2-3 iterations
- May require higher precision (300+ bits)

## Error Sources

1. **Series Truncation**: Truncating R(x) at K terms
2. **li(x) Approximation**: Series expansion error
3. **Floating-Point Rounding**: MPFR precision limits
4. **Convergence Tolerance**: Early stopping criterion

## Optimization Strategies

### Implemented

1. **Static Möbius Computation**: μ(k) computed once per k
2. **Log Caching**: ln(x) computed once per iteration
3. **Power Caching**: Reuse x^(1/k) computations
4. **Inline Functions**: Small functions inlined

### Potential

1. **Pre-computed li(x)**: Table lookup for common values
2. **Parallel Series Sum**: OpenMP for K terms
3. **Adaptive K**: Choose K based on n
4. **Halley's Method**: Third-order convergence

## Comparison to Reference

### Python Reference (z5d_newton_r_predictor.py)

- Uses mpmath with dps=50
- Single Newton step
- K=5 by default

### C/MPFR Implementation

- Uses MPFR with 200-bit precision (≈50 dps)
- Multi-iteration Newton method
- K=5 by default
- ~100-1000x faster than Python

## Testing Strategy

### Unit Tests

- Möbius function correctness
- li(x) accuracy
- R(x) and R'(x) computation
- Dusart initializer

### Integration Tests

- Known prime values (10^1 to 10^9)
- Medium scale (10^10 to 10^12)
- Edge cases (n=1, very large n)

### Performance Tests

- Timing benchmarks
- Convergence analysis
- Precision vs speed tradeoff

## API Design

### Philosophy

- Simple C API
- RAII-style initialization/cleanup
- Configurable precision and parameters
- Clear error handling

### Thread Safety

- Library initialization not thread-safe
- Prediction function thread-safe if separate result structures used
- MPFR itself is thread-safe with proper precautions

## Future Enhancements

1. **Halley's Method**: Third-order convergence
2. **Corrector Term**: 1-D corrector for sub-ppm accuracy
3. **Parallel Computation**: OpenMP for series sums
4. **Adaptive Precision**: Automatically adjust based on n
5. **Batch Prediction**: Vectorized predictions
6. **GPU Acceleration**: CUDA for massive parallelism

## References

1. Dusart, P. (1999). "The kth prime is greater than k(ln k + ln ln k − 1)"
2. Riemann, B. (1859). "On the Number of Primes Less Than a Given Magnitude"
3. MPFR documentation: https://www.mpfr.org/
4. Python reference: z5d_newton_r_predictor.py
5. Repository: https://github.com/zfifteen/unified-framework
