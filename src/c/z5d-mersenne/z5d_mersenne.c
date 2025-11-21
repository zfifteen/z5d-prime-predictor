/*
 * z5d_mersenne.c - Wave-Knob Invariant, Self-Tuning Prime Scan
 * ==============================================================
 *
 * MPFR/GMP-only implementation of the Z Framework Wave-Knob system.
 * Implements adaptive (window, step) scanning to find R* where prime_count = 1.
 *
 * Features:
 * - High-precision arithmetic (configurable MPFR precision)
 * - Wave-ratio scanning with R = window/step invariant
 * - Self-tuning algorithm to lock onto resonance valleys
 * - Wheel-based coprime offset scanning (mod 210)
 * - JSON telemetry output for scientific analysis
 * - Miller-Rabin primality testing with configurable rounds
 *
 * Build: see Makefile in this folder (Apple Silicon / Homebrew MPFR+GMP)
 *
 * Usage Examples:
 *   ./z5d_mersenne 1e100 --prec=4096 --scan --window=4200 --step=18
 *   ./z5d_mersenne 1e100 --auto-tune --target=1 --wheel=210 --json
 *
 * @author Unified Framework Team
 * @version 1.0 (Wave-Knob Initial Implementation)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <getopt.h>
#include <mpfr.h>
#include <gmp.h>
#include "z5d_predictor.h"

#define VERSION "1.0.0"
#define DEFAULT_PRECISION 4096
#define DEFAULT_MR_ROUNDS 50
#define DEFAULT_WINDOW 64
#define DEFAULT_STEP 2
#define DEFAULT_MAX_ITERS 100
#define DEFAULT_WHEEL 210

// Wave-knob scanning configuration
typedef struct {
    unsigned long window;        // aperture around prediction
    unsigned long step;          // scanning increment
    unsigned long wheel_mod;     // coprime wheel modulus (30, 210, 2310)
    unsigned long max_iters;     // max adjustment iterations
    unsigned int target_count;   // target prime count (usually 1)
    unsigned int mr_rounds;      // Miller-Rabin test rounds
    mpfr_prec_t precision;       // MPFR precision in bits
    int auto_tune;              // enable self-tuning mode
    int json_output;            // JSON telemetry output
    int verbose;                // verbose output
    char *output_file;          // output file path
} wave_config_t;

// Scanning results and telemetry
typedef struct {
    mpz_t k_value;              // input k
    unsigned long window;        // final window used
    unsigned long step;          // final step used
    double ratio;               // R = window/step
    unsigned int prime_count;    // number of primes found
    unsigned int iterations;     // tuning iterations needed
    unsigned long mr_calls;      // total Miller-Rabin calls
    double elapsed_ms;          // elapsed time in milliseconds
    mpz_t prime_found;          // the prime found (if count=1)
    int locked;                 // 1 if successfully locked to target
    char wheel_residue[64];     // wheel residue pattern used
} wave_result_t;

// Wheel definitions for coprime scanning
typedef struct {
    unsigned long modulus;
    unsigned long *offsets;
    size_t count;
} wheel_t;

// Pre-computed wheel offsets (coprime residues)
static unsigned long wheel_30[] = {1, 7, 11, 13, 17, 19, 23, 29};
static unsigned long wheel_210[] = {
    1, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
    101, 103, 107, 109, 113, 121, 127, 131, 137, 139, 143, 149, 151, 157, 163, 167, 169,
    173, 179, 181, 187, 191, 193, 197, 199, 209
};

static wheel_t wheels[] = {
    {30, wheel_30, sizeof(wheel_30)/sizeof(wheel_30[0])},
    {210, wheel_210, sizeof(wheel_210)/sizeof(wheel_210[0])},
    {0, NULL, 0} // sentinel
};

// Global statistics
static unsigned long g_total_mr_calls = 0;
static clock_t g_start_time;

// Function prototypes
static void print_usage(const char *prog_name);
static void print_version(void);
static int parse_arguments(int argc, char **argv, wave_config_t *config, mpfr_t k_input);
static void init_wave_config(wave_config_t *config);
static void cleanup_wave_config(wave_config_t *config);
static void init_wave_result(wave_result_t *result);
static void cleanup_wave_result(wave_result_t *result);
static wheel_t *get_wheel(unsigned long modulus);
static int miller_rabin_test(const mpz_t n, unsigned int rounds);
static int scan_prime_count(const mpfr_t prediction, unsigned long window, unsigned long step, 
                          wheel_t *wheel, unsigned int mr_rounds, mpz_t *found_primes, 
                          unsigned int max_primes);
static int auto_tune_scan(const mpfr_t prediction, wave_config_t *config, wave_result_t *result);
static int manual_scan(const mpfr_t prediction, wave_config_t *config, wave_result_t *result);
static void output_json_result(const wave_result_t *result, FILE *fp);
static void output_human_result(const wave_result_t *result, const wave_config_t *config);
static double compute_z5d_prediction_mpfr(const mpfr_t k, mpfr_t result, mpfr_prec_t prec);

int main(int argc, char **argv) {
    wave_config_t config;
    wave_result_t result;
    mpfr_t k_input, prediction;
    int ret = 0;
    int mpfr_inited = 0;
    int result_inited = 0;
    
    g_start_time = clock();
    
    // Initialize configuration first
    init_wave_config(&config);
    
    // Parse arguments to get precision setting
    int parse_ret = parse_arguments(argc, argv, &config, NULL);  // Pass NULL for k_input initially
    if (parse_ret != 0) {
        // parse_ret > 0 indicates help/version was handled
        cleanup_wave_config(&config);
        return (parse_ret > 0) ? 0 : 1;
    }
    
    // Now initialize MPFR with correct precision
    mpfr_init2(k_input, config.precision);
    mpfr_init2(prediction, config.precision);
    mpfr_inited = 1;
    
    // Re-parse k value with correct precision
    if (mpfr_set_str(k_input, argv[1], 0, MPFR_RNDN) != 0) {
        fprintf(stderr, "Error: Invalid k value '%s'\n", argv[1]);
        ret = 1;
        goto cleanup;
    }
    
    // Initialize result structure
    init_wave_result(&result);
    result_inited = 1;
    
    if (config.verbose) {
        printf("Wave-Knob Prime Scanner v%s\n", VERSION);
        printf("MPFR precision: %lu bits (~%lu decimal digits)\n", 
               config.precision, (unsigned long)(config.precision * 0.30103));
        printf("Target k: ");
        mpfr_printf("%.Rg\n", k_input);  // Use %Rg for better formatting
    }
    
    // Copy k to result (convert MPFR to MPZ)
    mpfr_get_z(result.k_value, k_input, MPFR_RNDN);
    
    // Compute Z5D prediction with high precision
    double pred_time = compute_z5d_prediction_mpfr(k_input, prediction, config.precision);
    
    if (config.verbose) {
        printf("Z5D prediction: ");
        mpfr_printf("%.Rg", prediction);  // Better scientific notation formatting
        printf(" (computed in %.3f ms)\n", pred_time * 1000.0);
    }
    
    // Perform scanning (auto-tune or manual)
    if (config.auto_tune) {
        ret = auto_tune_scan(prediction, &config, &result);
    } else {
        ret = manual_scan(prediction, &config, &result);
    }
    
    // Output results
    if (config.json_output) {
        FILE *fp = config.output_file ? fopen(config.output_file, "w") : stdout;
        if (fp) {
            output_json_result(&result, fp);
            if (fp != stdout) fclose(fp);
        }
    } else {
        output_human_result(&result, &config);
    }
    
cleanup:
    cleanup_wave_config(&config);
    if (result_inited) {
        cleanup_wave_result(&result);
    }
    if (mpfr_inited) {
        mpfr_clear(k_input);
        mpfr_clear(prediction);
        mpfr_free_cache();
    }
    
    return ret;
}

static void print_usage(const char *prog_name) {
    printf("Usage: %s <k> [options]\n", prog_name);
    printf("\nWave-Knob Invariant Prime Scanner\n");
    printf("Searches for primes using adaptive (window, step) parameters\n\n");
    
    printf("Positional arguments:\n");
    printf("  k                     Target index (supports scientific notation)\n\n");
    
    printf("Scanning options:\n");
    printf("  --scan                Enable manual scanning mode\n");
    printf("  --auto-tune           Enable self-tuning mode (default)\n");
    printf("  --window=N            Search window size (default: %d)\n", DEFAULT_WINDOW);
    printf("  --step=N              Scanning step size (default: %d)\n", DEFAULT_STEP);
    printf("  --target=N            Target prime count (default: 1)\n");
    printf("  --wheel=N             Coprime wheel modulus: 30, 210 (default: %d)\n", DEFAULT_WHEEL);
    printf("  --max-iters=N         Max tuning iterations (default: %d)\n", DEFAULT_MAX_ITERS);
    
    printf("\nPrecision options:\n");
    printf("  --prec=N              MPFR precision in bits (default: %d)\n", DEFAULT_PRECISION);
    printf("  --mr-rounds=N         Miller-Rabin test rounds (default: %d)\n", DEFAULT_MR_ROUNDS);
    
    printf("\nOutput options:\n");
    printf("  --json                Output results in JSON format\n");
    printf("  --output=FILE         Output file path (default: stdout)\n");
    printf("  --verbose, -v         Verbose output\n");
    printf("  --help, -h            Show this help message\n");
    printf("  --version             Show version information\n");
    
    printf("\nExamples:\n");
    printf("  %s 1e100 --prec=6144 --scan --window=4200 --step=18\n", prog_name);
    printf("  %s 1e100 --auto-tune --target=1 --wheel=210 --json\n", prog_name);
    printf("  %s 1e300 --prec=8192 --auto-tune --max-iters=200 --verbose\n", prog_name);
}

static void print_version(void) {
    printf("z5d_mersenne version %s\n", VERSION);
    printf("Wave-Knob Invariant Prime Scanner\n");
    printf("Built with MPFR %s, GMP %s\n", mpfr_get_version(), gmp_version);
    printf("Part of the Unified Z Framework\n");
}

static void init_wave_config(wave_config_t *config) {
    config->window = DEFAULT_WINDOW;
    config->step = DEFAULT_STEP;
    config->wheel_mod = DEFAULT_WHEEL;
    config->max_iters = DEFAULT_MAX_ITERS;
    config->target_count = 1;
    config->mr_rounds = DEFAULT_MR_ROUNDS;
    config->precision = DEFAULT_PRECISION;
    config->auto_tune = 1; // default to auto-tune
    config->json_output = 0;
    config->verbose = 0;
    config->output_file = NULL;
}

static void cleanup_wave_config(wave_config_t *config) {
    if (config->output_file) {
        free(config->output_file);
        config->output_file = NULL;
    }
}

static void init_wave_result(wave_result_t *result) {
    mpz_init(result->k_value);
    mpz_init(result->prime_found);
    result->window = 0;
    result->step = 0;
    result->ratio = 0.0;
    result->prime_count = 0;
    result->iterations = 0;
    result->mr_calls = 0;
    result->elapsed_ms = 0.0;
    result->locked = 0;
    strcpy(result->wheel_residue, "none");
}

static void cleanup_wave_result(wave_result_t *result) {
    mpz_clear(result->k_value);
    mpz_clear(result->prime_found);
}

static int parse_arguments(int argc, char **argv, wave_config_t *config, mpfr_t k_input) {
    static struct option long_options[] = {
        {"scan", no_argument, 0, 's'},
        {"auto-tune", no_argument, 0, 'a'},
        {"window", required_argument, 0, 'w'},
        {"step", required_argument, 0, 't'},
        {"target", required_argument, 0, 'T'},
        {"wheel", required_argument, 0, 'W'},
        {"max-iters", required_argument, 0, 'i'},
        {"prec", required_argument, 0, 'p'},
        {"mr-rounds", required_argument, 0, 'm'},
        {"json", no_argument, 0, 'j'},
        {"output", required_argument, 0, 'o'},
        {"verbose", no_argument, 0, 'v'},
        {"help", no_argument, 0, 'h'},
        {"version", no_argument, 0, 'V'},
        {0, 0, 0, 0}
    };
    
    int c;
    int option_index = 0;
    char *k_string = NULL;  // Save k string for re-parsing with new precision
    
    // Quick check for help/version before requiring k
    if (argc >= 2 && (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0)) {
        print_usage(argv[0]);
        return 1;  // signal handled (no error)
    }
    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        print_version();
        return 1;  // signal handled (no error)
    }
    
    if (argc < 2) {
        print_usage(argv[0]);
        return -1;
    }
    
    // Save k string for later parsing
    k_string = strdup(argv[1]);
    
    // Parse options starting from argv[2]
    optind = 2;  // Skip program name and k value
    
    // Parse options first to get precision
    while ((c = getopt_long(argc, argv, "saw:t:T:W:i:p:m:jo:vhV", long_options, &option_index)) != -1) {
        switch (c) {
            case 's':
                config->auto_tune = 0;
                break;
            case 'a':
                config->auto_tune = 1;
                break;
            case 'w':
                config->window = strtoul(optarg, NULL, 10);
                break;
            case 't':
                config->step = strtoul(optarg, NULL, 10);
                break;
            case 'T':
                config->target_count = strtoul(optarg, NULL, 10);
                break;
            case 'W':
                config->wheel_mod = strtoul(optarg, NULL, 10);
                break;
            case 'i':
                config->max_iters = strtoul(optarg, NULL, 10);
                break;
            case 'p':
                config->precision = strtoul(optarg, NULL, 10);
                break;
            case 'm':
                config->mr_rounds = strtoul(optarg, NULL, 10);
                break;
            case 'j':
                config->json_output = 1;
                break;
            case 'o':
                config->output_file = strdup(optarg);
                break;
            case 'v':
                config->verbose = 1;
                break;
            case 'h':
                print_usage(argv[0]);
                free(k_string);
                return -1;
            case 'V':
                print_version();
                free(k_string);
                return -1;
            case '?':
                fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
                free(k_string);
                return -1;
            default:
                free(k_string);
                return -1;
        }
    }
    
    // Now parse k with final precision (only if k_input is provided)
    if (k_input) {
        if (mpfr_set_str(k_input, k_string, 0, MPFR_RNDN) != 0) {
            fprintf(stderr, "Error: Invalid k value '%s'\n", k_string);
            free(k_string);
            return -1;
        }
        
        // Validate k
        if (mpfr_cmp_ui(k_input, 2) < 0) {
            free(k_string);
            fprintf(stderr, "Error: k must be >= 2\n");
            return -1;
        }
    }
    
    free(k_string);
    
    if (config->window == 0 || config->step == 0) {
        fprintf(stderr, "Error: window and step must be > 0\n");
        return -1;
    }
    
    if (config->precision < 64 || config->precision > 131072) {
        fprintf(stderr, "Error: precision must be between 64 and 131072 bits\n");
        return -1;
    }
    
    // Validate wheel modulus
    wheel_t *wheel = get_wheel(config->wheel_mod);
    if (!wheel) {
        fprintf(stderr, "Error: unsupported wheel modulus %lu (supported: 30, 210)\n", config->wheel_mod);
        return -1;
    }
    
    return 0;
}

static wheel_t *get_wheel(unsigned long modulus) {
    for (int i = 0; wheels[i].modulus != 0; i++) {
        if (wheels[i].modulus == modulus) {
            return &wheels[i];
        }
    }
    return NULL;
}

// Placeholder implementations - will implement the core scanning logic next
static double compute_z5d_prediction_mpfr(const mpfr_t k, mpfr_t result, mpfr_prec_t prec) {
    clock_t start = clock();
    
    // High-precision Z5D prediction using only MPFR (no double fallback)
    mpfr_t log_k, log_log_k, pnt_base, adjustment;
    
    mpfr_init2(log_k, prec);
    mpfr_init2(log_log_k, prec);  
    mpfr_init2(pnt_base, prec);
    mpfr_init2(adjustment, prec);
    
    // Compute log(k)
    mpfr_log(log_k, k, MPFR_RNDN);
    
    // Compute log(log(k))
    mpfr_log(log_log_k, log_k, MPFR_RNDN);
    
    // Prime Number Theorem estimate: k * (log(k) + log(log(k)) - 1)
    mpfr_add(pnt_base, log_k, log_log_k, MPFR_RNDN);      // log(k) + log(log(k))
    mpfr_sub_ui(pnt_base, pnt_base, 1, MPFR_RNDN);         // - 1
    mpfr_mul(pnt_base, k, pnt_base, MPFR_RNDN);             // k * (...)
    
    // Simple Z5D adjustment (placeholder for full Z5D formula)
    // adjustment = k^0.04 * log(k) / 100  (empirical correction)
    mpfr_set_d(adjustment, 0.04, MPFR_RNDN);               // 0.04
    mpfr_pow(adjustment, k, adjustment, MPFR_RNDN);         // k^0.04
    mpfr_mul(adjustment, adjustment, log_k, MPFR_RNDN);     // * log(k)
    mpfr_div_ui(adjustment, adjustment, 100, MPFR_RNDN);    // / 100
    
    // Final prediction: PNT + adjustment
    mpfr_add(result, pnt_base, adjustment, MPFR_RNDN);
    
    mpfr_clear(log_k);
    mpfr_clear(log_log_k);
    mpfr_clear(pnt_base);
    mpfr_clear(adjustment);
    
    return (double)(clock() - start) / CLOCKS_PER_SEC;
}

static int miller_rabin_test(const mpz_t n, unsigned int rounds) {
    g_total_mr_calls++;
    return mpz_probab_prime_p(n, rounds);
}

static int scan_prime_count(const mpfr_t prediction, unsigned long window, unsigned long step,
                          wheel_t *wheel, unsigned int mr_rounds, mpz_t *found_primes,
                          unsigned int max_primes) {
    mpz_t center, candidate;
    unsigned int count = 0;
    static unsigned int wheel_index = 0; // cycle through wheel offsets
    
    mpz_init(center);
    mpz_init(candidate);
    
    // Convert prediction to integer center
    mpfr_get_z(center, prediction, MPFR_RNDN);
    
    // Use one wheel offset at a time (cycle through them)
    unsigned long wheel_offset = wheel->offsets[wheel_index % wheel->count];
    wheel_index++;
    
    // Adjust center to be congruent to wheel offset
    unsigned long remainder = mpz_fdiv_ui(center, wheel->modulus);
    if (remainder != wheel_offset) {
        long adjust = (long)wheel_offset - (long)remainder;
        if (adjust < 0) {
            adjust += wheel->modulus;
        }
        mpz_add_ui(center, center, adjust);
    }
    
    // Search in window around the adjusted center with given step
    for (unsigned long offset = 0; offset <= window && count < max_primes; offset += step) {
        // Forward direction
        if (offset == 0 || count < max_primes) {
            mpz_set(candidate, center);
            if (offset > 0) mpz_add_ui(candidate, candidate, offset * wheel->modulus);
            
            if (mpz_cmp_ui(candidate, 3) > 0 && miller_rabin_test(candidate, mr_rounds) >= 1) {
                if (found_primes) {
                    mpz_set(found_primes[count], candidate);
                }
                count++;
            }
        }
        
        // Backward direction (if offset > 0)
        if (offset > 0 && count < max_primes) {
            mpz_set(candidate, center);
            mpz_sub_ui(candidate, candidate, offset * wheel->modulus);
            
            if (mpz_cmp_ui(candidate, 3) > 0 && miller_rabin_test(candidate, mr_rounds) >= 1) {
                if (found_primes) {
                    mpz_set(found_primes[count], candidate);
                }
                count++;
            }
        }
    }
    
    mpz_clear(center);
    mpz_clear(candidate);
    
    return count;
}

static int auto_tune_scan(const mpfr_t prediction, wave_config_t *config, wave_result_t *result) {
    clock_t start = clock();
    wheel_t *wheel = get_wheel(config->wheel_mod);
    
    if (!wheel) {
        return -1;
    }
    
    unsigned long window = config->window;
    unsigned long step = config->step;
    unsigned int iteration = 0;
    int found_target = 0;
    
    mpz_t *candidates = malloc(sizeof(mpz_t) * 10); // up to 10 candidates
    for (int i = 0; i < 10; i++) {
        mpz_init(candidates[i]);
    }
    
    if (config->verbose) {
        printf("\nStarting auto-tune scan (target count: %u):\n", config->target_count);
    }
    
    // Self-tuning loop
    while (iteration < config->max_iters && !found_target) {
        unsigned int count = scan_prime_count(prediction, window, step, wheel, 
                                            config->mr_rounds, candidates, 10);
        
        if (config->verbose) {
            printf("Iter %u: window=%lu, step=%lu, R=%.3f, count=%u\n", 
                   iteration + 1, window, step, (double)window/step, count);
        }
        
        if (count == config->target_count) {
            // Found target - lock in
            found_target = 1;
            result->prime_count = count;
            if (count == 1) {
                mpz_set(result->prime_found, candidates[0]);
            }
            break;
        } else if (count == 0) {
            // No primes found - increase R (expand window first)
            if (window < 10000) {
                window = window * 3 / 2; // grow window by 50%
            } else {
                step = (step > 1) ? step - 1 : 1; // reduce step if large window
            }
        } else if (count > config->target_count) {
            // Too many primes - decrease R (shrink window or increase step)
            if (window > step * 2) {
                window = window * 2 / 3; // shrink window by 33%
            } else {
                step++; // increase step
            }
        }
        
        iteration++;
    }
    
    // Record final state
    result->window = window;
    result->step = step;
    result->ratio = (double)window / step;
    result->iterations = iteration;
    result->locked = found_target;
    result->mr_calls = g_total_mr_calls;
    
    snprintf(result->wheel_residue, sizeof(result->wheel_residue), "mod_%lu", wheel->modulus);
    
    for (int i = 0; i < 10; i++) {
        mpz_clear(candidates[i]);
    }
    free(candidates);
    
    result->elapsed_ms = ((double)(clock() - start) / CLOCKS_PER_SEC) * 1000.0;
    
    if (config->verbose) {
        if (found_target) {
            printf("✅ LOCKED at R* = %.6f after %u iterations\n", result->ratio, iteration);
        } else {
            printf("❌ Failed to lock after %lu iterations\n", config->max_iters);
        }
    }
    
    return found_target ? 0 : -1;
}

static int manual_scan(const mpfr_t prediction, wave_config_t *config, wave_result_t *result) {
    clock_t start = clock();
    wheel_t *wheel = get_wheel(config->wheel_mod);
    
    if (!wheel) {
        return -1;
    }
    
    mpz_t *candidates = malloc(sizeof(mpz_t) * 10);
    for (int i = 0; i < 10; i++) {
        mpz_init(candidates[i]);
    }
    
    // Single scan with fixed parameters
    unsigned int count = scan_prime_count(prediction, config->window, config->step, 
                                        wheel, config->mr_rounds, candidates, 10);
    
    // Record results
    result->window = config->window;
    result->step = config->step;
    result->ratio = (double)config->window / config->step;
    result->prime_count = count;
    result->iterations = 0;
    result->locked = (count == config->target_count);
    result->mr_calls = g_total_mr_calls;
    
    if (count >= 1) {
        mpz_set(result->prime_found, candidates[0]);
    }
    
    snprintf(result->wheel_residue, sizeof(result->wheel_residue), "mod_%lu", wheel->modulus);
    
    for (int i = 0; i < 10; i++) {
        mpz_clear(candidates[i]);
    }
    free(candidates);
    
    result->elapsed_ms = ((double)(clock() - start) / CLOCKS_PER_SEC) * 1000.0;
    
    if (config->verbose) {
        printf("Manual scan: found %u primes with R=%.6f\n", count, result->ratio);
    }
    
    return 0;
}

static void output_json_result(const wave_result_t *result, FILE *fp) {
    fprintf(fp, "{\n");
    fprintf(fp, "  \"k\": \"%s\",\n", mpz_get_str(NULL, 10, result->k_value));
    fprintf(fp, "  \"window\": %lu,\n", result->window);
    fprintf(fp, "  \"step\": %lu,\n", result->step);
    fprintf(fp, "  \"R\": %.6f,\n", result->ratio);
    fprintf(fp, "  \"prime_count\": %u,\n", result->prime_count);
    fprintf(fp, "  \"iterations\": %u,\n", result->iterations);
    fprintf(fp, "  \"mr_calls\": %lu,\n", result->mr_calls);
    fprintf(fp, "  \"elapsed_ms\": %.3f,\n", result->elapsed_ms);
    fprintf(fp, "  \"locked\": %s,\n", result->locked ? "true" : "false");
    fprintf(fp, "  \"wheel_residue\": \"%s\",\n", result->wheel_residue);
    if (result->prime_count == 1) {
        fprintf(fp, "  \"prime_found\": \"%s\"\n", mpz_get_str(NULL, 10, result->prime_found));
    } else {
        fprintf(fp, "  \"prime_found\": null\n");
    }
    fprintf(fp, "}\n");
}

static void output_human_result(const wave_result_t *result, const wave_config_t *config) {
    (void)config; // currently unused
    printf("\nWave-Knob Scanning Results:\n");
    printf("k = %s\n", mpz_get_str(NULL, 10, result->k_value));
    printf("Final parameters: window=%lu, step=%lu, R=%.6f\n", 
           result->window, result->step, result->ratio);
    printf("Prime count: %u\n", result->prime_count);
    printf("Tuning iterations: %u\n", result->iterations);
    printf("Miller-Rabin calls: %lu\n", result->mr_calls);
    printf("Elapsed time: %.3f ms\n", result->elapsed_ms);
    printf("Status: %s\n", result->locked ? "LOCKED" : "FAILED");
    
    if (result->prime_count == 1) {
        printf("Prime found: %s\n", mpz_get_str(NULL, 10, result->prime_found));
    }
}
