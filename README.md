# Z5D Prime Predictor

Cross-language nth‑prime predictor (C / Python / Java) with calibrated closed‑form estimate + deterministic refinement. Exact on the 10^0…10^18 grid and validated for very large n (up to 10^1233) via MPFR/GMP (C), gmpy2 (Python), and BigInteger (Java).

## How it works
- **Estimator** (Z5D closed form):  
  pnt = n(ln n + ln ln n − 1 + (ln ln n − 2)/ln n)  
  d-term with c = −0.00016667; e-term with κ* = 0.065·pnt^(2/3); rounded to nearest int.
- **Refinement**: forward prime search (`next_prime`/`nextProbablePrime`) after snapping to a suitable starting point. Ensures a probable prime near the estimate.
- **Ground truth grid**: exact primes for n = 10^0…10^18 in `data/KNOWN_PRIMES.md` to lock parity across languages.

## Scope and guarantees
- Exact on the 19 benchmark indices.  
+- Big‑n path supports n up to 10^1233 (tested); precision scales with bit length + slack.  
- Outputs are probable primes (GMP/Java: strong probable prime; Python: gmpy2 probable prime).

## Layout
- `src/c/z5d-predictor-c` — MPFR/GMP core, CLI, tests/bench.  
- `src/python/z5d_predictor` — gmpy2 implementation for parity.  
- `src/java/src/main/java/z5d/predictor` — BigInteger implementation + CLI.  
- `scripts/` — compliance harness, calibration, and big‑n benchmarks; outputs land in `scripts/output/`.  
- `data/KNOWN_PRIMES.md` — ground-truth grid for parity tests.

## Prerequisites
- **C**: macOS Apple Silicon; Homebrew `mpfr` and `gmp` on PATH.  
- **Python**: Python 3.10+ with `gmpy2` installed (`python3 -m pip install gmpy2`).  
- **Java**: JDK 17+ and Gradle available on PATH.  

## Build
- C all: `./src/c/build_all.sh`  
- C predictor only: `cd src/c/z5d-predictor-c && make`  
- Python tests: `python3 -m unittest src/python/z5d_predictor/test_predictor.py`  
- Java classes/tests: `cd src/java && gradle testClasses` (or `gradle test`)

## Run the predictors
- **C CLI (auto precision)**  
  `src/c/z5d-predictor-c/bin/z5d_cli 1000000000`  
  (use `-p <bits>` to override precision)
- **Python**  
  ```bash
  PYTHONPATH=src/python python3 - <<'PY'
  from z5d_predictor import predict_nth_prime
  print(predict_nth_prime(10**20).prime)
  PY
  ```
- **Java CLI**  
  ```bash
  cd src/java
  gradle -q testClasses
  java -cp build/classes/java/main z5d.predictor.Z5DMain 1000000
  ```

## Compliance / parity harness
Run all three implementations against the 19-case grid:  
`./scripts/compare_z5dp_implementations.sh`  
Expected: 19/19 PASS (C/Python/Java). Log written to `/tmp/z5d_c_validation.log`.

## Big‑n benchmarking (10^20 … 10^1233)
- C:      `./scripts/benchmark_big_n.sh`  → `scripts/output/z5d_big_n_timings.csv`
- Python: `./scripts/benchmark_big_n_python.sh` → `scripts/output/z5d_big_n_timings_python.csv`
- Java:   `./scripts/benchmark_big_n_java.sh`   → `scripts/output/z5d_big_n_timings_java.csv`
Each script prints a hardware header, performs a warm-up sweep, then logs the measured sweep.

## Calibration (d/e-term coefficients)
Calibrate the closed-form coefficients `c` and `kappa_star` against the ground-truth grid (enforces minimum n, default 10,000):
```bash
./scripts/calibrate_de_terms.py --c-bounds -0.01 0.01 --k-bounds 0 0.2 --c-steps 25 --k-steps 25 --refine --compare --filter-below-min
```
Outputs:
- Per‑n errors → `scripts/output/calibration_errors.csv`
- Comparison table (when `--compare`) → `scripts/output/calibration_comparison.csv`

## Notes
- Apple Silicon requirement is for the C build; Python/Java are portable but not tuned for non‑macOS targets.  
- C precision auto-raises to (bitlen(n)+2048); Python uses gmpy2 mpfr with similar slack; Java uses scaled MathContext + `nextProbablePrime`.  
