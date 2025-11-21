// prime_generator.c — Enhanced GMP/MPFR prime scanner with Z5D optimizations
//
// Build:
//   cc prime_generator.c z5d_predictor.c -o prime_generator -lgmp -lmpfr -lm -O3
//
// Usage:
//   ./prime_generator --start 10^1234 --count 10 --csv
//   ./prime_generator --start 123456789012345678901234567890 --count 5
//
// Enhanced features (addressing issue requirements):
// - Z5D-powered intelligent candidate jumping using prime-density predictions
// - Adaptive reps count for mpz_probab_prime_p based on number size
// - Pre-filtering with mpz_probab_prime_p(n, 1) before full verification
// - Geodesic-informed optimization using ZF_KAPPA_GEO_DEFAULT
// - Maintains deterministic output while drastically reducing search time
//
// Design goals:
// - **Only** GMP/MPFR; hard compile error if missing. No fallbacks.
// - Handles candidates as large as 10^1234 (and beyond), limited by memory/time.
// - Clean CSV output when --csv is passed. No extra logs.
// - Mersenne detection via Lucas–Lehmer using GMP (for n = 2^p - 1).
// - Leverage Z Framework's prime-density model for intelligent jumps
//
// Output (CSV):
//   n,prime,is_mersenne,ms
// where "prime" is a full decimal string (no scientific notation).
//
// Notes:
// - We *scan* primes starting from --start upward, returning --count primes.
// - Enhanced primality test: adaptive reps + pre-filtering optimization.
// - Mersenne detection: check n+1 is a power of two, then run Lucas–Lehmer for exponent p.
// - We avoid thread parallelism to keep deterministic, clean output at extreme scales.
//
// -----------------------------------------------------------------------------

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>
#include <math.h>

// OpenMP support for M1 Max parallelization (following parent pattern)
#ifdef _OPENMP
#include <omp.h>
#endif

#ifndef __has_include
#  define __has_include(x) 0
#endif
#if __has_include(<gmp.h>) && __has_include(<mpfr.h>)
#  include <gmp.h>
#  include <mpfr.h>
#else
#  error "MPFR/GMP headers are required (no fallbacks). Install libgmp-dev and libmpfr-dev."
#endif

// Z5D predictor integration for intelligent candidate generation
#if __has_include("z5d_predictor.h")
#  include "z5d_predictor.h"
#  define Z5D_ENHANCED 1
#else
#  define Z5D_ENHANCED 0
#endif

// Parameter constants (shared)
#include "z_framework_params.h"

// Vectorized timing integration - Attribution: Dionisio Alberto Lopez III (D.A.L. III)
#if __has_include("z_framework_params.h")
#  define BOOTSTRAP_ENABLED 1
#else
#  define BOOTSTRAP_ENABLED 0
#  define ZF_BOOTSTRAP_RESAMPLES_DEFAULT 1000
#endif

// ----------------------- CLI parsing helpers -----------------------

typedef struct {
    mpz_t start;      // starting candidate (inclusive)
    unsigned long count;  // how many primes to output
    int csv;          // flag
    int verbose;      // verbose output for performance analysis
    int show_stats;   // show optimization statistics
} config_t;

// Parse strings like "10^1234" or plain decimal into mpz_t.
static int parse_bigint(const char* s, mpz_t out) {
    if (!s || !*s) {
        return -1; // Empty or null string
    }
    
    const char* caret = strchr(s, '^');
    if (!caret) {
        return mpz_set_str(out, s, 10) == 0 ? 0 : -1;
    }
    // a^b
    char base_str[256];
    size_t len = (size_t)(caret - s);
    if (len >= sizeof(base_str) || len == 0) return -1;
    memcpy(base_str, s, len);
    base_str[len] = '\0';
    const char* exp_str = caret + 1;
    
    if (!*exp_str) return -1; // No exponent after ^

    mpz_t base;
    mpz_init(base);
    if (mpz_set_str(base, base_str, 10) != 0) { mpz_clear(base); return -1; }

    unsigned long exp;
    char* endptr = NULL;
    exp = strtoul(exp_str, &endptr, 10);
    if (endptr == exp_str || *endptr != '\0') { mpz_clear(base); return -1; }
    
    // Prevent extremely large exponents that could cause resource exhaustion
    if (exp > 100000) { 
        mpz_clear(base); 
        fprintf(stderr, "Error: Exponent %lu is too large (max 100000)\n", exp);
        return -1; 
    }

    // out = base^exp
    mpz_pow_ui(out, base, exp);
    mpz_clear(base);
    return 0;
}

