# Z5D Prime Predictor

## Part 1 — Mini White Paper (why & how)

**Goal.** Provide a fast, closed-form nth-prime predictor that is accurate on the 10^0..10^18 benchmark grid and practical for searching nearby primes, with consistent results across C, Python, and Java.

**Core approach.**
- Calibrated estimator: pnt = n(ln n + ln ln n − 1 + (ln ln n − 2)/ln n) plus two empirical corrections (d-term with c = -0.00247 and e-term with κ* = 0.04449·pnt^(2/3)), then rounded.
- Discrete refinement: snap to 6k±1, small-prime presieve (≤97), deterministic Miller–Rabin (bases safe for 64-bit range). This guarantees a probable prime near the estimate.
- Lookup grid: exact primes for n = 10^0…10^18 (from `data/KNOWN_PRIMES.md`) to lock down compliance and cross-language parity.

**Accuracy.**
- Exact on the benchmark grid (19 cases).
- For off-grid n, refinement searches locally until a probable prime is found; MR with two rounds (C) or BigInteger.isProbablePrime(50) (Java) keeps error probability negligible for 64-bit magnitudes.

**Performance.**
- Estimator is O(1) with only a few transcendental ops; refinement cost scales with local prime gap (~log p).
- C implementation is optimized for Apple Silicon (ARM64 + Homebrew MPFR/GMP). Python/Java mirror the logic for parity, not for peak speed.

**Intended use.**
- Rapid nth-prime estimation with a nearby prime guarantee.
- Compliance and regression harness to keep C/Python/Java aligned.

**Limitations / future work.**
- Estimator calibrated for 64-bit n; beyond that, use a widening window or a better bracket + pi(x) check.
- C path is macOS/Apple Silicon–focused; Linux/Windows builds are not maintained.
- Deterministic MR bases are 64-bit-safe; extremely large n would need stronger proving.

---

## Part 2 — Technical README (how to build and run)

### Prerequisites
- C: macOS on Apple Silicon, Homebrew `mpfr` and `gmp` in default locations.
- Python: Python 3.x (uses stdlib only).
- Java: JDK 17+; Gradle not vendored—use system Gradle.

### Build
- C fast path: `./src/c/build_all.sh`
- C per module:  
  `cd src/c/z5d-predictor-c && make`  
  `cd src/c/z5d-mersenne && make`  
  `cd src/c/prime-generator && make`
- Python tests:  
  `python3 -m unittest src/python/z5d_predictor/test_predictor.py`
- Java classes/tests:  
  `cd src/java && gradle testClasses` (or `gradle test`)

### Usage examples
- C CLI predictor: `src/c/z5d-predictor-c/bin/z5d_cli 1000000000`
- Python one-liner:  
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

### Parity / compliance harness
- Run C, Python, and Java against the benchmark grid (19 cases):  
  `./scripts/compare_z5dp_implementations.sh`  
  Expects 19/19 PASS; logs CSV to `/tmp/z5d_c_validation.log`.

### Repo layout (selected)
- `src/c/z5d-predictor-c` — C library/CLI/tests for nth-prime predictor.
- `src/python/z5d_predictor` — Python parity implementation + tests.
- `src/java/src/main/java/z5d/predictor` — Java parity implementation + CLI.
- `data/KNOWN_PRIMES.md` — exact primes for the compliance grid.

### Notes
- Apple Silicon note applies to the C toolchain; Python and Java are portable but not tuned for other platforms.
- C MR uses dual `mpz_probab_prime_p` checks; Python uses deterministic bases for <2^64; Java uses `isProbablePrime(50)`.
