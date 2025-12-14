# References Artifact

**Date Created:** 2025-11-22  
**Section:** Title Page (Section 1 of White Paper)  
**Purpose:** Document all internal and external references for the white paper

---

## Internal Repository References

### Primary Documentation Files

1. **README.md**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/README.md`
   - Content: Project overview, components description, build instructions, usage examples
   - Key Information: Apple Silicon focus, MPFR/GMP dependencies, module descriptions

2. **TODO.md**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/TODO.md`
   - Content: Current development priorities, benchmark tasks, documentation requirements
   - Key Information: Focus on benchmarks, tests, and documentation alignment

3. **C-IMPLEMENTATION.md**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/src/c/C-IMPLEMENTATION.md`
   - Content: Detailed C toolkit overview, module descriptions, build notes
   - Key Information: Three C modules (z5d-predictor-c, z5d-mersenne, prime-generator), shared includes

4. **SPEC.md** (z5d-predictor-c)
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/src/c/z5d-predictor-c/SPEC.md`
   - Content: Technical specification for nth-prime predictor
   - Key Information: Mathematical foundation, Riemann R-function, algorithm details, performance characteristics

5. **VERIFICATION.md** (z5d-predictor-c)
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/src/c/z5d-predictor-c/VERIFICATION.md`
   - Content: Validation and testing information
   - Key Information: Test coverage, accuracy analysis

6. **FORENSIC_ANALYSIS.md**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/analysis/FORENSIC_ANALYSIS.md`
   - Content: Comprehensive project analysis, algorithm details, validation methods
   - Key Information: Z5D algorithm description, geodesic mapping (kappa_geo=0.3), error rates, validation methods

7. **z_framework_params.h**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/src/c/includes/z_framework_params.h`
   - Content: Standardized C header for framework parameters
   - Key Information: Mathematical constants, precision settings, calibration parameters

### Benchmark Documentation

8. **BENCHMARKS.md**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/benchmarks/BENCHMARKS.md`
   - Content: Benchmark framework and methodology
   - Key Information: Performance measurement standards

9. **z5d-predictor-c Smoke Test Results**
   - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/benchmarks/z5d-predictor-c/z5d-predictor-c_smoke-1e9.md`
   - Content: Smoke test results for predictor at k=10^9
   - Key Information: Actual performance data, error rates

10. **z5d-mersenne Smoke Test Results**
    - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/benchmarks/z5d-mersenne/z5d-mersenne_smoke-1e18.md`
    - Content: Smoke test results for Mersenne scanner
    - Key Information: Large-scale performance data

11. **prime-generator Smoke Test Results**
    - Location: `/home/runner/work/z5d-prime-predictor/z5d-prime-predictor/benchmarks/prime-generator/prime-generator_smoke-1e18.md`
    - Content: Smoke test results for prime generator
    - Key Information: Forward walking performance data

---

## External References (To Be Cited in Final Paper)

### Foundational Mathematical Works

1. **Riemann, Bernhard (1859)**
   - Title: "Ueber die Anzahl der Primzahlen unter einer gegebenen Grösse" (On the Number of Primes Less Than a Given Magnitude)
   - Relevance: Foundation of Riemann R-function used in Z5D predictor
   - Note: Original work on prime counting function

2. **Prime Number Theorem (PNT)**
   - Historical: Independently proven by Hadamard and de la Vallée Poussin (1896)
   - Relevance: Base approximation n*ln(n) + n*ln(ln(n)) - n for prime distribution
   - Note: Foundational for all prime prediction methods

3. **Cipolla Approximation**
   - Reference: Cipolla's work on prime number bounds
   - Relevance: Used in initialization step of predictor
   - Note: Provides better initial estimates than basic PNT

4. **Dusart, Pierre (1999)**
   - Title: "The kth prime is greater than k(ln k + ln ln k − 1)"
   - Relevance: Bounds used in predictor algorithm
   - Note: Improved bounds for large primes

### Recent Mathematical Research

5. **Stadlmann (2023)**
   - Title: Bounds on prime gaps in arithmetic progressions
   - Relevance: θ ≈ 0.525 parameter for distribution improvements
   - Key Contribution: 1-2% density enhancement from θ adjustments
   - Note: Recent work influencing Z5D calibration

### Computational Libraries

6. **MPFR Library**
   - Website: https://www.mpfr.org/
   - Documentation: https://www.mpfr.org/mpfr-current/mpfr.html
   - Relevance: High-precision floating-point arithmetic (50 decimal places)
   - Version: Latest stable version for Apple Silicon
   - License: GNU LGPL

7. **GMP (GNU Multiple Precision Arithmetic Library)**
   - Website: https://gmplib.org/
   - Documentation: https://gmplib.org/manual/
   - Relevance: Arbitrary-precision integer arithmetic, Miller-Rabin primality testing
   - Version: Latest stable version for Apple Silicon
   - License: GNU LGPL or GPL

### Related Geometric Number Theory

8. **Conical Flow Models**
   - Relevance: 15-20% density enhancement from geodesic transformations
   - Note: Physical analogy used in Z5D framework
   - Application: Geometric interpretation of prime distribution

9. **Golden Ratio (φ) in Number Theory**
   - Value: φ = 1.61803398874989...
   - Relevance: Used in geometric resolution θ'(n,k) = φ * ((n mod φ) / φ)^k
   - Historical: Classical constant with applications in discrete mathematics

### Software Development Tools

10. **Apple Silicon Documentation**
    - Platform: macOS on M1/M2/M-series processors
    - Relevance: Platform-specific optimizations
    - Compiler: Clang/LLVM for ARM64 architecture

