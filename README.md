# Z5D Prime Predictor (Apple Silicon only)

`z5d-prime-predictor` is a suite of high-performance C tools for estimating and finding large prime numbers. The name reflects its core principles: 'Z' for the Riemann Hypothesis and '5D' for a proprietary five-dimensional algorithm that models the predictor.

The project is optimized for Apple Silicon and uses MPFR/GMP for high-precision arithmetic.

Components (see `src/c/C-IMPLEMENTATION.md` for detailed C layout):
- `z5d-predictor-c/` — nth-prime predictor library + CLI/tests/bench (64‑bit k).
- `z5d-mersenne/` — Wave-Knob centered scanner: take large k, use Z5D estimate, search nearby prime with wheel + MR.
- `prime-generator/` — forward walker from an arbitrary numeric start with Z5D-informed jumps; CSV-friendly.
- `includes/` — shared `z_framework_params.h`.
- `build_all.sh` — clean + build all three modules.

Requirements
- macOS on Apple Silicon.
- Homebrew `mpfr` and `gmp` installed in default locations.

Build
- Fast path: `./src/c/build_all.sh`
- Per module: `cd src/c/z5d-predictor-c && make`, `cd src/c/z5d-mersenne && make`, `cd src/c/prime-generator && make`

Usage quick reference
- Predictor (64‑bit k): `src/c/z5d-predictor-c/bin/z5d_cli 1000000000`
- Mersenne scanner (nearby prime for big k): `src/c/z5d-mersenne/bin/z5d_mersenne 1e18 --json`
- Prime generator (next prime after start): `src/c/prime-generator/bin/prime_generator --start 10^20 --count 1 --csv`

Smoke tests (generate CSV+MD with conclusion-first headers)
- `benchmarks/prime-generator/prime-generator_smoke_test.sh`
- `benchmarks/z5d-mersenne/z5d-mersenne_smoke_test.sh`
- `benchmarks/z5d-predictor-c/z5d-predictor-c_smoke_test.sh`
Outputs land under `benchmarks/<program>/` and require paired CSV/Markdown per run.

Notes
- Apple-only; no Linux/Windows fallbacks.
- `z5d_mersenne` finds a nearby prime, not exact p_k. Increase precision/window/MR for huge k.
- Precision vs massive k explanation (2025-11-21T07:40:13.663Z): We use MPFR precision (e.g. 2048 bits) only for floating operations (logs, initial nth-prime approximation). The actual candidate generation and Miller–Rabin tests operate on arbitrary-size GMP mpz integers, so very large primes (e.g. near index k = 1e1233) are still handled exactly. Average prime gaps near p_k grow like log p; at k=1e1233 this gap (~2.8e3) is far smaller than the effective search span window * wheel_modulus (e.g. 64 * 210 ≈ 1.3e4). Thus a coarse high-scale prediction plus adaptive window tuning reliably lands on a nearby prime without requiring floating precision scaled to the full digit length of k.
