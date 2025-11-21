- re-implement the core C99 z5d predictor algorithm from the unified framework repo
- new C99 project should created under 'src/c'

* **0. Repo skeleton**

    * Init git in `z5d-prime-predictor` (if not already).
    * Create `src/`, `include/`, `tests/`, `benchmarks/`, `docs/`.

* **1. Locate the C99 reference in unified-framework**

    * Identify current C99 Z5D files (core predictor, helpers, headers, Makefile bits).
    * List exact entrypoints (e.g. `z5d_predict_prime(n)`, config structs, constants).

* **2. Define minimal public API**

    * Choose clean C99 API in `include/z5d.h` (e.g. `uint64_t z5d_prime_index(uint64_t n);`, plus 128-bit/BigInt path).
    * Decide config struct for precision / scale gates (10^14–10^18 only).

* **3. Extract core math without baggage**

    * Copy/port only math required for:

        * Riemann-R seed estimate.
        * Single-step Newton refinement.
        * 5D geodesic correction term(s).
        * Stadlmann θ=0.525 density adjustment and constants.
    * Remove any framework-generic abstractions, logging, agent hooks.

* **4. Precision / numeric types**

    * Decide numeric backend: `long double` + explicit comments on valid range, or small custom high-precision layer.
    * Port any tuning constants (k*, curvature params, θ, etc.) as `static const` with doc strings.

* **5. Implement core predictor**

    * Implement pure C99 `z5d_predict_prime_index(n)` using the extracted math.
    * Add fast path for in-range n (10^14–10^18); guard or assert on out-of-range.
    * Ensure no dynamic allocation in the hot path.

* **6. CLI wrapper**

    * Add `src/main.c` that:

        * Parses `n` from argv.
        * Calls predictor.
        * Prints result and basic timing.

* **7. Build system**

    * Add simple `Makefile`:

        * Targets: `libz5d.a`, `z5d-cli`, `test`, `bench`.
        * Flags: C99, `-O3`, `-Wall -Wextra`, optional `-march=native`.

* **8. Test harness**

    * Add `tests/test_z5d.c`:

        * Hard-code a small set of large-n indices (10^14–10^18) and reference primes from unified-framework logs.
        * Check relative error thresholds (ppm gates).
    * Add small-n sanity checks (no claims, just “doesn’t explode”).

* **9. Cross-validation script (optional helper)**

    * In unified-framework, write tiny script to dump `(n, p_ref, p_z5d)` for chosen test points.
    * Import those fixtures into `tests/fixtures/` for the C project.

* **10. Benchmark harness**

    * Add `benchmarks/bench_z5d.c`:

        * Time predictor over a sweep of n values.
        * Emit CSV (n, predicted, elapsed_ns, rel_error) for quick plots.

* **11. Docs**

    * `README.md`: scope, API, build instructions, scale gates, error profile.
    * `docs/DESIGN.md`: short note on which parts of unified-framework this C99 port corresponds to.

* **12. Validation pass**

    * Run tests + benchmarks on your M1 Max.
    * Compare results vs unified-framework predictor; adjust constants/precision if needed.
    * Tag initial commit once accuracy + speed meet your gate criteria.

Additional components now present:
- `src/c/z5d-predictor-c/` (MPFR/GMP nth-prime library, CLI, tests, bench).
- `src/c/z5d-mersenne/` (Wave-Knob MPFR scanner for arbitrary-precision k; heuristic nearby-prime search).