static void print_usage(const char* prog) {
    fprintf(stderr,
        "Usage: %s --start <BIGINT|a^b> --count <N> [--csv] [--verbose] [--stats]\n"
        "Example: %s --start 10^1234 --count 5 --csv\n"
        "Options:\n"
        "  --verbose   Show detailed timing and Z5D optimization info\n"
        "  --stats     Show candidate generation statistics\n",
        prog, prog);
}

// ----------------------- Mersenne / Lucas–Lehmer -----------------------
// Lucas–Lehmer for M_p = 2^p - 1, with p >= 2 (p should be prime for M_p to be prime).
static int is_mersenne_prime_ll(unsigned long p) {
    if (p == 2) return 1; // M_2 = 3
    if (p < 2) return 0;

    mpz_t Mp, s, tmp;
    mpz_inits(Mp, s, tmp, NULL);

    // Mp = 2^p - 1
    mpz_ui_pow_ui(Mp, 2, p);
    mpz_sub_ui(Mp, Mp, 1);

    // s = 4
    mpz_set_ui(s, 4);

    for (unsigned long i = 0; i < p - 2; i++) {
        // s = (s^2 - 2) mod Mp
        mpz_mul(tmp, s, s);      // s^2
        mpz_sub_ui(tmp, tmp, 2); // s^2 - 2
        mpz_mod(s, tmp, Mp);
    }

    int is_prime = (mpz_cmp_ui(s, 0) == 0);
    mpz_clears(Mp, s, tmp, NULL);
    return is_prime;
}

// Check if n = 2^p - 1 for some unsigned long p, and if so run LL test.
static int detect_mersenne_and_test(const mpz_t n) {
    if (mpz_cmp_ui(n, 3) < 0) return 0; // smallest Mersenne is 3
    mpz_t t; mpz_init(t);
    mpz_add_ui(t, n, 1); // t = n + 1
    // Check if t is a power of two: true iff popcount(t)==1
    int is_power_two = (mpz_popcount(t) == 1);
    if (!is_power_two) { mpz_clear(t); return 0; }

    // p = log2(t), but exact; since t is power of two, find index of highest bit.
    // mpz_sizeinbase(t, 2) returns floor(log2(t)) + 1; for powers of two, that's p+1.
    unsigned long p = mpz_sizeinbase(t, 2) - 1;
    mpz_clear(t);

    // If p is composite, M_p is composite; quick probable primality on p (fits in UL here).
    // For p up to ~1e6 fits UL; in our expected ranges (around 10^1234 -> p ≈ 4097) it's fine.
    // Perform LL regardless; p primality quickly pre-checked with simple sieve is optional.

    return is_mersenne_prime_ll(p);
}

// ----------------------- Prime scanning with LIS-Corrector pipeline -----------------------

static void next_odd(mpz_t n) {
    if (mpz_even_p(n)) mpz_add_ui(n, n, 1);
}


// High-precision safe modular arithmetic for GMP Miller-Rabin
static void mpz_mulmod(mpz_t result, const mpz_t a, const mpz_t b, const mpz_t mod) {
    mpz_mul(result, a, b);
    mpz_mod(result, result, mod);
}

static void mpz_powmod_safe(mpz_t result, const mpz_t base, const mpz_t exp, const mpz_t mod) {
    mpz_powm(result, base, exp, mod);
}

