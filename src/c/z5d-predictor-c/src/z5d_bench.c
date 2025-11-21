/**
 * Z5D nth-Prime Predictor - Benchmark Tool
 * ========================================
 * 
 * Benchmarking tool for Z5D predictor performance testing.
 * 
 * @file z5d_bench.c
 * @version 1.0
 */

#include "../include/z5d_predictor.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpfr.h>

/* Known prime values for validation */
static const struct {
    uint64_t n;
    const char* prime_str;
} known_primes[] = {
    {10, "29"},
    {100, "541"},
    {1000, "7919"},
    {10000, "104729"},
    {100000, "1299709"},
    {1000000, "15485863"},
    {10000000, "179424673"},
    {100000000, "2038074743"},
    {1000000000, "22801763489"},
    {0, NULL}  // Sentinel
};

static void run_benchmark(uint64_t n, const char* expected) {
    z5d_config_t config;
    z5d_result_t result;
    
    z5d_config_init(&config);
    z5d_result_init(&result, Z5D_DEFAULT_PRECISION);
    
    printf("\n--- n = %llu ---\n", (unsigned long long)n);
    
    z5d_predict_nth_prime_ex(&result, n, &config);
    
    printf("Predicted: ");
    mpfr_out_str(stdout, 10, 0, result.predicted_prime, MPFR_RNDN);
    printf("\n");
    
    if (expected) {
        printf("Expected:  %s\n", expected);
        
        // Calculate error
        mpfr_t expected_mpfr, error, abs_error, rel_error;
        mpfr_init2(expected_mpfr, Z5D_DEFAULT_PRECISION);
        mpfr_init2(error, Z5D_DEFAULT_PRECISION);
        mpfr_init2(abs_error, Z5D_DEFAULT_PRECISION);
        mpfr_init2(rel_error, Z5D_DEFAULT_PRECISION);
        
        mpfr_set_str(expected_mpfr, expected, 10, MPFR_RNDN);
        mpfr_sub(error, result.predicted_prime, expected_mpfr, MPFR_RNDN);
        mpfr_abs(abs_error, error, MPFR_RNDN);
        
        // Relative error in ppm
        mpfr_div(rel_error, error, expected_mpfr, MPFR_RNDN);
        mpfr_mul_ui(rel_error, rel_error, 1000000, MPFR_RNDN);
        
        printf("Abs Error: ");
        mpfr_out_str(stdout, 10, 0, abs_error, MPFR_RNDN);
        printf("\n");
        
        printf("Rel Error: ");
        mpfr_out_str(stdout, 10, 6, rel_error, MPFR_RNDN);
        printf(" ppm\n");
        
        mpfr_clear(expected_mpfr);
        mpfr_clear(error);
        mpfr_clear(abs_error);
        mpfr_clear(rel_error);
    }
    
    printf("Converged: %s\n", result.converged ? "Yes" : "No");
    printf("Iterations: %d\n", result.iterations);
    printf("Time: %.3f ms\n", result.elapsed_ms);
    
    z5d_result_clear(&result);
    z5d_config_clear(&config);
}

int main(int argc __attribute__((unused)), char** argv __attribute__((unused))) {
    printf("Z5D nth-Prime Predictor Benchmark\n");
    printf("==================================\n");
    printf("Version: %s\n", z5d_get_version());
    
    z5d_init();
    
    // Run benchmarks for known values
    for (int i = 0; known_primes[i].n != 0; i++) {
        run_benchmark(known_primes[i].n, known_primes[i].prime_str);
    }
    
    // Summary
    printf("\n=================================\n");
    printf("Benchmark Complete\n");
    
    z5d_cleanup();
    return 0;
}
