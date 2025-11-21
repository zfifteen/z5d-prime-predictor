# C Toolkit Overview (Apple Silicon only)

This folder holds three focused C programs that all depend on MPFR/GMP but serve different jobs. Build outputs stay inside each module’s `bin/` subdir.

- **z5d-predictor-c/** – The core nth‑prime predictor. CLI `z5d_cli` takes a 64‑bit index *k* and returns an estimate for *p_k*, plus tests/benchmarks. Use when you need the calibrated Z5D model itself (validation, profiling, library embedding).
- **z5d-mersenne/** – “Find a nearby prime” scanner for arbitrary‑precision *k* (e.g., 1e1233). It centers on the Z5D estimate and searches symmetrically with wheel + Miller–Rabin. Use for exploratory large‑k hunts where any close prime is acceptable; it does **not** certify the exact nth prime.
- **prime-generator/** – Forward prime walker from an explicit numeric start (e.g., 10^1234). Uses Z5D-informed jumps, wheel filters, and MR to locate the next prime(s), optionally logging CSV. Use to extend a frontier or resume from a checkpoint value rather than an index.
- **includes/** – Shared `z_framework_params.h` with the tunable constants each module includes via `-I../includes`.

Build notes (Apple M1/M2 with Homebrew `mpfr`/`gmp`):
- `cd z5d-predictor-c && make`
- `cd z5d-mersenne && make`
- `cd prime-generator && make`

Outputs:
- `z5d-predictor-c/bin/` → `z5d_cli`, tests, bench tools
- `z5d-mersenne/bin/` → `z5d_mersenne`
- `prime-generator/bin/` → `prime_generator`

Choose the module based on your question:
- Know the index *k*, want the Z5D estimate itself → z5d-predictor-c.
- Have a huge *k*, just need a nearby prime quickly → z5d-mersenne.
- Have a large numeric start value, want the next prime past it → prime-generator.
