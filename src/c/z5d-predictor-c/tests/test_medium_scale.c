/**
 * Z5D nth-Prime Predictor - Medium Scale Test
 * ===========================================
 * 
 * Tests predictor at medium scales (10^10 - 10^12).
 * 
 * @file test_medium_scale.c
 * @version 1.0
 */

#include "../include/z5d_predictor.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpfr.h>

typedef struct {
    uint64_t n;
    const char* expected_prime;
    const char* label;
} test_case_t;

static const test_case_t test_cases[] = {
    {10000000000ULL, "252097800623", "10^10"},
    {100000000000ULL, "2760727302517", "10^11"},
    {1000000000000ULL, "29996224275833", "10^12"},
    {0, NULL, NULL}  // Sentinel
};

static int run_test(const test_case_t* test) {
    z5d_config_t config;
    z5d_result_t result;
    
    z5d_config_init(&config);
    config.precision = 300;  // Higher precision for larger numbers
    z5d_result_init(&result, config.precision);
    
    printf("Testing n = %s (%llu)...\n", test->label, (unsigned long long)test->n);
    
    int ret = z5d_predict_nth_prime_ex(&result, test->n, &config);
    
    printf("  Predicted:  ");
    mpfr_out_str(stdout, 10, 0, result.predicted_prime, MPFR_RNDN);
    printf("\n");
    printf("  Expected:   %s\n", test->expected_prime);
    
    // Calculate relative error
    mpfr_t expected_mpfr, error, rel_error_ppm;
    mpfr_init2(expected_mpfr, config.precision);
    mpfr_init2(error, config.precision);
    mpfr_init2(rel_error_ppm, config.precision);
    
    mpfr_set_str(expected_mpfr, test->expected_prime, 10, MPFR_RNDN);
    mpfr_sub(error, result.predicted_prime, expected_mpfr, MPFR_RNDN);
    mpfr_div(rel_error_ppm, error, expected_mpfr, MPFR_RNDN);
    mpfr_mul_ui(rel_error_ppm, rel_error_ppm, 1000000, MPFR_RNDN);
    
    printf("  Rel Error:  ");
    mpfr_out_str(stdout, 10, 6, rel_error_ppm, MPFR_RNDN);
    printf(" ppm\n");
    
    double rel_err_ppm = mpfr_get_d(rel_error_ppm, MPFR_RNDN);
    
    printf("  Converged:  %s\n", result.converged ? "Yes" : "No");
    printf("  Iterations: %d\n", result.iterations);
    printf("  Time:       %.3f ms\n", result.elapsed_ms);
    
    // Test passes if relative error < 1000 ppm (0.1%)
    int passed = (fabs(rel_err_ppm) < 1000.0);
    printf("  Status:     %s\n\n", passed ? "PASS" : "FAIL");
    
    mpfr_clear(expected_mpfr);
    mpfr_clear(error);
    mpfr_clear(rel_error_ppm);
    z5d_result_clear(&result);
    z5d_config_clear(&config);
    
    return passed;
}

int main(void) {
    printf("Z5D nth-Prime Predictor - Medium Scale Test\n");
    printf("============================================\n\n");
    
    z5d_init();
    
    int total = 0;
    int passed = 0;
    
    for (int i = 0; test_cases[i].n != 0; i++) {
        total++;
        if (run_test(&test_cases[i])) {
            passed++;
        }
    }
    
    printf("============================================\n");
    printf("Test Results: %d/%d passed\n", passed, total);
    
    z5d_cleanup();
    
    return (passed == total) ? 0 : 1;
}
