# Project Layout

Apple Silicon only; assumes Homebrew MPFR/GMP.

- `src/c/z5d-predictor-c/`: MPFR/GMP nth-prime library + CLI/tests/bench (64-bit n input).
- `src/c/z5d-mersenne/`: Wave-Knob MPFR scanner; accepts arbitrary-precision k (e.g., 1e1233) and scans around a Z5D estimate with wheel + Miller–Rabin to find a nearby prime. Apple Silicon only. Build: `cd src/c/z5d-mersenne && make` (outputs `bin/z5d_mersenne` inside that folder).
- `src/c/bin/`: built binaries (e.g., `z5d_mersenne`).