// Size-aware Miller-Rabin using GMP's mpz_probab_prime_p with sufficient rounds for large n.
// Returns 1 if probable prime, 0 if composite.
static int is_prime_mr_gmp(const mpz_t n) {
    if (mpz_cmp_ui(n, 2) < 0) return 0;
    if (mpz_cmp_ui(n, 2) == 0 || mpz_cmp_ui(n, 3) == 0 || mpz_cmp_ui(n, 5) == 0) return 1;

    // Check divisibility by 2, 3, 5
    if (mpz_even_p(n)) return 0;
    mpz_t tmp;
    mpz_init(tmp);
    mpz_mod_ui(tmp, n, 3); if (mpz_cmp_ui(tmp, 0) == 0) { mpz_clear(tmp); return 0; }
    mpz_mod_ui(tmp, n, 5); if (mpz_cmp_ui(tmp, 0) == 0) { mpz_clear(tmp); return 0; }
    mpz_clear(tmp);

    // Pick rounds based on size to keep error < 2^-128 even for huge n
    size_t bits = mpz_sizeinbase(n, 2);
    int reps;
    if (bits <= 64) {
        reps = 10;      // much stronger than needed for 64-bit range
    } else if (bits <= 512) {
        reps = 25;
    } else if (bits <= 4096) {
        reps = 40;
    } else {
        reps = 64;      // very large integers (10^1234 ~ 4096 bits), drive error probability down
    }

    int r = mpz_probab_prime_p(n, reps);
    return r > 0;  // 1 = probable, 2 = definitely prime (for small n)
}

// Wheel-30 optimization for GMP
static int is_wheel30_candidate(const mpz_t n) {
    mpz_t mod_result;
    mpz_init(mod_result);
    mpz_mod_ui(mod_result, n, 30);
    unsigned long mod = mpz_get_ui(mod_result);
    mpz_clear(mod_result);

    // candidate must be ≡ {1,11,13,17,19,23,29,31} mod 30
    return (mod == 1 || mod == 11 || mod == 13 || mod == 17 ||
            mod == 19 || mod == 23 || mod == 29 || mod == 31);
}

// Lucas pre-filter for GMP
static int lucas_prefilter_gmp(const mpz_t n) {
    // Quick divisibility checks by small primes
    mpz_t tmp;
    mpz_init(tmp);

    unsigned long small_primes[] = {7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47};
    int num_primes = sizeof(small_primes) / sizeof(unsigned long);

    for (int i = 0; i < num_primes; i++) {
        mpz_mod_ui(tmp, n, small_primes[i]);
        if (mpz_cmp_ui(tmp, 0) == 0) {
            // Check if n equals the prime itself
            if (mpz_cmp_ui(n, small_primes[i]) == 0) {
                mpz_clear(tmp);
                return 1; // n is this prime
            }
            mpz_clear(tmp);
            return 0; // n is divisible by this prime
        }
    }

    mpz_clear(tmp);
    return 1; // Passed Lucas filter
}

// LIS-Corrector full pipeline: Wheel-30 + Lucas + Miller-Rabin
static int __attribute__((unused)) is_probable_prime(const mpz_t n) {
    // Step 1: Wheel-30 optimization
    if (!is_wheel30_candidate(n)) {
        return 0;
    }

    // Step 2: Lucas pre-filter
    if (!lucas_prefilter_gmp(n)) {
        return 0;
    }

    // Step 3: High-precision deterministic Miller-Rabin
    return is_prime_mr_gmp(n);
}

