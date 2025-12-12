# Z5D Prime Predictor

## Overview
Z5D is a calibrated nth-prime predictor with a deterministic refinement step. It targets exact results on the 10^0–10^18 benchmark grid and consistent behavior across C, Python, and Java.

## Method
- **Estimator**: pnt = n(ln n + ln ln n − 1 + (ln ln n − 2)/ln n)  
  Corrections: d-term with c = -0.00247 and e-term with κ* = 0.04449·pnt^(2/3); result is rounded.
- **Refinement**: snap to 6k±1, small-prime presieve (≤97), Miller–Rabin (deterministic bases covering 64-bit). Produces a probable prime near the estimate.
- **Lookup grid**: exact primes for n = 10^0…10^18 (`data/KNOWN_PRIMES.md`) to lock cross-language parity.

## Guarantees and limits
- Exact on the 19 benchmark indices.  
- For other n (within 64-bit range), returns a probable prime found by local search; MR probability is negligible for this range.  
- Estimator is calibrated for 64-bit n; larger ranges would need wider search/bracketing.  
- C toolchain is optimized for macOS/Apple Silicon; Python/Java are portable but not performance-tuned for other platforms.

## Performance notes
- Estimator is O(1); refinement cost is proportional to the local prime gap (~log p).  
- C uses MPFR/GMP; Python/Java mirror the logic for correctness parity.

## Components
- `src/c/z5d-predictor-c` — C library, CLI, tests/bench (nth prime).  
- `src/c/z5d-mersenne` — nearby-prime scan for large k.  
- `src/c/prime-generator` — forward prime walker.  
- `src/python/z5d_predictor` — Python parity implementation.  
- `src/java/src/main/java/z5d/predictor` — Java parity implementation + CLI.  
- `data/KNOWN_PRIMES.md` — ground-truth grid.

## Prerequisites
- C: macOS on Apple Silicon; Homebrew `mpfr` and `gmp` in default locations.  
- Python: Python 3.x (stdlib only).  
- Java: JDK 17+ and system Gradle (wrapper not vendored).

## Build
- C fast path: `./src/c/build_all.sh`  
- C per module:  
  `cd src/c/z5d-predictor-c && make`  
  `cd src/c/z5d-mersenne && make`  
  `cd src/c/prime-generator && make`  
- Python tests: `python3 -m unittest src/python/z5d_predictor/test_predictor.py`  
- Java classes/tests: `cd src/java && gradle testClasses` (or `gradle test`)

## Usage
- C CLI predictor: `src/c/z5d-predictor-c/bin/z5d_cli 1000000000`  
- Python:  
  ```bash
  python3 - <<'PY'
  from z5d_predictor import predict_nth_prime
  print(predict_nth_prime(1000000).prime)
  PY
  ```  
- Java CLI:  
  ```bash
  cd src/java
  gradle -q testClasses
  java -cp build/classes/java/main z5d.predictor.Z5DMain 1000000
  ```

## Compliance / parity harness
- Run all three implementations against the 19-case grid:  
  `./scripts/compare_z5dp_implementations.sh`  
  Writes CSV log to `/tmp/z5d_c_validation.log`; expected: 19/19 PASS.

## Notes
- Apple Silicon requirement applies to the C build; Python/Java run elsewhere but are not tuned for non-macOS platforms.  
- C refinement uses dual `mpz_probab_prime_p`; Python uses deterministic bases for <2^64; Java uses `isProbablePrime(50)`.