11. **Homebrew Package Manager**
    - Website: https://brew.sh/
    - Relevance: Distribution method for MPFR/GMP on macOS
    - Package Installation: `brew install mpfr gmp`

---

## Project-Specific References

### GitHub Repository

1. **Main Repository**
   - URL: https://github.com/zfifteen/z5d-prime-predictor
   - Branch: main (and development branches)
   - License: See repository LICENSE file
   - Issues: https://github.com/zfifteen/z5d-prime-predictor/issues

2. **Related Gists** (if applicable)
   - EXPLAIN.txt: Detailed explanations of Z5D concepts
   - HIGH_SCALE_Z5D_VALIDATION.md: Ultra-large scale validation notes
   - Note: Check repository for linked gists in documentation

### Module-Specific Documentation

3. **z5d-predictor-c Module**
   - Binary: `bin/z5d_cli`
   - Purpose: Core nth-prime predictor (64-bit k)
   - Tests: Smoke tests, unit tests
   - Benchmarks: Performance measurements at various scales

4. **z5d-mersenne Module**
   - Binary: `bin/z5d_mersenne`
   - Purpose: Wave-Knob centered scanner for nearby primes
   - Use Case: Large k exploratory hunts (e.g., k=10^1233)

5. **prime-generator Module**
   - Binary: `bin/prime_generator`
   - Purpose: Forward walker from explicit numeric start
   - Use Case: Extending frontiers from checkpoint values

---

## Mathematical Concepts to Reference

### Core Z5D Framework Concepts

1. **Universal Invariant**
   - Formula: Z = A(B/c)
   - Purpose: Normalizing discrete systems
   - Context: Lorentz-inspired invariant for prime framework

2. **Discrete Curvature**
   - Formula: κ(n) = d(n) * ln(n+1) / e²
   - Purpose: Signaling prime locations
   - Context: Frame-normalized consistency

3. **Geometric Resolution**
   - Formula: θ'(n,k) = φ * ((n mod φ) / φ)^k
   - Purpose: Adaptive refinements
   - Context: Geodesic-based adjustments

4. **5D Geodesic Model**
   - Concept: Mapping primes as resonances on curved paths
   - Implementation: Wave-knob scanners for targeted searches
   - Enhancement: 15-20% density boost over PNT alone

### Calibration Parameters

5. **Key Constants from z_framework_params.h**
   - KAPPA_GEO_DEFAULT: 0.3 (geodesic exponent)
   - KAPPA_STAR_DEFAULT: 0.06500 (Z5D calibration factor, large-n calibration 2025-12-14)
   - Z5D_C_CALIBRATED: -0.00016667 (large-n calibration 2025-12-14)
   - E_SQUARED: 7.38905609893065
   - GOLDEN_PHI: 1.61803398874989

---

## Performance Metrics References

### Benchmark Results to Include

1. **Sub-microsecond Predictions**
   - Scale: k = 10^9
   - Time: < 1 microsecond
   - Platform: Apple Silicon (M1 Max)

2. **Error Rates**
   - Mean: 278 ppm for k = 10^6 to 10^8
   - Best: 12 ppm at peaks
   - Overall: Under 200 ppm for large n

3. **Speedup Comparisons**
   - vs. Naive Methods: 93-100x faster
   - vs. Sieving: Significantly faster for ultra-large scales
   - Platform Advantage: Apple Silicon optimizations

4. **High-Scale Performance**
   - k = 10^473: 79 milliseconds
   - k = 10^1233: Cryptographic scale simulations
   - Bit Ranges: 1661-4096 bits validated

---

## Bootstrap Validation References

### Statistical Methods

1. **Bootstrap Resampling**
   - Default: 1000 resamples
   - Confidence Interval: 95% (α = 0.05)
   - Purpose: Validate parameter optimality

2. **SHA Matching Validation**
   - Score Threshold: 0.85
   - Pearson Correlation: > 0.93 for zeta-SHA consistency
   - Pass Rate: 80% minimum

3. **Confidence Intervals**
   - Geodesic Enhancement: CI [14.6%, 15.4%] at higher N
   - Statistical Rigor: Bootstrap-validated parameters
   - Sample Requirements: Minimum 10 samples for reliable analysis

---

## Future Reference Sections to Develop

### For Section 4 (Background and Prior Art)
- Detailed Riemann R-function derivation sources
- Complete Stadlmann 2023 citation
- Historical PNT development timeline
- Geometric number theory survey papers

### For Section 5 (Z5D Methodology)
- Original Z5D framework papers (if published)
- Geodesic mapping mathematical foundations
- Physical analogy justifications

### For Section 7 (Empirical Results)
- Full benchmark CSV data files
- Smoke test complete outputs
- Performance comparison methodologies

### For Section 10 (References)
- 10-15 formal citations in academic format
- DOI links where available
- ArXiv references for preprints
- Software version numbers and dates

---

## Notes on Reference Quality

1. **Primary Sources**: Prefer original papers (Riemann, Stadlmann)
2. **Software Documentation**: Link to specific versions used
3. **Repository Commits**: Reference specific git hashes for code examples
4. **Benchmark Data**: Include timestamps and exact test conditions
5. **Platform Details**: Specify exact hardware (M1 Max, M2, etc.)

---

## Cross-Reference Strategy

When writing subsequent sections, ensure:
- All mathematical formulas reference their origin (SPEC.md, params.h)
- All performance claims cite specific benchmark files
- All code examples link to actual repository files
- All external papers include full bibliographic information
- All software versions are explicitly stated

---

_This artifact provides a comprehensive reference guide for all citations, links, and sources to be used throughout the white paper. It should be updated as new references are identified during the writing of subsequent sections._