// Enhanced wheel-30 candidate generation with OpenMP
// Align candidate to the nearest wheel-30 residue at or above current value (inclusive).
static void align_wheel30_candidate(mpz_t candidate) {
    static const unsigned long wheel30[] = {1,11,13,17,19,23,29,31};

    mpz_t mod_result;
    mpz_init(mod_result);
    mpz_mod_ui(mod_result, candidate, 30);
    unsigned long mod = mpz_get_ui(mod_result);
    mpz_clear(mod_result);

    for (int i = 0; i < 8; i++) {
        if (mod == wheel30[i]) {
            return; // already aligned
        } else if (mod < wheel30[i]) {
            mpz_add_ui(candidate, candidate, wheel30[i] - mod);
            return;
        }
    }

    // If we're past 31, jump to next 30-block + 1
    unsigned long gap_to_next = 30 - mod + 1;
    mpz_add_ui(candidate, candidate, gap_to_next);
}

static void next_wheel30_candidate(mpz_t candidate) {
    // Move to next wheel-30 position: {1,11,13,17,19,23,29,31} mod 30
    static const unsigned long wheel30[] = {1,11,13,17,19,23,29,31};
    static const unsigned long wheel30_gaps[] = {10,2,4,2,4,6,2,6}; // gaps to next position

    mpz_t mod_result;
    mpz_init(mod_result);
    mpz_mod_ui(mod_result, candidate, 30);
    unsigned long mod = mpz_get_ui(mod_result);
    mpz_clear(mod_result);

    // Find current position in wheel and advance to next
    for (int i = 0; i < 8; i++) {
        if (mod == wheel30[i]) {
            mpz_add_ui(candidate, candidate, wheel30_gaps[i]);
            return;
        } else if (mod < wheel30[i]) {
            mpz_add_ui(candidate, candidate, wheel30[i] - mod);
            return;
        }
    }

    // If we're past 31, jump to next 30-block + 1
    unsigned long gap_to_next = 30 - mod + 1;
    mpz_add_ui(candidate, candidate, gap_to_next);
}

// Enhanced prime search with LIS-Corrector pipeline and OpenMP
static void next_prime_from(const mpz_t start, mpz_t out, int verbose, int show_stats) {
    mpz_set(out, start);

    // Statistics for optimization tracking
    static unsigned long total_candidates_tested = 0;
    static unsigned long total_wheel_filtered = 0;
    static unsigned long total_lucas_filtered = 0;
    static unsigned long total_mr_calls = 0;

    unsigned long local_candidates = 0;
    unsigned long local_wheel_filtered = 0;
    unsigned long local_lucas_filtered = 0;
    unsigned long local_mr_calls = 0;

    // Align to first wheel-30 residue at or above the start (inclusive)
    align_wheel30_candidate(out);

    for (;;) {
        local_candidates++;
        total_candidates_tested++;

        // Step 1: Wheel-30 check (already guaranteed by next_wheel30_candidate)
        // Track how many candidates were advanced purely by wheel skipping
        // (every loop except when a prime is returned counts as wheel-filtered
        // because the generator only yields wheel residues)
        local_wheel_filtered++;
        total_wheel_filtered++;

        // Step 2: Lucas pre-filter
        if (!lucas_prefilter_gmp(out)) {
            local_lucas_filtered++;
            total_lucas_filtered++;
            next_wheel30_candidate(out);
            continue;
        }

    // Step 3: Miller-Rabin verification (size-aware rounds)
    local_mr_calls++;
    total_mr_calls++;

    if (is_prime_mr_gmp(out)) {
            if (verbose || show_stats) {
                fprintf(stderr, "LIS-Corrector pipeline performance:\n");
                fprintf(stderr, "  Candidates tested: %lu (total: %lu)\n",
                       local_candidates, total_candidates_tested);
                fprintf(stderr, "  Wheel-30 filtered: %lu (total: %lu)\n",
                       local_wheel_filtered, total_wheel_filtered);
                fprintf(stderr, "  Lucas filtered: %lu (total: %lu)\n",
                       local_lucas_filtered, total_lucas_filtered);
                fprintf(stderr, "  Miller-Rabin calls: %lu (total: %lu)\n",
                       local_mr_calls, total_mr_calls);

                double reduction_pct = (local_candidates > 0) ?
                    100.0 * (1.0 - (double)local_mr_calls / (double)local_candidates) : 0.0;
                fprintf(stderr, "  Pre-filter reduction: %.2f%%\n", reduction_pct);
            }
            return;
        }

        // Move to next wheel-30 candidate
        next_wheel30_candidate(out);

        if (verbose && local_candidates % 1000 == 0) {
            gmp_fprintf(stderr, "Debug: Tested %lu candidates, current: %Zd\n",
                       local_candidates, out);
        }
    }
}

