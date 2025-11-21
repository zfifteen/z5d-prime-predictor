# Z5D Prime Predictor (Apple Silicon, C/MPFR)

Apple‑only port of the Z5D nth‑prime tools.

`src/c/` layout:
- `z5d-predictor-c/` — MPFR/GMP nth-prime library, CLI, tests, bench (64-bit n input).
- `z5d-mersenne/` — Wave-Knob MPFR scanner that accepts arbitrary-precision k (e.g., 1e1233) and searches near a Z5D estimate with wheel + Miller–Rabin; heuristic “find a prime near k” tool.
- `prime-generator/` — GMP/MPFR prime scanner that steps forward from an arbitrary start (e.g., 10^1234), with Z5D-informed jumps and optional CSV output.

Build (Apple Silicon, requires Homebrew mpfr/gmp):
- Predictor CLI/tests: `cd src/c/z5d-predictor-c && make`
- Wave-Knob scanner: `cd src/c/z5d-mersenne && make`

Usage examples:
- Predictor CLI (64-bit n): `src/c/z5d-predictor-c/bin/z5d_cli 1000000`
- Wave-Knob scanner (arbitrary k): `src/c/z5d-mersenne/bin/z5d_mersenne 1e6 --prec=2048 --auto-tune`

Notes:
- This repo targets macOS on Apple Silicon only; no Linux/Windows support.
- `z5d_mersenne` finds a nearby prime, not a certified p_k. Increase `--prec`, `--window`, `--mr-rounds` for huge k.
