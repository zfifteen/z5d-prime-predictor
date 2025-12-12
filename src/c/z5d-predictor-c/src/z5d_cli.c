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
    printf("  -p <precision>  MPFR precision in bits (default: %d)\n", Z5D_DEFAULT_PRECISION);
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
    int precision = Z5D_DEFAULT_PRECISION;
    int verbose = 0;
    uint64_t n = 0;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            precision = atoi(argv[++i]);
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
    
    /* Set precision globally if user overrode */
    if (precision != Z5D_DEFAULT_PRECISION) {
        mpfr_set_default_prec(precision);
    }

    // Print configuration if verbose
    if (verbose) {
        printf("Configuration:\n");
        printf("  n           = %llu\n", (unsigned long long)n);
        printf("  precision   = %d bits (~%d decimal places)\n", precision, (int)(precision * 0.30103));
        printf("\n");
    }
    
    // Predict nth prime
    printf("Predicting the %llu-th prime...\n", (unsigned long long)n);
    mpz_t prime;
    mpz_init(prime);
    int ret = z5d_predict_nth_prime_mpz(prime, n);

    printf("\nResults:\n");
    gmp_printf("  Predicted prime: %Zd\n", prime);
    if (verbose) {
        printf("  Note: derived via calibrated Z5D predictor + discrete refinement\n");
    }

    mpz_clear(prime);
    z5d_cleanup();
    return ret;
}