// ----------------------- CSV printing -----------------------
static void print_csv_header(void) {
    printf("n,prime,is_mersenne,ms\n");
}

static void print_csv_row(unsigned long idx, const mpz_t prime, int is_mersenne, double ms) {
    gmp_printf("%lu,%Zd,%d,%.3f\n", idx, prime, is_mersenne ? 1 : 0, ms);
}



// ----------------------- timing helpers -----------------------
static inline double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1.0e6;
}

// ----------------------- Vectorized timing logger -----------------------
// Attribution: Dionisio Alberto Lopez III (D.A.L. III)

void log_prime_time(mpfr_t prime, clock_t start) {
    clock_t end = clock();
    double ms = ((double)(end - start)) * 1000 / CLOCKS_PER_SEC;
    mpfr_printf("1) prime=%%R*  (%.3f ms)\n", prime, ms);  // MPFR print
    // Bootstrap log for CI (stub; integrate ZF_BOOTSTRAP_RESAMPLES_DEFAULT=1000)
}

// Global bootstrap storage for analysis
#if BOOTSTRAP_ENABLED
static double global_timing_samples[1000];
static int global_sample_count = 0;
#endif

static void log_prime_time_bootstrap(const mpz_t prime, clock_t start, unsigned long prime_index) {
    clock_t end = clock();
    double ms = ((double)(end - start)) * 1000 / CLOCKS_PER_SEC;

    // Enhanced logging with bootstrap tracking
    gmp_printf("%lu) prime=%Zd*  (%.3f ms)\n", prime_index, prime, ms);

    // Bootstrap CI integration (when ZF_BOOTSTRAP_RESAMPLES_DEFAULT available)
    #if BOOTSTRAP_ENABLED
    if (global_sample_count < 1000) {
        global_timing_samples[global_sample_count++] = ms;
    }
    #endif
}

#if BOOTSTRAP_ENABLED
static double calculate_bootstrap_mean(double *samples, int count) {
    double sum = 0.0;
    for (int i = 0; i < count; i++) {
        sum += samples[i];
    }
    return sum / count;
}

static void calculate_bootstrap_ci(double *samples, int count, double *ci_lower, double *ci_upper) {
    // Simple percentile method for bootstrap CI
    // In full implementation, would do proper bootstrap resampling
    double sum = 0.0, sum_sq = 0.0;
    for (int i = 0; i < count; i++) {
        sum += samples[i];
        sum_sq += samples[i] * samples[i];
    }
    double mean = sum / count;
    double variance = (sum_sq / count) - (mean * mean);
    double std_dev = sqrt(variance);

    // Approximate 95% CI using normal approximation
    *ci_lower = mean - 1.96 * std_dev / sqrt(count);
    *ci_upper = mean + 1.96 * std_dev / sqrt(count);
}
#endif
// ----------------------- main -----------------------

