/**
 * Z5D nth-Prime Predictor - Command Line Interface
 * ================================================
 * 
 * CLI tool for predicting nth prime using Z5D predictor.
 * 
 * @file z5d_cli.c
 * @version 1.0
 */

#include "../include/z5d_predictor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <mpfr.h>

static void print_usage(const char* prog_name) {
    printf("Z5D nth-Prime Predictor v%s\n", z5d_get_version());
    printf("Usage: %s [options] <n>\n", prog_name);
    printf("\nOptions:\n");
    printf("  -k <K>          Number of terms in R(x) series (default: %d)\n", Z5D_DEFAULT_K);
    printf("  -p <precision>  MPFR precision in bits (default: %d)\n", Z5D_DEFAULT_PRECISION);
    printf("  -i <max_iter>   Maximum Newton iterations (default: 10)\n");
    printf("  -v              Verbose output\n");
    printf("  -h              Show this help\n");
    printf("\nArguments:\n");
    printf("  <n>             Index of prime to predict (positive integer)\n");
    printf("\nExamples:\n");
    printf("  %s 1000000\n", prog_name);
    printf("  %s -k 10 -p 300 1000000000\n", prog_name);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }
    
    // Parse command line options
    int K = Z5D_DEFAULT_K;
    int precision = Z5D_DEFAULT_PRECISION;
    int max_iter = 10;
    int verbose = 0;
    uint64_t n = 0;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-k") == 0 && i + 1 < argc) {
            K = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            precision = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
            max_iter = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = 1;
        } else if (argv[i][0] != '-') {
            n = strtoull(argv[i], NULL, 10);
        }
    }
    
    if (n == 0) {
        fprintf(stderr, "Error: Invalid or missing value for n\n");
        print_usage(argv[0]);
        return 1;
    }
    
    // Initialize library
    z5d_init();
    
    // Configure predictor
    z5d_config_t config;
    z5d_config_init(&config);
    config.precision = precision;
    config.K = K;
    config.max_iterations = max_iter;
    
    // Initialize result
    z5d_result_t result;
    z5d_result_init(&result, precision);
    
    // Print configuration if verbose
    if (verbose) {
        printf("Configuration:\n");
        printf("  n           = %llu\n", (unsigned long long)n);
        printf("  K           = %d\n", K);
        printf("  precision   = %d bits (~%d decimal places)\n", precision, (int)(precision * 0.30103));
        printf("  max_iter    = %d\n", max_iter);
        printf("\n");
    }
    
    // Predict nth prime
    printf("Predicting the %llu-th prime...\n", (unsigned long long)n);
    int ret = z5d_predict_nth_prime_ex(&result, n, &config);
    
    // Print results
    printf("\nResults:\n");
    printf("  Predicted prime: ");
    mpfr_out_str(stdout, 10, 0, result.predicted_prime, MPFR_RNDN);
    printf("\n");
    
    if (verbose) {
        printf("  Converged:       %s\n", result.converged ? "Yes" : "No");
        printf("  Iterations:      %d\n", result.iterations);
        printf("  Estimated error: ");
        mpfr_out_str(stdout, 10, 10, result.error, MPFR_RNDN);
        printf("\n");
    }
    
    printf("  Time elapsed:    %.3f ms\n", result.elapsed_ms);
    
    if (ret != 0 && !result.converged) {
        printf("\nWarning: Did not converge to tolerance in %d iterations.\n", max_iter);
        printf("         Result may be approximate. Try increasing -i or -p.\n");
    }
    
    // Cleanup
    z5d_result_clear(&result);
    z5d_config_clear(&config);
    z5d_cleanup();
    
    return ret;
}