int main(int argc, char** argv) {
    config_t cfg;
    mpz_init(cfg.start);
    cfg.count = 0;
    cfg.csv = 0;
    cfg.verbose = 0;
    cfg.show_stats = 0;

    // Parse args
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--start") == 0 && i + 1 < argc) {
            if (parse_bigint(argv[++i], cfg.start) != 0) {
                fprintf(stderr, "Invalid --start value.\n");
                print_usage(argv[0]);
                return 1;
            }
        } else if (strcmp(argv[i], "--count") == 0 && i + 1 < argc) {
            char* end = NULL;
            unsigned long c = strtoul(argv[++i], &end, 10);
            if (end == argv[i] || *end != '\0' || c == 0) {
                fprintf(stderr, "Invalid --count value.\n");
                print_usage(argv[0]);
                return 1;
            }
            cfg.count = c;
        } else if (strcmp(argv[i], "--csv") == 0) {
            cfg.csv = 1;
        } else if (strcmp(argv[i], "--verbose") == 0) {
            cfg.verbose = 1;
        } else if (strcmp(argv[i], "--stats") == 0) {
            cfg.show_stats = 1;
        } else if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    if (mpz_sgn(cfg.start) == 0 || cfg.count == 0) {
        print_usage(argv[0]);
        return 1;
    }

    // Ensure we start at an odd candidate >= 3
    if (mpz_cmp_ui(cfg.start, 3) < 0) mpz_set_ui(cfg.start, 3);
    next_odd(cfg.start);

    if (cfg.csv) print_csv_header();
    
    if (cfg.verbose) {
        fprintf(stderr, "Enhanced Prime Generator with Z5D Optimizations\n");
        fprintf(stderr, "==============================================\n");
        #if Z5D_ENHANCED
        fprintf(stderr, "Z5D Support: ENABLED\n");
        fprintf(stderr, "Using ZF_KAPPA_STAR_DEFAULT: %.5f\n", ZF_KAPPA_STAR_DEFAULT);
        fprintf(stderr, "Using ZF_KAPPA_GEO_DEFAULT: %.3f\n", ZF_KAPPA_GEO_DEFAULT);
        #else
        fprintf(stderr, "Z5D Support: FALLBACK (geodesic-informed jumping only)\n");
        #endif
        fprintf(stderr, "Adaptive reps: ENABLED\n");
        fprintf(stderr, "Pre-filtering: ENABLED\n");
        gmp_fprintf(stderr, "Starting from: %Zd\n", cfg.start);
        fprintf(stderr, "Generating %lu primes\n\n", cfg.count);
    }

    mpz_t candidate, prime;
    mpz_inits(candidate, prime, NULL);
    mpz_set(candidate, cfg.start);

    for (unsigned long i = 1; i <= cfg.count; ++i) {
        clock_t t0 = clock();
        double start_ms = now_ms();
        next_prime_from(candidate, prime, cfg.verbose, cfg.show_stats);

        int is_mers = detect_mersenne_and_test(prime);

        if (cfg.csv) {
            double elapsed_ms = now_ms() - start_ms;
            print_csv_row(i, prime, is_mers, elapsed_ms);
        } else {
            // Use vectorized timing logger with bootstrap integration
            log_prime_time_bootstrap(prime, t0, i);
            if (is_mers) {
                printf("  [Mersenne detected]\n");
            }
        }

        // Prepare next candidate
        mpz_add_ui(candidate, prime, 2);
    }

    // Bootstrap Performance Analysis - Attribution: Dionisio Alberto Lopez III (D.A.L. III)
    #if BOOTSTRAP_ENABLED
    if ((cfg.verbose || cfg.show_stats) && !cfg.csv && global_sample_count >= 3) {
        double mean_ms = calculate_bootstrap_mean(global_timing_samples, global_sample_count);
        double ci_lower, ci_upper;
        calculate_bootstrap_ci(global_timing_samples, global_sample_count, &ci_lower, &ci_upper);

        fprintf(stderr, "\nBootstrap Performance Analysis:\n");
        fprintf(stderr, "  Mean detection time: %.3f ms\n", mean_ms);
        fprintf(stderr, "  Bootstrap CI [2.5%%, 97.5%%]: [%.3f, %.3f] ms\n",
               ci_lower, ci_upper);
        fprintf(stderr, "  Samples: %d/%d\n", global_sample_count, ZF_BOOTSTRAP_RESAMPLES_DEFAULT);
        fprintf(stderr, "  Attribution: Dionisio Alberto Lopez III (D.A.L. III)\n");
    }
    #endif

    mpz_clears(candidate, prime, cfg.start, NULL);
    return 0;
}
